import json
import string

import pytest
import yaml

from typing import Any


def test_cassette_recording(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_{}(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200

        @pytest.mark.vcr
        class TestSomething:
            def test_with_network(self, httpbin):
                assert requests.get(httpbin.url + "/get").status_code == 200

        @pytest.mark.vcr
        def test_without_network():
            pass
    """.format(string.ascii_letters)
    )

    # If recording is enabled
    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=3)

    # Then tests that use network will create cassettes
    cassette_path = testdir.tmpdir.join("cassettes/test_cassette_recording/test_{}.yaml".format(string.ascii_letters))
    assert cassette_path.size()
    cassette_path = testdir.tmpdir.join("cassettes/test_cassette_recording/TestSomething.test_with_network.yaml")
    assert cassette_path.size()

    # And tests that do not use network will not create any cassettes
    cassette_path = testdir.tmpdir.join("cassettes/test_cassette_recording/test_without_network.yaml")
    assert not cassette_path.exists()


def test_disable_recording(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )

    # If recording is disabled
    result = testdir.runpytest("--disable-recording")
    result.assert_outcomes(passed=1)

    # Then there should be no cassettes
    cassette_path = testdir.tmpdir.join("cassettes/test_disable_recording/test_.yaml")
    assert not cassette_path.exists()


def test_record_mode_in_mark(testdir):
    # See GH-47
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr(record_mode="once")
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_record_mode_in_mark/test_record_mode.yaml")
    assert cassette_path.size()


def test_override_default_cassette(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.default_cassette("foo.yaml")
        @pytest.mark.vcr(record_mode="once")
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_override_default_cassette/foo.yaml")
    assert cassette_path.size()


def test_record_mode_in_config(testdir):
    # See GH-47
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": "once"}

        @pytest.mark.vcr
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_record_mode_in_config/test_record_mode.yaml")
    assert cassette_path.size()


def test_cassette_recording_rewrite(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200

        @pytest.mark.vcr
        class TestSomething:
            def test_with_network(self, httpbin):
                assert requests.get(httpbin.url + "/uuid").status_code == 200
    """
    )

    # If recording is enabled
    result = testdir.runpytest("--record-mode=rewrite")
    result.assert_outcomes(passed=2)

    # Then tests that use network will create cassettes
    test_function_cassette_path = testdir.tmpdir.join(
        "cassettes/test_cassette_recording_rewrite/test_with_network.yaml"
    )
    test_function_size = test_function_cassette_path.size()
    assert test_function_size
    # Cassette should contain uuid as response
    cassette: Any
    with open(str(test_function_cassette_path), encoding="utf8") as cassette:
        cassette = yaml.load(cassette, Loader=yaml.BaseLoader)
        test_function_cassette_uuid = cassette["interactions"][0]["response"]["body"]["string"]

    test_class_cassette_path = testdir.tmpdir.join(
        "cassettes/test_cassette_recording_rewrite/TestSomething.test_with_network.yaml"
    )
    test_class_size = test_class_cassette_path.size()
    assert test_class_size
    with open(str(test_class_cassette_path), encoding="utf8") as cassette:
        cassette = yaml.load(cassette, Loader=yaml.BaseLoader)
        test_class_cassette_uuid = cassette["interactions"][0]["response"]["body"]["string"]

    # Second run will pass as well
    result = testdir.runpytest("--record-mode=rewrite")
    result.assert_outcomes(passed=2)
    # And cassette size has not changed
    assert test_function_cassette_path.size() == test_function_size
    # But uuid is different
    with open(str(test_function_cassette_path), encoding="utf8") as cassette:
        cassette = yaml.load(cassette, Loader=yaml.BaseLoader)
        assert test_function_cassette_uuid != cassette["interactions"][0]["response"]["body"]["string"]

    assert test_class_cassette_path.size() == test_class_size
    with open(str(test_class_cassette_path), encoding="utf8") as cassette:
        cassette = yaml.load(cassette, Loader=yaml.BaseLoader)
        assert test_class_cassette_uuid != cassette["interactions"][0]["response"]["body"]["string"]


def test_custom_cassette_name(testdir):
    # When a custom cassette name is passed to pytest.mark.vcr
    cassette = testdir.tmpdir.join("cassettes/test_custom_cassette_name/test_with_network.yaml")
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr("{}")
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """.format(cassette)
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # Then tests with custom cassette names specified will create appropriate cassettes
    # And writing will happen to the default cassette
    assert cassette.size()


def test_custom_cassette_name_rewrite(testdir):
    # When a custom cassette name is passed to pytest.mark.vcr
    cassette = testdir.tmpdir.join("cassettes/test_custom_cassette_name_rewrite/test_with_network.yaml")
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr("{}")
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200
    """.format(cassette)
    )

    result = testdir.runpytest("--record-mode=rewrite")
    result.assert_outcomes(passed=1)

    # Then tests with custom cassette names specified will create appropriate cassettes
    # And writing will happen to the default cassette
    cassette_size = cassette.size()
    assert cassette_size
    file: Any
    with open(str(cassette), encoding="utf8") as file:
        file = yaml.load(file, Loader=yaml.BaseLoader)
        uuid = file["interactions"][0]["response"]["body"]["string"]

    # Second run will pass as well
    result = testdir.runpytest("--record-mode=rewrite")
    result.assert_outcomes(passed=1)
    # And cassette size is the same
    assert cassette.size() == cassette_size
    # But uuid in response is different
    with open(str(cassette), encoding="utf8") as file:
        file = yaml.load(file, Loader=yaml.BaseLoader)
        assert uuid != file["interactions"][0]["response"]["body"]["string"]


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
    """.format(ip_response_cassette)
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

@pytest.mark.parametrize("value", ("/A", "../foo", "/foo/../bar", "foo/../../bar"))
def test_network(httpbin, value):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    """
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=4)

    # Then those characters should be replaced
    assert not testdir.tmpdir.join("cassettes/test_forbidden_characters/test_network[").exists()
    cassette_path = testdir.tmpdir.join("cassettes/test_forbidden_characters/test_network[-A].yaml")
    assert cassette_path.size()
    cassettes_dir = testdir.tmpdir.join("cassettes/test_forbidden_characters")
    assert len(cassettes_dir.listdir()) == 4


def test_json_serializer(testdir):
    custom_cassette_path = testdir.tmpdir.join("custom.json")
    # When the `serializer` config option is set to "json"
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr()]

@pytest.mark.vcr(serializer="json")
def test_network(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.vcr("{}", serializer="json")
def test_custom_name(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    """.format(custom_cassette_path)
    )

    result = testdir.runpytest("--record-mode=all", "-s")
    result.assert_outcomes(passed=2)

    # Then the created cassette should have "json" extension
    cassette_path = testdir.tmpdir.join("cassettes/test_json_serializer/test_network.json")
    assert cassette_path.size()

    # and contain a valid JSON
    data = cassette_path.read_text("utf8")
    json.loads(data)

    # and a custom cassette is not created
    assert not custom_cassette_path.exists()


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

    # And only the default cassette is writable
    assert testdir.tmpdir.join("cassettes/test_multiple_marks/test_with_network.yaml").size()
    assert not second_cassette.exists()
    assert not first_cassette.exists()


def test_kwargs_overriding(testdir):
    # Example from the docs
    testdir.makepyfile(
        """
import pytest

pytestmark = [pytest.mark.vcr(ignore_localhost=True)]

@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": ["authorization"]}

def make_request(**kwargs):
    return type("Request", (), kwargs)

@pytest.mark.vcr(filter_headers=[])
def test_one(vcr):
    # Headers should be untouched
    request = make_request(headers={"authorization": "something"})
    assert vcr._before_record_request(request).headers == {"authorization": "something"}

    # Check `ignore_localhost`
    request = make_request(host="127.0.0.1")
    assert vcr._before_record_request(request) is None


@pytest.mark.vcr(filter_query_parameters=["api_key"])
def test_two(vcr):
    request = make_request(
        uri="https://www.example.com?api_key=secret",
        headers={"authorization": "something"},
        query=(("api_key", "secret"),)
    )
    processed = vcr._before_record_request(request)
    assert processed.headers == {}
    assert processed.uri == "https://www.example.com"

    # Check `ignore_localhost`
    request = make_request(
        uri="http://127.0.0.1",
        host="127.0.0.1",
        headers={"authorization": "something"},
        query=(("api_key", "secret"),)
    )
    assert vcr._before_record_request(request) is None
    """
    )

    # Different kwargs should be merged properly
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)
