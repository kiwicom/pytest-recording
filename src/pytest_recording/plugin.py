import os
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

import pytest
from _pytest.config import Config, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest
from _pytest.mark.structures import Mark

if TYPE_CHECKING:
    from vcr.cassette import Cassette

from . import hooks, network
from .utils import merge_kwargs
from .validation import validate_block_network_mark

RECORD_MODES = ("once", "new_episodes", "none", "all", "rewrite")


def pytest_configure(config: Config) -> None:
    if config.pluginmanager.has_plugin("vcr"):
        raise RuntimeError(
            "`pytest-recording` is incompatible with `pytest-vcr`. "
            "Please, uninstall `pytest-vcr` in order to use `pytest-recording`."
        )
    config.addinivalue_line("markers", "vcr: Mark the test as using VCR.py.")
    config.addinivalue_line("markers", "block_network: Block network access except for VCR recording.")
    config.addinivalue_line("markers", "default_cassette: Override the default cassette name.")
    config.addinivalue_line(
        "markers",
        "allowed_hosts: List of regexes to match hosts to where connection must be allowed.",
    )
    network.install_pycurl_wrapper()


def pytest_unconfigure() -> None:
    network.uninstall_pycurl_wrapper()


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("recording")
    group.addoption(
        "--record-mode",
        action="store",
        default=None,
        choices=RECORD_MODES,
        help='VCR.py record mode. Default to "none".',
    )
    group.addoption(
        "--block-network",
        action="store_true",
        default=False,
        help="Block network access except for VCR recording.",
    )
    group.addoption(
        "--allowed-hosts",
        action="store",
        default=None,
        help="List of regexes, separated by comma, to match hosts to where connection must be allowed.",
    )
    group.addoption(
        "--disable-recording",
        action="store_true",
        default=False,
        help="Disable VCR.py integration.",
    )


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    pluginmanager.add_hookspecs(hooks)


@pytest.fixture(scope="session")  # type: ignore
def record_mode(request: SubRequest) -> str:
    """When recording is disabled the VCR recording mode should be "none" to prevent network access."""
    return request.config.getoption("--record-mode") or "none"


@pytest.fixture(scope="session")  # type: ignore
def disable_recording(request: SubRequest) -> bool:
    """Disable VCR.py integration."""
    return request.config.getoption("--disable-recording")


@pytest.fixture  # type: ignore
def vcr_config() -> Dict:
    """A shareable configuration for VCR.use_cassette call."""
    return {}


@pytest.fixture  # type: ignore
def allowed_hosts(request: SubRequest) -> List[str]:
    """List of regexes to match hosts to where connection must be allowed."""
    block_network = request.node.get_closest_marker(name="block_network")
    config = request.getfixturevalue("vcr_config")
    # Take `--allowed-hosts` with the most priority:
    #  - `block_network` mark
    #  - CLI option
    #  - `vcr_config` fixture
    allowed_hosts = (
        getattr(block_network, "kwargs", {}).get("allowed_hosts")
        or request.config.getoption("--allowed-hosts")
        or config.get("allowed_hosts")
    )
    if isinstance(allowed_hosts, str):
        allowed_hosts = allowed_hosts.split(",")
    return allowed_hosts


@pytest.fixture  # type: ignore
def vcr_markers(request: SubRequest) -> List[Mark]:
    """All markers applied to the certain test together with cassette names associated with each marker."""
    return list(request.node.iter_markers(name="vcr"))


@pytest.fixture(autouse=True)  # type: ignore
def block_network(request: SubRequest, record_mode: str, vcr_markers: List[Mark]) -> Iterator[None]:
    """Block network access in tests except for "none" VCR recording mode."""
    block_network = request.node.get_closest_marker(name="block_network")
    if block_network is not None:
        validate_block_network_mark(block_network)
    if vcr_markers:
        # Take `record_mode` with the most priority:
        #  - Explicit CLI option
        #  - The `vcr_config` fixture
        #  - The `vcr` mark
        config = request.getfixturevalue("vcr_config")
        merged_config = merge_kwargs(config, vcr_markers)
        # If `--record-mode` was not explicitly passed in CLI, then take one from the merged config
        if request.config.getoption("--record-mode") is None:
            record_mode = merged_config.get("record_mode", "none")
    # If network blocking is enabled there is one exception - if VCR is in recording mode (any mode except "none")
    if (block_network or request.config.getoption("--block-network")) and (not vcr_markers or record_mode == "none"):
        allowed_hosts = request.getfixturevalue("allowed_hosts")
        with network.blocking_context(allowed_hosts=allowed_hosts):
            yield
    else:
        yield


@pytest.fixture(autouse=True)  # type: ignore
def vcr(
    request: SubRequest,
    vcr_markers: List[Mark],
    vcr_cassette_dir: str,
    record_mode: str,
    disable_recording: bool,
    pytestconfig: Config,
) -> Iterator[Optional["Cassette"]]:
    """Install a cassette if a test is marked with `pytest.mark.vcr`."""
    if disable_recording:
        yield None
    elif vcr_markers:
        from ._vcr import use_cassette

        config = request.getfixturevalue("vcr_config")
        default_cassette = request.getfixturevalue("default_cassette_name")
        with use_cassette(
            default_cassette,
            vcr_cassette_dir,
            record_mode,
            vcr_markers,
            config,
            pytestconfig,
        ) as cassette:
            yield cassette
    else:
        yield None


@pytest.fixture(scope="module")  # type: ignore
def vcr_cassette_dir(request: SubRequest) -> str:
    """Each test module has its own cassettes directory to avoid name collisions.

    For example each test module could have test function with the same names:
      - test_users.py:test_create
      - test_profiles.py:test_create
    """
    module = request.node.fspath  # current test file
    return os.path.join(module.dirname, "cassettes", module.purebasename)


@pytest.fixture  # type: ignore
def default_cassette_name(request: SubRequest) -> str:
    marker = request.node.get_closest_marker("default_cassette")
    if marker is not None:
        assert marker.args, (
            "You should pass the cassette name as an argument to the `pytest.mark.default_cassette` marker"
        )
        return marker.args[0]
    return get_default_cassette_name(request.cls, request.node.name)


def get_default_cassette_name(test_class: Any, test_name: str) -> str:
    if test_class:
        cassette_name = "{}.{}".format(test_class.__name__, test_name)
    else:
        cassette_name = test_name
    # The cassette name should not contain characters that are forbidden in a file name
    # In this case there is a possibility to have a collision if there will be names with different
    # forbidden chars but the same resulting string.
    # Possible solution is to add a hash to the resulting name, but this probability is too low to have such fix.
    for ch in r"<>?%*:|\"'/\\":
        cassette_name = cassette_name.replace(ch, "-")
    return cassette_name
