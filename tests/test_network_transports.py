import socket
import sys

import pytest

from pytest_recording import network


@pytest.mark.parametrize("transports", [("socket",), ("pycurl",), ("socket", "pycurl")])
@pytest.mark.parametrize("raise_inside", [False, True])
def test_selected_transports(httpbin, transports, raise_inside):
    pycurl = pytest.importorskip("pycurl")
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_socketpair = socket.socketpair
    network.install_pycurl_wrapper()
    try:
        try:
            with network.blocking_context(transports=transports):
                assert network._disable_pycurl == ("pycurl" in transports)
                if "socket" not in transports:
                    assert socket.socket.connect is original_connect
                    assert socket.socket.connect_ex is original_connect_ex
                    assert socket.socketpair is original_socketpair
                with socket.socket() as client:
                    if "socket" in transports:
                        with pytest.raises(RuntimeError, match="Network is disabled"):
                            client.connect(("127.0.0.1", httpbin.port))
                    else:
                        client.connect(("127.0.0.1", httpbin.port))
                curl = sys.modules["pycurl"].Curl()
                try:
                    curl.setopt(pycurl.URL, httpbin.url + "/get")
                    curl.setopt(pycurl.PROXY, "")
                    curl.setopt(pycurl.WRITEFUNCTION, lambda data: len(data))
                    if "pycurl" in transports:
                        with pytest.raises(RuntimeError, match="Network is disabled"):
                            curl.perform()
                    else:
                        curl.perform()
                        assert curl.getinfo(pycurl.RESPONSE_CODE) == 200
                finally:
                    curl.close()
                if raise_inside:
                    raise LookupError("synthetic failure")
        except LookupError:
            assert raise_inside
        assert socket.socket.connect is original_connect
        assert socket.socket.connect_ex is original_connect_ex
        assert socket.socketpair is original_socketpair
        assert not network._disable_pycurl
    finally:
        network.uninstall_pycurl_wrapper()


def test_socket_selection_preserves_pycurl_state():
    network.block_pycurl(["kept"], allow_private_ips=True)
    try:
        with network.blocking_context(transports=("socket",)):
            assert network._disable_pycurl
            assert network._allowed_hosts == ["kept"]
            assert network._allow_private_ips
        assert network._disable_pycurl
        assert network._allowed_hosts == ["kept"]
        assert network._allow_private_ips
    finally:
        network.unblock_pycurl()


def test_pycurl_selection_preserves_socket_wrappers(monkeypatch):
    def custom_connect(*args):
        raise AssertionError("unselected wrapper called")

    monkeypatch.setattr(socket.socket, "connect", custom_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", custom_connect)
    monkeypatch.setattr(socket, "socketpair", custom_connect)
    with network.blocking_context(transports=("pycurl",)):
        assert socket.socket.connect is custom_connect
    assert socket.socket.connect is custom_connect
    assert socket.socket.connect_ex is custom_connect
    assert socket.socketpair is custom_connect


@pytest.mark.parametrize("operation", [network.block, network.unblock, network.blocking_context])
@pytest.mark.parametrize("transports", [(), ("unknown",), ("socket", "unknown"), "socket"])
def test_invalid_selection_leaves_state_untouched(operation, transports):
    original_connect = socket.socket.connect
    original_disable = network._disable_pycurl
    with pytest.raises(ValueError):
        if operation is network.blocking_context:
            with operation(transports=transports):
                pytest.fail("invalid selection entered the context")
        else:
            operation(transports=transports)
    assert socket.socket.connect is original_connect
    assert network._disable_pycurl == original_disable


def test_selection_can_be_a_generator():
    original_connect = socket.socket.connect
    with network.blocking_context(transports=(name for name in ["socket", "socket"])):
        with socket.socket() as client, pytest.raises(RuntimeError, match="Network is disabled"):
            client.connect(("127.0.0.1", 1))
    assert socket.socket.connect is original_connect


def test_pycurl_selection_without_pycurl(monkeypatch):
    monkeypatch.setattr(network, "pycurl", None)
    original_connect = socket.socket.connect
    with network.blocking_context(transports=("pycurl",)):
        assert socket.socket.connect is original_connect
    assert socket.socket.connect is original_connect


def test_selected_transport_setup_error_is_cleaned_up(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("setup failed")

    monkeypatch.setattr(network, "block_pycurl", fail)
    with pytest.raises(RuntimeError, match="setup failed"), network.blocking_context():
        pytest.fail("setup should not complete")
    assert socket.socket.connect is network._original_connect
