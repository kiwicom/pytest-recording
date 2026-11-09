import ipaddress
import re
import socket
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, List, Optional, Tuple, Union
from urllib.parse import urlparse

try:
    import pycurl

    @dataclass
    class Curl:
        """Proxy to real pycurl.Curl.

        If `perform` is called then it will raise an error if network is disabled via `disable`
        """

        handle: pycurl.Curl = field(default_factory=pycurl.Curl)
        url = None  # type: Optional[str]

        def __getattribute__(self, item: str) -> Any:
            handle = object.__getattribute__(self, "handle")
            if _disable_pycurl and item == "perform":
                host = urlparse(self.url).hostname
                if not host or is_host_allowed(host, _allowed_hosts, _allow_private_ips):
                    return getattr(handle, item)
                raise network_disabled_error(host, _allowed_hosts, _allow_private_ips)
            if item == "handle":
                return handle
            if item == "setopt":
                return object.__getattribute__(self, "setopt")
            return getattr(handle, item)

        def __setattr__(self, key: str, value: Any) -> None:
            if key == "handle":
                object.__setattr__(self, key, value)
            else:
                setattr(self.handle, key, value)

        def setopt(self, option: int, value: Any) -> None:
            if option == pycurl.URL:
                self.url = value
            self.handle.setopt(option, value)

except ImportError:
    pycurl = None  # type: ignore
    Curl = None  # type: ignore

# `socket.socket` is not patched, because it could be needed for live servers (e.g. pytest-httpbin)
# But methods that could connect to remote are patched to prevent network access
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_socketpair = socket.socketpair

# `socket.socketpair()` is emulated on Windows with a real loopback `connect()`, and asyncio builds
# every event loop's self-pipe that way. Without an exemption the guard blocks the event loop
# itself instead of the network, so the whole asyncio suite dies at setup.
#
# The exemption is set only while a `socketpair()` call is running, and it is thread-local: a
# plain module-level flag would also unblock every other thread's connections for the duration of
# that call, and a test suite running thread pools would silently lose the guard.
_socketpair_state = threading.local()


def _inside_socketpair() -> bool:
    return getattr(_socketpair_state, "active", False)


TRANSPORTS = ("socket", "pycurl")


# Global switch for pycurl disabling
_disable_pycurl = False
_allowed_hosts = None  # type: ignore
_allow_private_ips = False


@dataclass(unsafe_hash=True)
class PyCurlWrapper:
    """Imitate pycurl module."""

    def __getattribute__(self, item: str) -> Any:
        if item == "Curl":
            return Curl
        return getattr(pycurl, item)


def check_pycurl_installed(func: Callable) -> Callable:
    """No-op if pycurl is not installed."""

    def inner(*args: Any, **kwargs: Any) -> Any:
        if pycurl is None:
            return  # type: ignore
        return func(*args, **kwargs)

    return inner


@check_pycurl_installed
def install_pycurl_wrapper() -> None:
    sys.modules["pycurl"] = PyCurlWrapper()  # type: ignore


@check_pycurl_installed
def uninstall_pycurl_wrapper() -> None:
    sys.modules["pycurl"] = pycurl


def block_pycurl(allowed_hosts: Optional[List[str]] = None, allow_private_ips: bool = False) -> None:
    global _disable_pycurl
    global _allowed_hosts
    global _allow_private_ips
    _disable_pycurl = True
    _allowed_hosts = allowed_hosts
    _allow_private_ips = allow_private_ips


def unblock_pycurl() -> None:
    global _disable_pycurl
    global _allowed_hosts
    global _allow_private_ips
    _disable_pycurl = False
    _allowed_hosts = None
    _allow_private_ips = False


def make_socketpair_guard(original_func: Callable) -> Callable:
    def socketpair_guard(*args: Any, **kwargs: Any) -> Tuple[Any, Any]:
        previous = getattr(_socketpair_state, "active", False)
        _socketpair_state.active = True
        try:
            return original_func(*args, **kwargs)
        finally:
            _socketpair_state.active = previous

    return socketpair_guard


def block_socket(allowed_hosts: Optional[List[str]] = None, allow_private_ips: bool = False) -> None:
    socket.socket.connect = make_network_guard(_original_connect, allowed_hosts, allow_private_ips)  # type: ignore
    socket.socket.connect_ex = make_network_guard(_original_connect_ex, allowed_hosts, allow_private_ips)  # type: ignore
    socket.socketpair = make_socketpair_guard(_original_socketpair)  # type: ignore


def unblock_socket() -> None:
    socket.socket.connect = _original_connect  # type: ignore
    socket.socket.connect_ex = _original_connect_ex  # type: ignore
    socket.socketpair = _original_socketpair  # type: ignore


def make_network_guard(
    original_func: Callable, allowed_hosts: Optional[List[str]] = None, allow_private_ips: bool = False
) -> Callable:
    def network_guard(self: Any, address: Union[Tuple, str, bytes], *args: Any, **kwargs: Any) -> Any:
        if _inside_socketpair():
            return original_func(self, address, *args, **kwargs)
        host = ""  # type: Union[str, bytes, bytearray]
        if self.family in (socket.AF_INET, socket.AF_INET6):
            host = address[0]  # type: ignore
        elif self.family == socket.AF_UNIX:
            host = address  # type: ignore
        if is_host_allowed(host, allowed_hosts, allow_private_ips):
            return original_func(self, address, *args, **kwargs)
        raise network_disabled_error(host, allowed_hosts, allow_private_ips)

    return network_guard


def _select_transports(transports: Iterable[str]) -> Tuple[str, ...]:
    if isinstance(transports, str):
        raise ValueError("transports must be a non-empty iterable of transport names")
    selected = tuple(transports)
    if not selected:
        raise ValueError("transports must not be empty")
    for transport in selected:
        if transport not in TRANSPORTS:
            raise ValueError(f"Unknown transport: {transport!r}. Available transports: {TRANSPORTS!r}")
    return tuple(dict.fromkeys(selected))


def block(
    allowed_hosts: Optional[List[str]] = None,
    allow_private_ips: bool = False,
    transports: Iterable[str] = TRANSPORTS,
) -> None:
    """Block the selected transports, defaulting to socket and pycurl."""
    selected = _select_transports(transports)
    if "socket" in selected:
        block_socket(allowed_hosts=allowed_hosts, allow_private_ips=allow_private_ips)
    # NOTE: Applying socket blocking makes curl hangs - it should be carefully patched
    if "pycurl" in selected:
        block_pycurl(allowed_hosts=allowed_hosts, allow_private_ips=allow_private_ips)


def unblock(transports: Iterable[str] = TRANSPORTS) -> None:
    """Unblock the same transports passed to :func:`block`."""
    selected = _select_transports(transports)
    if "pycurl" in selected:
        unblock_pycurl()
    if "socket" in selected:
        unblock_socket()


@contextmanager
def blocking_context(
    allowed_hosts: Optional[List[str]] = None,
    allow_private_ips: bool = False,
    transports: Iterable[str] = TRANSPORTS,
) -> Iterator[None]:
    """Block connections via the selected transports (socket and pycurl by default).

    Note:
    ----
        Only connections to remotes are blocked in `socket`.
        Local servers are not touched since it could interfere with live servers needed for tests (e.g. pytest-httpbin)

    """
    global _disable_pycurl, _allowed_hosts, _allow_private_ips
    selected = _select_transports(transports)
    if "socket" in selected:
        socket_state = (socket.socket.connect, socket.socket.connect_ex, socket.socketpair)
    if "pycurl" in selected:
        pycurl_state = (_disable_pycurl, _allowed_hosts, _allow_private_ips)
    try:
        block(allowed_hosts=allowed_hosts, allow_private_ips=allow_private_ips, transports=selected)
        yield
    finally:
        # Restore only selected state, including when setup raises.
        if "pycurl" in selected:
            _disable_pycurl, _allowed_hosts, _allow_private_ips = pycurl_state
        if "socket" in selected:
            socket.socket.connect, socket.socket.connect_ex, socket.socketpair = socket_state  # type: ignore


def to_string(value: Union[str, bytes, bytearray]) -> str:
    if isinstance(value, (bytes, bytearray)):
        return value.decode()
    return value


def network_disabled_error(
    host: Union[str, bytes, bytearray], allowed_hosts: Optional[List[str]], allow_private_ips: bool = False
) -> RuntimeError:
    message = f"Network is disabled for host {host!r}"
    allowed = [repr(allowed_host) for allowed_host in allowed_hosts or ()]
    if allow_private_ips:
        allowed.append("private IPs")
    if allowed:
        message += f" (allowed hosts: {', '.join(allowed)})"
    return RuntimeError(message)


def is_host_allowed(
    host: Union[str, bytes, bytearray], allowed_hosts: Optional[List[str]], allow_private_ips: bool
) -> bool:
    return is_host_in_allowed_hosts(host, allowed_hosts) or (allow_private_ips and is_private_ip(host))


def is_private_ip(host: Union[str, bytes, bytearray]) -> bool:
    try:
        return ipaddress.ip_address(to_string(host)).is_private
    except ValueError:
        # Hostnames (pycurl) and AF_UNIX paths
        return False


def is_host_in_allowed_hosts(host: Union[str, bytes, bytearray], allowed_hosts: Optional[List[str]]) -> bool:
    """Match provided host to a list of host regexps."""
    if allowed_hosts is not None:
        combined = "(" + ")|(".join(allowed_hosts) + ")"
        return bool(re.match(combined, to_string(host)))
    return False
