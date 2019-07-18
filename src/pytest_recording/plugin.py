# -*- coding: utf-8 -*-
import os

import pytest

from ._vcr import make_cassette


def pytest_configure(config):
    config.addinivalue_line("markers", "vcr: Mark the test as using VCR.py.")


def pytest_addoption(parser):
    group = parser.getgroup("recording")
    group.addoption(
        "--record-mode",
        action="store",
        default="none",
        choices=["once", "new_episodes", "none", "all"],
        help='VCR.py record mode. Default to "none".',
    )


@pytest.fixture(scope="session")
def record_mode(request):
    """When recording is disabled the VCR recording mode should be "none" to prevent network access."""
    return request.config.getoption("--record-mode")


@pytest.fixture
def vcr_config():
    """A shareable configuration for VCR.use_cassette call."""
    return {}


@pytest.fixture
def vcr_markers(request):
    """All markers applied to the certain test together with cassette names associated with each marker."""
    markers = []
    for idx, marker in enumerate(request.node.iter_markers(name="vcr")):
        if idx == 0:
            if marker not in request.node.own_markers:
                markers.append(((request.getfixturevalue("default_cassette_name"),), None))
        if marker.args:
            # All arguments given to the `pytest.mark.vcr` are cassettes names
            markers.append((marker.args, marker))
        else:
            # Only the closest marker could have a name generated from the given test
            if idx == 0 and marker in request.node.own_markers:
                name = (request.getfixturevalue("default_cassette_name"),)
            else:
                # Otherwise markers don't have any associated cassettes names
                name = None
            markers.append((name, marker))
    return markers


@pytest.fixture(autouse=True)
def _vcr(request, vcr_markers, vcr_cassette_dir, record_mode):
    """Install a cassette if a test is marked with `pytest.mark.vcr`."""
    if vcr_markers:
        config = request.getfixturevalue("vcr_config")
        with make_cassette(vcr_cassette_dir, record_mode, vcr_markers, config):
            yield
    else:
        yield


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """Each test module has its own cassettes directory to avoid name collisions.

    For example each test module could have test function with the same names:
      - test_users.py:test_create
      - test_profiles.py:test_create
    """
    module = request.node.fspath  # current test file
    return os.path.join(module.dirname, "cassettes", module.purebasename)


@pytest.fixture
def default_cassette_name(request):
    test_class = request.cls
    if test_class:
        cassette_name = "{}.{}".format(test_class.__name__, request.node.name)
    else:
        cassette_name = request.node.name
    # The cassette name should not contain characters that are forbidden in a file name
    # In this case there is a possibility to have a collision if there will be names with different
    # forbidden chars but the same resulting string.
    # Possible solution is to add a hash to the resulting name, but this probability is too low to have such fix.
    for ch in r"<>?%*:|\"'/\\":
        cassette_name = cassette_name.replace(ch, "-")
    return cassette_name
