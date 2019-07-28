from contextlib import contextmanager
import socket
import sys

import attr

try:
    import pycurl

    @attr.s(slots=True)
    class Curl(object):
        """Proxy to real pycurl.Curl.

        If `perform` is called then it will raise an error if network is disabled via `disable`
        """

        handle = attr.ib(factory=pycurl.Curl)

        def __getattribute__(self, item):
            if _disable_pycurl and item == "perform":
                raise RuntimeError("Network is disabled")
            handle = object.__getattribute__(self, "handle")
            return getattr(handle, item)


except ImportError:
    pycurl = None
    Curl = None

# `socket.socket` is not patched, because it could be needed for live servers (e.g. pytest-httpbin)
# But methods that could connect to remote are patched to prevent network access
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex

# Global switch for pycurl disabling
_disable_pycurl = False


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


def block_pycurl():
    global _disable_pycurl  # pylint: disable=global-statement
    _disable_pycurl = True


def unblock_pycurl():
    global _disable_pycurl  # pylint: disable=global-statement
    _disable_pycurl = False


def block_socket():
    socket.socket.connect = network_guard
    socket.socket.connect_ex = network_guard


def unblock_socket():
    socket.socket.connect = _original_connect
    socket.socket.connect_ex = _original_connect_ex


def network_guard(*args, **kwargs):
    raise RuntimeError("Network is disabled")


def block():
    block_socket()
    # NOTE: Applying socket blocking makes curl hangs - it should be carefully patched
    block_pycurl()


def unblock():
    unblock_pycurl()
    unblock_socket()


@contextmanager
def blocking_context():
    """Block connections via socket and pycurl.

    NOTE:
        Only connections to remotes are blocked in `socket`.
        Local servers are not touched since it could interfere with live servers needed for tests (e.g. pytest-httpbin)
    """
    block()
    try:
        yield
    finally:
        # an error could happen somewhere else when this ctx manager is on `yield`
        unblock()
