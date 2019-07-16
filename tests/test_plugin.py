# -*- coding: utf-8 -*-
import pytest


@pytest.mark.parametrize("args, expected", ((("--record-mode=all",), "all"), ((), "none")))
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
