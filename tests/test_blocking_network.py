import pytest
from packaging import version

try:
    import pycurl
except ImportError as exc:
    if "No module named" not in str(exc):
        # Case with different SSL backends should be loud and visible
        # Could happen with development when environment is recreated (e.g. locally)
        raise
    pycurl = None  # type: ignore[assignment]


def assert_network_blocking(testdir, dirname):
    result = testdir.runpytest("--record-mode=all")
    # Then all network requests in tests with block_network mark except for marked with pytest.mark.vcr should fail
    result.assert_outcomes(passed=3)

    # And a cassette is recorded for the case where pytest.mark.vcr is applied
    cassette_path = testdir.tmpdir.join("cassettes/{}/test_recording.yaml".format(dirname))
    assert cassette_path.exists()


def test_blocked_network_recording_cli_arg(testdir):
    # When record is enabled via a CLI arg
    testdir.makepyfile(
        """
import pytest
import requests

def test_no_blocking(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
@pytest.mark.vcr
def test_recording(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
def test_error(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        assert requests.get(httpbin.url + "/ip").status_code == 200
    """
    )
    assert_network_blocking(testdir, "test_blocked_network_recording_cli_arg")


def test_blocked_network_recording_vcr_config(testdir):
    # When record is enabled via the `vcr_config` fixture
    testdir.makepyfile(
        """
import pytest
import requests

@pytest.fixture(autouse=True)
def vcr_config():
    return {"record_mode": "once"}


def test_no_blocking(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
@pytest.mark.vcr
def test_recording(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
def test_error(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        assert requests.get(httpbin.url + "/ip").status_code == 200
    """
    )
    assert_network_blocking(testdir, "test_blocked_network_recording_vcr_config")


def test_blocked_network_recording_vcr_mark(testdir):
    # When record is enabled via the `vcr` mark
    testdir.makepyfile(
        """
import pytest
import requests

def test_no_blocking(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
@pytest.mark.vcr(record_mode="once")
def test_recording(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.block_network
def test_error(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        assert requests.get(httpbin.url + "/ip").status_code == 200
    """
    )
    assert_network_blocking(testdir, "test_blocked_network_recording_vcr_mark")


def test_socket_connect(testdir):
    # When socket.socket is aliased in some module
    testdir.makepyfile(
        another="""
from socket import socket, AF_INET, SOCK_STREAM

def call(port):
    s = socket(AF_INET, SOCK_STREAM)
    try:
        return s.connect(("127.0.0.1", port))
    finally:
        s.close()
"""
    )
    testdir.makepyfile(
        """
from another import call
import pytest

@pytest.mark.block_network
def test_no_blocking(httpbin):
    _, port = httpbin.url.rsplit(":", 1)
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        call(int(port))
    """
    )

    result = testdir.runpytest()
    # Then socket.socket.connect should fail
    result.assert_outcomes(passed=1)


def test_unix_socket(testdir):
    testdir.makepyfile(
        """
from socket import socket, AF_UNIX, SOCK_STREAM
import pytest

def call(socket_name):
    s = socket(AF_UNIX, SOCK_STREAM)
    try:
        return s.connect(socket_name)
    finally:
        s.close()

@pytest.mark.block_network(allowed_hosts=["./allowed_socket"])
def test_allowed():
    # Error from actual socket call, that means it was not blocked
    with pytest.raises(IOError):
        call("./allowed_socket")

@pytest.mark.block_network(allowed_hosts=["./allowed_socket"])
def test_blocked():
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        call("./blocked_socket")
    """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_other_socket(testdir):
    # When not AF_UNIX, AF_INET or AF_INET6 socket is used
    testdir.makepyfile(
        """
from socket import socket, AF_NETLINK, SOCK_RAW
import pytest

def call():
    s = socket(AF_NETLINK, SOCK_RAW)
    try:
        return s.connect((0, 0))
    finally:
        s.close()

@pytest.mark.block_network(allowed_hosts=["./allowed_socket", "127.0.0.1", "0"])
def test_blocked():
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        call()
    """
    )
    # Then socket.socket.connect call is blocked, even if resource name is in the allowed list
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_block_network(testdir):
    # When record is disabled
    testdir.makepyfile(
        """
import socket
import pytest
import requests
import vcr.errors

@pytest.mark.block_network
@pytest.mark.vcr
def test_with_vcr_mark(httpbin):
    with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException, match=r"overwrite existing cassette"):
        requests.get(httpbin.url + "/ip")
    assert socket.socket.connect.__name__ == "network_guard"
    assert socket.socket.connect_ex.__name__ == "network_guard"

@pytest.mark.block_network
def test_no_vcr_mark(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        requests.get(httpbin.url + "/ip")


@pytest.mark.block_network(allowed_hosts=["127.0.0.2"])
def test_no_vcr_mark_bytes():
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((b"127.0.0.1", 80))

@pytest.mark.block_network(allowed_hosts=["127.0.0.2"])
def test_no_vcr_mark_bytearray():
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((bytearray(b"127.0.0.1"), 80))
    """
    )

    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)


@pytest.mark.parametrize(
    "marker, cmd_options, vcr_cfg",
    (
        pytest.param(
            '@pytest.mark.block_network(allowed_hosts=["127.0.0.*", "127.0.1.1"])',
            "",
            "",
            id="block_marker",
        ),
        pytest.param(
            "",
            ("--block-network", "--allowed-hosts=127.0.0.*,127.0.1.1"),
            "",
            id="block_cmd",
        ),
        pytest.param(
            "@pytest.mark.block_network()",
            "",
            "@pytest.fixture(autouse=True)\ndef vcr_config():\n    return {'allowed_hosts': '127.0.0.*,127.0.1.1'}",
            id="vcr_cfg",
        ),
    ),
)
def test_block_network_with_allowed_hosts(testdir, marker, cmd_options, vcr_cfg):
    testdir.makepyfile(
        """
import socket
import pytest
import requests

{vcr_cfg}

{marker}
def test_allowed(httpbin):
    response = requests.get(httpbin.url + "/ip")
    assert response.status_code == 200
    assert socket.socket.connect.__name__ == "network_guard"
    assert socket.socket.connect_ex.__name__ == "network_guard"

{marker}
def test_blocked():
    with pytest.raises(RuntimeError, match="^Network is disabled$"):
        requests.get("http://example.com")
    assert socket.socket.connect.__name__ == "network_guard"
    assert socket.socket.connect_ex.__name__ == "network_guard"
    """.format(
            marker=marker,
            vcr_cfg=vcr_cfg,
        )
    )

    result = testdir.runpytest(*cmd_options)
    result.assert_outcomes(passed=2)


def test_block_network_via_cmd(testdir):
    # When `--block-network` option is passed to CMD
    testdir.makepyfile(
        """
import socket
import pytest
import requests
import vcr.errors

@pytest.mark.vcr
def test_with_vcr_mark(httpbin):
    with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException, match=r"overwrite existing cassette"):
        requests.get(httpbin.url + "/ip")
    assert socket.socket.connect.__name__ == "network_guard"
    assert socket.socket.connect_ex.__name__ == "network_guard"


def test_no_vcr_mark(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        requests.get(httpbin.url + "/ip")
    """
    )

    result = testdir.runpytest("--block-network")
    # Then all network interactions in all tests should be blocked
    result.assert_outcomes(passed=2)


def test_block_network_via_cmd_with_recording(testdir):
    # When `--block-network` option is passed to CMD and VCR recording is enabled
    testdir.makepyfile(
        """
import socket
import pytest
import requests
import vcr.errors

@pytest.mark.vcr
def test_recording(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

def test_no_vcr_mark(httpbin):
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        requests.get(httpbin.url + "/ip")
    """
    )

    result = testdir.runpytest("--block-network", "--record-mode=all")
    # Then only tests with `pytest.mark.vcr` should record cassettes, other tests with network should raise errors
    result.assert_outcomes(passed=2)

    # And a cassette is recorded for the case where pytest.mark.vcr is applied
    cassette_path = testdir.tmpdir.join("cassettes/test_block_network_via_cmd_with_recording/test_recording.yaml")
    assert cassette_path.exists()


@pytest.mark.skipif(pycurl is None, reason="Requires pycurl installed.")
def test_pycurl(testdir):
    # When pycurl is used for network access
    testdir.makepyfile(
        r"""
import json
import sys
import pytest
import pycurl
from io import BytesIO


@pytest.mark.block_network
def test_error(httpbin):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, httpbin.url + "/ip")
    c.setopt(c.WRITEDATA, buffer)
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        c.perform()
    c.close()

def test_work(httpbin):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, httpbin.url + "/ip")
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    assert json.loads(buffer.getvalue()) == {"origin":"127.0.0.1"}
    """
    )

    result = testdir.runpytest()
    # It should be blocked as well
    result.assert_outcomes(passed=2)


@pytest.mark.skipif(pycurl is None, reason="Requires pycurl installed.")
def test_pycurl_with_allowed_hosts(testdir):
    # When pycurl is used for network access
    testdir.makepyfile(
        r"""
import json
import sys
import pytest
import pycurl
from io import BytesIO


@pytest.mark.block_network(allowed_hosts=["127.0.0.*", "127.0.1.1"])
def test_allowed(httpbin):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, httpbin.url + "/ip")
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    assert json.loads(buffer.getvalue()) == {"origin":"127.0.0.1"}

@pytest.mark.block_network(allowed_hosts=["127.0.0.*", "127.0.1.1"])
def test_blocked(httpbin):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, "http://example.com")
    c.setopt(c.WRITEDATA, buffer)
    with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
        c.perform()
    c.close()
    """
    )

    result = testdir.runpytest("-s")
    # It should be blocked as well
    result.assert_outcomes(passed=2)


@pytest.mark.skipif(pycurl is None, reason="Requires pycurl installed.")
def test_pycurl_setattr():
    # When pycurl is used for network access
    # And an attribute is set on an instance
    curl = pycurl.Curl()
    curl.attr = 42  # type: ignore[attr-defined]
    # Then it should be proxied to the original Curl instance itself
    assert curl.handle.attr == 42  # type: ignore[attr-defined]


@pytest.mark.skipif(pycurl is None, reason="Requires pycurl installed.")
def test_pycurl_url_error():
    # When pycurl is used for network access
    # And a wrapper may fail on URL manipulation due to missing URL
    curl = pycurl.Curl()
    # Then original pycurl error must be raised
    with pytest.raises(pycurl.error, match="No URL set"):
        curl.perform()


@pytest.mark.skipif(pycurl is None, reason="Requires pycurl installed.")
def test_sys_modules(testdir):
    # When pycurl is patched
    testdir.makepyfile(
        """
import sys
import pytest

@pytest.mark.block_network
def test_sys_modules():
    set(sys.modules.values())
    """
    )

    result = testdir.runpytest()
    # Patched module should be hashable - use case for auto-reloaders and similar (e.g. in Django)
    # The patch should behave as close to real modules as possible
    result.assert_outcomes(passed=1)


def test_critical_error(testdir):
    # When a critical error happened and the `network.disable` ctx manager is interrupted on `yield`
    testdir.makepyfile(
        """
import socket
from pytest_recording.network import blocking_context

def test_critical_error():
    try:
        with blocking_context():
            assert socket.socket.connect.__name__ == "network_guard"
            assert socket.socket.connect_ex.__name__ == "network_guard"
            raise ValueError
    except ValueError:
        pass
    assert socket.socket.connect.__name__ == "connect"
    assert socket.socket.connect_ex.__name__ == "connect_ex"
    """
    )
    result = testdir.runpytest()
    # Then socket and pycurl should be unpatched anyway
    result.assert_outcomes(passed=1)
    # NOTE. In reality, it is not likely to happen - e.g. if pytest will partially crash and will not call the teardown
    # part of the generator, but this try/finally implementation could also guard against errors on manual


IS_PYTEST_ABOVE_54 = version.parse(pytest.__version__) >= version.parse("5.4.0")


@pytest.mark.parametrize("args", ("foo=42", "42"))
def test_invalid_input_arguments(testdir, args):
    # When the `block_network` mark receives an unknown argument
    testdir.makepyfile(
        """
import pytest
import requests

@pytest.mark.block_network({})
def test_request():
    requests.get("https://google.com")
    """.format(args)
    )
    result = testdir.runpytest()
    # Then there should be an error
    if IS_PYTEST_ABOVE_54:
        result.assert_outcomes(errors=1)
    else:
        result.assert_outcomes(error=1)
    expected = "Invalid arguments to `block_network`. It accepts only the following keyword arguments: `allowed_hosts`."
    assert expected in result.stdout.str()
