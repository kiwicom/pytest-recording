import json
import string
from typing import Any

import pytest
import yaml


def test_cassette_recording(testdir):
    testdir.makepyfile(
        f"""
        import pytest
        import requests

        @pytest.mark.vcr
        def test_{string.ascii_letters}(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200

        @pytest.mark.vcr
        class TestSomething:
            def test_with_network(self, httpbin):
                assert requests.get(httpbin.url + "/get").status_code == 200

        @pytest.mark.vcr
        def test_without_network():
            pass
    """
    )

    # If recording is enabled
    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=3)

    # Then tests that use network will create cassettes
    cassette_path = testdir.tmpdir.join(f"cassettes/test_cassette_recording/test_{string.ascii_letters}.yaml")
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


def assert_cassette_is_rewritten(testdir, cassette_path):
    """Run the test again and assert that ``rewrite`` replaces the cassette instead of extending it."""
    # If recording is enabled
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)

    # Then the test creates a cassette
    cassette_size = cassette_path.size()
    assert cassette_size
    with open(str(cassette_path), encoding="utf8") as cassette:
        first_uuid = yaml.load(cassette, Loader=yaml.BaseLoader)["interactions"][0]["response"]["body"]["string"]

    # Rewriting again replaces the cassette instead of replaying or extending it
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    assert cassette_path.size() == cassette_size
    with open(str(cassette_path), encoding="utf8") as cassette:
        second_uuid = yaml.load(cassette, Loader=yaml.BaseLoader)["interactions"][0]["response"]["body"]["string"]
    assert first_uuid != second_uuid


def test_rewrite_record_mode_in_config(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": "rewrite"}

        @pytest.mark.vcr
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200
    """
    )
    cassette_path = testdir.tmpdir.join("cassettes/test_rewrite_record_mode_in_config/test_record_mode.yaml")
    assert_cassette_is_rewritten(testdir, cassette_path)


def test_rewrite_record_mode_in_mark(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr(record_mode="rewrite")
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200
    """
    )
    cassette_path = testdir.tmpdir.join("cassettes/test_rewrite_record_mode_in_mark/test_record_mode.yaml")
    assert_cassette_is_rewritten(testdir, cassette_path)


def test_recording_configure_hook_does_not_override_record_mode(testdir):
    """`record_mode` set via the `vcr_config` fixture wins over the `pytest_recording_configure` hook."""
    testdir.makeconftest(
        """
def pytest_recording_configure(config, vcr):
    vcr.record_mode = "none"
        """
    )
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": "all"}

        @pytest.mark.vcr
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200
    """
    )
    cassette_path = testdir.tmpdir.join(
        "cassettes/test_recording_configure_hook_does_not_override_record_mode/test_record_mode.yaml"
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
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
        f"""
        import pytest
        import requests

        @pytest.mark.vcr(r"{cassette}")
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    # Then tests with custom cassette names specified will create appropriate cassettes
    # And writing will happen to the default cassette
    assert cassette.size()


def test_rewrite_warns_when_cassette_cannot_be_removed(testdir):
    # A directory in place of the cassette makes `os.remove` fail with an error other than "not found"
    testdir.mkdir("cassettes").mkdir("test_rewrite_warns_when_cassette_cannot_be_removed").mkdir("test_rewrite.yaml")
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.vcr
        def test_rewrite():
            pass
    """
    )

    result = testdir.runpytest("--record-mode=rewrite")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*UserWarning: Failed to remove cassette*test_rewrite.yaml*"])


def test_rewrite_does_not_warn_when_cassette_is_missing(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.vcr
        def test_rewrite():
            pass
    """
    )

    result = testdir.runpytest("--record-mode=rewrite", "-W", "error::UserWarning")
    result.assert_outcomes(passed=1)


def test_custom_cassette_name_rewrite(testdir):
    # When a custom cassette name is passed to pytest.mark.vcr
    cassette = testdir.tmpdir.join("cassettes/test_custom_cassette_name_rewrite/test_with_network.yaml")
    testdir.makepyfile(
        f"""
        import pytest
        import requests

        @pytest.mark.vcr(r"{cassette}")
        def test_with_network(httpbin):
            assert requests.get(httpbin.url + "/uuid").status_code == 200
    """
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
        f"""
import pytest
import requests

pytestmark = [pytest.mark.vcr(r"{ip_response_cassette}")]

def test_network(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    assert requests.get(httpbin.url + "/get").status_code == 200
    """
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
        f"""
import pytest
import requests

pytestmark = [pytest.mark.vcr()]

@pytest.mark.vcr(serializer="json")
def test_network(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200

@pytest.mark.vcr(r"{custom_cassette_path}", serializer="json")
def test_custom_name(httpbin):
    assert requests.get(httpbin.url + "/ip").status_code == 200
    """
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

@pytest.mark.vcr(r"{}")
@pytest.mark.vcr(r"{}")
def test_with_network(httpbin):
    assert requests.get(httpbin.url + "/get").status_code == 200
""",
        """
import pytest
import requests

pytestmark = pytest.mark.vcr(r"{}")

@pytest.mark.vcr(r"{}")
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


def test_long_cassette_name(testdir):
    testdir.makepyfile(
        """
import pytest
import requests

@pytest.mark.vcr
@pytest.mark.parametrize(
    "data",
    [
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' * 5,
    ],
    ids=str,
)
def test_with_parametrize(httpbin,data):
    assert requests.get(httpbin.url + "/get").status_code == 200
    """
    )

    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=1)

    cassette_path = testdir.tmpdir.join(
        "cassettes/test_long_cassette_name/test_with_parametrize[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg...e6273968ceb1173c9b9ca1a67463cdd4.yaml"
    )
    assert cassette_path.size()


def test_vcr_fixture_is_none_without_flag(testdir):
    testdir.makepyfile(
        """
        def test_cassette(vcr):
            assert vcr is None
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_vcr_fixture_with_flag(testdir):
    testdir.makepyfile(
        """
        def test_cassette(vcr):
            assert vcr is not None
        """
    )
    result = testdir.runpytest("--vcr")
    result.assert_outcomes(passed=1)


def test_record_mode_without_vcr_flag(testdir):
    # `--record-mode` on its own still only affects tests marked with `vcr`.
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_marked(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200

        def test_unmarked(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )
    result = testdir.runpytest("--record-mode=all")
    result.assert_outcomes(passed=2)
    cassette_dir = "cassettes/test_record_mode_without_vcr_flag"
    assert testdir.tmpdir.join(f"{cassette_dir}/test_marked.yaml").size()
    assert not testdir.tmpdir.join(f"{cassette_dir}/test_unmarked.yaml").exists()


@pytest.mark.parametrize("mode", ("once", "rewrite"))
def test_vcr_flag_records(testdir, mode):
    testdir.makepyfile(
        """
        import requests

        def test_single(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200

        class TestGroup:
            def test_method(self, httpbin):
                assert requests.get(httpbin.url + "/ip").status_code == 200

        def test_offline():
            pass
        """
    )
    result = testdir.runpytest("--vcr", f"--record-mode={mode}")
    result.assert_outcomes(passed=3)
    cassette_dir = "cassettes/test_vcr_flag_records"
    assert testdir.tmpdir.join(f"{cassette_dir}/test_single.yaml").size()
    assert testdir.tmpdir.join(f"{cassette_dir}/TestGroup.test_method.yaml").size()
    assert not testdir.tmpdir.join(f"{cassette_dir}/test_offline.yaml").exists()


def test_vcr_flag_record_mode_none(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests
        import vcr

        def test_single(httpbin):
            with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
                requests.get(httpbin.url + "/ip")
        """
    )
    result = testdir.runpytest("--vcr", "--record-mode=none")
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_vcr_flag_record_mode_none/test_single.yaml")
    assert not cassette_path.exists()


def test_vcr_flag_replays_existing_cassette(testdir, create_file, get_cassette):
    create_file("cassettes/test_vcr_flag_replays_existing_cassette/test_replay.yaml", get_cassette)
    testdir.makepyfile(
        """
        import requests

        def test_replay():
            assert requests.get("http://httpbin.org/get").text == '{"get": true}'
        """
    )
    # Network stays blocked in the default `none` mode, so this only passes on replay.
    result = testdir.runpytest("--vcr", "--block-network")
    result.assert_outcomes(passed=1)


def test_vcr_flag_keeps_marker_cassettes(testdir, get_response_cassette):
    testdir.makepyfile(
        f"""
        import pytest
        import requests
        import vcr

        @pytest.mark.vcr(r"{get_response_cassette}")
        def test_marked():
            assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'

        def test_unmarked():
            with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
                requests.get("http://httpbin.org/get")
        """
    )
    result = testdir.runpytest("--vcr")
    result.assert_outcomes(passed=2)
    cassette_dir = "cassettes/test_vcr_flag_keeps_marker_cassettes"
    assert not testdir.tmpdir.join(f"{cassette_dir}/test_unmarked.yaml").exists()


def test_vcr_flag_honors_mark_record_mode(testdir):
    # A mark's `record_mode` still applies when the CLI flag is on and `--record-mode` is omitted.
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr(record_mode="once")
        def test_marked(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )
    result = testdir.runpytest("--vcr")
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_vcr_flag_honors_mark_record_mode/test_marked.yaml")
    assert cassette_path.size()


def test_vcr_flag_honors_config_record_mode_while_network_is_blocked(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": "once"}

        def test_single(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )
    result = testdir.runpytest("--vcr", "--block-network")
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join(
        "cassettes/test_vcr_flag_honors_config_record_mode_while_network_is_blocked/test_single.yaml"
    )
    assert cassette_path.size()


def test_vcr_flag_records_while_network_is_blocked(testdir):
    testdir.makepyfile(
        """
        import requests

        def test_single(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )
    result = testdir.runpytest("--vcr", "--block-network", "--record-mode=all")
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_vcr_flag_records_while_network_is_blocked/test_single.yaml")
    assert cassette_path.size()


def test_vcr_flag_honors_default_cassette_marker(testdir):
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.default_cassette("custom.yaml")
        def test_named(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )
    result = testdir.runpytest("--vcr", "--record-mode=once")
    result.assert_outcomes(passed=1)
    cassette_dir = "cassettes/test_vcr_flag_honors_default_cassette_marker"
    assert testdir.tmpdir.join(f"{cassette_dir}/custom.yaml").size()
    assert not testdir.tmpdir.join(f"{cassette_dir}/test_named.yaml").exists()
