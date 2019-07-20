# -*- coding: utf-8 -*-
import os
from itertools import chain

import pytest

from ._vcr import make_cassette

RECORD_MODES = ("once", "new_episodes", "none", "all")


def pytest_configure(config):
    config.addinivalue_line("markers", "vcr: Mark the test as using VCR.py.")


def pytest_addoption(parser):
    group = parser.getgroup("recording")
    group.addoption(
        "--record-mode",
        action="store",
        default="none",
        choices=RECORD_MODES,
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
    all_markers = request.node.iter_markers(name="vcr")
    return list(chain(_process_closest_mark(request, all_markers), ((marker.args, marker) for marker in all_markers)))


def _process_closest_mark(request, all_marks):
    """The closest mark to the test function is special."""
    try:
        closest_mark = next(all_marks)

        # When the closest mark is not on the test function itself
        # Then a cassette with default name should be added for recording
        if closest_mark not in request.node.own_markers:
            yield (request.getfixturevalue("default_cassette_name"),), None

        # When no custom cassette name specified
        # Then default name should be used
        if not closest_mark.args:
            names = (request.getfixturevalue("default_cassette_name"),)
        else:
            names = closest_mark.args
        yield names, closest_mark
    except StopIteration:
        # No pytest.mark.vcr at all
        pass


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
    return get_default_cassette_name(request.cls, request.node.name)


def get_default_cassette_name(test_class, test_name):
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
