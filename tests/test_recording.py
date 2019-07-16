import pytest


def test_cassette_recording(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200

        @pytest.mark.vcr
        def test_without_network():
            pass
    """
    )

    # If recording is enabled
    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=2)

    # Then tests that use network will create cassettes
    cassette_path = testdir.tmpdir.join("cassettes/test_cassette_recording/test_with_network.yaml")
    assert cassette_path.size()

    # And tests that do not use network will not create any cassettes
    cassette_path = testdir.tmpdir.join("cassettes/test_cassette_recording/test_without_network.yaml")
    assert not cassette_path.exists()


def test_custom_cassette_name(testdir):
    # When a custom cassette name is passed to pytest.mark.vcr
    cassette = testdir.tmpdir.join("custom.yaml")
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr("{}")
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200

    """.format(
            cassette
        )
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # Then tests with custom cassette names specified will create appropriate  cassettes
    assert cassette.size()


def test_default_cassette_recording(testdir, ip_response_cassette):
    # When a cassette is applied on a module level
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr("{}")]

def test_network(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    assert requests.get(httpbin.url + "/get").status_code == 200
    """.format(
            ip_response_cassette
        )
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # Then writing should happen only to the closest cassette
    cassette_path = testdir.tmpdir.join("cassettes/test_default_cassette_recording/test_network.yaml")
    assert cassette_path.size()


def test_forbidden_characters(testdir):
    # When a test name contains characters that will lead to a directory creation
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr()]

@pytest.mark.parametrize("value", ("/A",))
def test_network(httpbin, value):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    """
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # Then those characters should be replaced
    assert not testdir.tmpdir.join("cassettes/test_forbidden_characters/test_network[").exists()
    cassette_path = testdir.tmpdir.join("cassettes/test_forbidden_characters/test_network[-A].yaml")
    assert cassette_path.size()


@pytest.mark.parametrize(
    "code",
    (
        """
import pytest
import requests

@pytest.mark.vcr("{}")
@pytest.mark.vcr("{}")
def test_with_network(httpbin):
    assert requests.get(httpbin.url + "/get").status_code == 200
""",
        """
import pytest
import requests

pytestmark = pytest.mark.vcr("{}")

@pytest.mark.vcr("{}")
def test_with_network(httpbin):
    assert requests.get(httpbin.url + "/get").status_code == 200
""",
    ),
)
def test_multiple_marks(testdir, code):
    first_cassette = testdir.tmpdir.join("custom.yaml")
    second_cassette = testdir.tmpdir.join("custom2.yaml")
    testdir.makepyfile(code.format(first_cassette, second_cassette))

    # If recording is enabled
    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # And only the closest cassette is writable
    assert second_cassette.size()
    assert not first_cassette.exists()
