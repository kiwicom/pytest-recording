import pytest

from pytest_recording.utils import unique


@pytest.mark.parametrize("sequence, expected", (([], []), ([1, 1, 3, 5], [1, 3, 5])))
def test_unique(sequence, expected):
    assert list(unique(sequence)) == expected
