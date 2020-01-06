import re
import socket
import sys
from contextlib import contextmanager

import attr

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


try:
    import pycurl

    @attr.s(slots=True)
    class Curl(object):
        """Proxy to real pycurl.Curl.

        If `perform` is called then it will raise an error if network is disabled via `disable`
        """

        handle = attr.ib(factory=pycurl.Curl)
        url = None

        def __getattribute__(self, item):
            handle = object.__getattribute__(self, "handle")
            if _disable_pycurl and item == "perform":
                host = urlparse(self.url).hostname
                if not host or is_host_in_allowed_hosts(host, _allowed_hosts):
                    return getattr(handle, item)
                raise RuntimeError("Network is disabled")
            if item == "handle":
                return handle
            if item == "setopt":
                return object.__getattribute__(self, "setopt")
            return getattr(handle, item)

        def __setattr__(self, key, value):
            if key == "handle":
                object.__setattr__(self, key, value)
            else:
                setattr(self.handle, key, value)

        def setopt(self, option, value):
            if option == pycurl.URL:
                self.url = value
            self.handle.setopt(option, value)


except ImportError:
    pycurl = None
    Curl = None

# `socket.socket` is not patched, because it could be needed for live servers (e.g. pytest-httpbin)
# But methods that could connect to remote are patched to prevent network access
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex

# Global switch for pycurl disabling
_disable_pycurl = False
_allowed_hosts = None


@attr.s(slots=True, hash=True)
class PyCurlWrapper(object):
    """Imitate pycurl module."""

    def __getattribute__(self, item):
        if item == "Curl":
            return Curl
        return getattr(pycurl, item)


def check_pycurl_installed(func):
    """No-op if pycurl is not installed."""

    def inner(*args, **kwargs):  # pylint: disable=inconsistent-return-statements
        if pycurl is None:
            return
        return func(*args, **kwargs)

    return inner


@check_pycurl_installed
def install_pycurl_wrapper():
    sys.modules["pycurl"] = PyCurlWrapper()


@check_pycurl_installed
def uninstall_pycurl_wrapper():
    sys.modules["pycurl"] = pycurl


def block_pycurl(allowed_hosts=None):
    global _disable_pycurl  # pylint: disable=global-statement
    global _allowed_hosts  # pylint: disable=global-statement
    _disable_pycurl = True
    _allowed_hosts = allowed_hosts


def unblock_pycurl():
    global _disable_pycurl  # pylint: disable=global-statement
    global _allowed_hosts  # pylint: disable=global-statement
    _disable_pycurl = False
    _allowed_hosts = None


def block_socket(allowed_hosts=None):
    socket.socket.connect = make_network_guard(_original_connect, allowed_hosts=allowed_hosts)
    socket.socket.connect_ex = make_network_guard(_original_connect_ex, allowed_hosts=allowed_hosts)


def unblock_socket():
    socket.socket.connect = _original_connect
    socket.socket.connect_ex = _original_connect_ex


def make_network_guard(original_func, allowed_hosts=None):
    def network_guard(self, address, *args, **kwargs):
        host = ""
        if self.family in (socket.AF_INET, socket.AF_INET6):
            host = address[0]
        elif self.family == socket.AF_UNIX:
            host = address
        if is_host_in_allowed_hosts(host, allowed_hosts):
            return original_func(self, address, *args, **kwargs)
        raise RuntimeError("Network is disabled")

    return network_guard


def block(allowed_hosts=None):
    block_socket(allowed_hosts=allowed_hosts)
    # NOTE: Applying socket blocking makes curl hangs - it should be carefully patched
    block_pycurl(allowed_hosts=allowed_hosts)


def unblock():
    unblock_pycurl()
    unblock_socket()


@contextmanager
def blocking_context(allowed_hosts=None):
    """Block connections via socket and pycurl.

    Note:
        Only connections to remotes are blocked in `socket`.
        Local servers are not touched since it could interfere with live servers needed for tests (e.g. pytest-httpbin)

    """
    block(allowed_hosts=allowed_hosts)
    try:
        yield
    finally:
        # an error could happen somewhere else when this ctx manager is on `yield`
        unblock()


def is_host_in_allowed_hosts(host, allowed_hosts):
    """Match provided host to a list of host regexps."""
    if allowed_hosts is not None:
        combined = "(" + ")|(".join(allowed_hosts) + ")"
        return re.match(combined, host)
    return False
