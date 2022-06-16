# -*- coding: utf-8 -*-
import pytest
from pytest_recording.plugin import RECORD_MODES


@pytest.mark.parametrize(
    "args, expected", [(("--record-mode={}".format(mode),), mode) for mode in RECORD_MODES] + [((), "none")]
)
def test_record_mode(testdir, args, expected):
    testdir.makepyfile(
        """
        def test_mode(record_mode):
            assert record_mode == "{}"
    """.format(
            expected
        )
    )

    # Record mode depends on the passed CMD arguments
    result = testdir.runpytest(*args)
    result.assert_outcomes(passed=1)
    assert result.ret == 0


def test_help_message(testdir):
    result = testdir.runpytest("--help")
    result.stdout.fnmatch_lines(["recording:", "*--record-mode=*", "*VCR.py record mode.*"])


def test_pytest_vcr_incompatibility(testdir, mocker):
    try:
        mocker.patch("pluggy._manager.PluginManager.has_plugin", return_value=True)
    except (AttributeError, ImportError):
        # Python 3.5 & older `pluggy`
        mocker.patch("pluggy.manager.PluginManager.has_plugin", return_value=True)
    testdir.makepyfile(
        """
        def test_():
            pass
    """
    )

    # Record mode depends on the passed CMD arguments
    result = testdir.runpytest()
    assert (
        "INTERNALERROR> RuntimeError: `pytest-recording` is incompatible with `pytest-vcr`. "
        "Please, uninstall `pytest-vcr` in order to use `pytest-recording`." in result.errlines
    )
    assert result.ret == 3


def test_default_cassette_marker(testdir):
    # When the `default_cassette` marker is defined
    testdir.makepyfile(
        """
        import pytest

        CASSETTE_NAME = "foo.yaml"

        @pytest.mark.default_cassette(CASSETTE_NAME)
        def test_marker(default_cassette_name):
            assert default_cassette_name == CASSETTE_NAME
        """
    )
    # Then the default_cassette_name fixture should be overridden
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    assert result.ret == 0
