import pytest
import requests
import vcr

from pytest_recording._vcr import load_cassette

VCR_VERSION = tuple(map(int, vcr.__version__.split(".")))


@pytest.mark.vcr
def test_no_cassete_vcr_used():
    """If pytest.mark.vcr is applied and there is no cassette - an exception happens."""
    with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
        requests.get("http://localhost/get")


def test_combine_cassettes(testdir, get_response_cassette, ip_response_cassette):
    testdir.makepyfile(
        """
import pytest
import requests

@pytest.mark.vcr("{}")
@pytest.mark.vcr("{}")
def test_combined():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'

def test_no_vcr(httpbin):
    assert requests.get(httpbin.url + "/headers").status_code == 200
""".format(get_response_cassette, ip_response_cassette)
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_combine_cassettes_module_level(testdir, get_response_cassette, ip_response_cassette):
    # When there there is a module-level mark and a test-level mark
    testdir.makepyfile(
        """
import pytest
import requests
import vcr

pytestmark = pytest.mark.vcr("{}")

@pytest.mark.vcr("{}")
def test_combined():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'

def test_single_cassette():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
        requests.get("http://httpbin.org/ip")
        """.format(get_response_cassette, ip_response_cassette)
    )
    # Then their cassettes are combined
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_empty_module_mark(testdir, get_response_cassette):
    # When a module-level mark is empty
    testdir.makepyfile(
        """
import pytest
import requests
import vcr

pytestmark = pytest.mark.vcr()

@pytest.mark.vcr("{}")
def test_combined():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
""".format(get_response_cassette)
    )
    # Then it is noop for tests that already have pytest.mark.vcr applied
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_merged_kwargs(testdir, get_response_cassette):
    # When there are multiple pytest.mark.vcr with different kwargs
    testdir.makepyfile(
        """
import pytest
import requests

ORIGINAL = object()
OVERRIDDEN = object()

def before_request(request):
    return ORIGINAL

def override_before_request(request):
    return OVERRIDDEN


pytestmark = pytest.mark.vcr(before_record_request=before_request)

GET_CASSETTE = "{}"

@pytest.mark.vcr
def test_custom_path(vcr):
    assert vcr._before_record_request("mock") is ORIGINAL

@pytest.mark.vcr(before_record_request=override_before_request)
def test_custom_path_with_kwargs(vcr):
    assert vcr._before_record_request("mock") is OVERRIDDEN
    """.format(get_response_cassette)
    )
    # Then each test function should have cassettes with merged kwargs
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_single_kwargs(testdir):
    # When the closest vcr mark contains kwargs
    testdir.makepyfile(
        """
import pytest
import requests

def before_request(request):
    raise ValueError("Before")

@pytest.mark.vcr(before_record_request=before_request)
def test_single_kwargs():
    with pytest.raises(ValueError, match="Before"):
        requests.get("http://httpbin.org/get")

    """
    )
    # Then the VCR instance associated with the test function should get these kwargs
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_cassettes_in_mark(testdir, get_response_cassette, ip_response_cassette):
    # When multiple cassettes are specified in pytest.mark.vcr
    testdir.makepyfile(
        """
import pytest
import requests

@pytest.mark.vcr("{}", "{}")
def test_custom_path():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'
    """.format(get_response_cassette, ip_response_cassette)
    )
    # Then they should be combined with each other
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_repeated_cassettes(testdir, mocker, get_response_cassette):
    # When the same cassette is specified multiple times in the same mark or in different ones
    testdir.makepyfile(
        """
import pytest
import requests

CASSETTE = "{}"

pytestmark = [pytest.mark.vcr(CASSETTE)]

@pytest.mark.vcr(CASSETTE, CASSETTE)
def test_custom_path():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    """.format(get_response_cassette)
    )
    # Then the cassette will be loaded only once
    # And will not produce any errors
    mocked_load_cassette = mocker.patch("pytest_recording._vcr.load_cassette", wraps=load_cassette)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    # Default one + extra one
    assert mocked_load_cassette.call_count == 2


def test_class_mark(testdir, get_response_cassette, ip_response_cassette):
    # When pytest.mark.vcr is applied to a class
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr("{}")]

@pytest.mark.vcr("{}")
class TestSomething:

    @pytest.mark.vcr()
    def test_custom_path(self):
        assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
        assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'
    """.format(get_response_cassette, ip_response_cassette)
    )
    # Then it should be combined with the other marks
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_own_mark(testdir, get_response_cassette, create_file, ip_cassette):
    # When a test doesn't have its own mark
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr("{}")]


def test_own():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'
    """.format(get_response_cassette)
    )
    create_file("cassettes/test_own_mark/test_own.yaml", ip_cassette)
    # Then it should use a cassette with a default name
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("scope", ("function", "module", "session"))
def test_global_config(testdir, scope):
    # When there is a `vcr_config` fixture
    testdir.makepyfile(
        """
import pytest
import requests

EXPECTED = object()

@pytest.fixture(scope="{}")
def vcr_config():
    return {{"before_record_request": before_request}}

def before_request(request):
    return EXPECTED

@pytest.mark.vcr
def test_own(vcr):
    assert vcr._before_record_request("mock") is EXPECTED
    """.format(scope)
    )
    # Then its config values should be merged with test-specific ones
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)


def test_name_collision(testdir, create_file, ip_cassette, get_cassette):
    # When different test files contains tests with the same names
    testdir.makepyfile(
        test_a="""
import pytest
import requests

@pytest.mark.vcr
def test_feature():
    assert requests.get("http://httpbin.org/get").text == '{"get": true}'
    """
    )
    testdir.makepyfile(
        test_b="""
import pytest
import requests

@pytest.mark.vcr
def test_feature():
    assert requests.get("http://httpbin.org/ip").text == '{"ip": true}'
    """
    )
    # Then cassettes should not collide with each other, they should be separate
    create_file("cassettes/test_a/test_feature.yaml", get_cassette)
    create_file("cassettes/test_b/test_feature.yaml", ip_cassette)
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_global_mark(testdir, create_file, get_cassette):
    # When only global vcr mark is applied without parameters
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr]


def test_feature():
    assert requests.get("http://httpbin.org/get").text == '{"get": true}'
    """
    )
    # Then tests without own marks should use test function names for cassettes
    create_file("cassettes/test_global_mark/test_feature.yaml", get_cassette)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@pytest.mark.skipif(
    VCR_VERSION >= (4, 4, 0),
    reason="Newer VCRpy versions do not use the `assert` statement in matchers",
)
def test_assertions_rewrite(testdir, create_file, get_cassette):
    # When a response match is not found
    testdir.makepyfile(
        """
import pytest
import requests

pytestmark = [pytest.mark.vcr]

def test_feature():
    assert requests.post("http://httpbin.org/get?a=1").text == "{'get': true}"
    """
    )
    create_file("cassettes/test_assertions_rewrite/test_feature.yaml", get_cassette)
    result = testdir.runpytest()
    result.assert_outcomes(failed=1)
    # Then assertions should be rewritten
    result.stdout.fnmatch_lines(["*assert 'POST' == 'GET'", "*Left contains one more item: ('a', '1')"])


def test_default_cassette_always_exist(testdir, create_file, ip_cassette, get_response_cassette):
    # When any test with VCR mark is performed
    testdir.makepyfile(
        """
import pytest
import requests


@pytest.mark.vcr("{}")
def test_feature():
    assert requests.get("http://httpbin.org/get").text == '{{"get": true}}'
    assert requests.get("http://httpbin.org/ip").text == '{{"ip": true}}'
    """.format(get_response_cassette)
    )
    # Then the default cassette should always be used together with the extra one
    create_file("cassettes/test_default_cassette_always_exist/test_feature.yaml", ip_cassette)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_relative_cassette_path(testdir, create_file, ip_cassette, get_cassette):
    # When a relative path is used in `pytest.mark.vcr`
    testdir.makepyfile(
        """
import pytest
import requests


@pytest.mark.vcr("ip_cassette.yaml")
def test_feature():
    assert requests.get("http://httpbin.org/get").text == '{"get": true}'
    assert requests.get("http://httpbin.org/ip").text == '{"ip": true}'
    """
    )
    create_file("cassettes/test_relative_cassette_path/test_feature.yaml", get_cassette)
    create_file("cassettes/test_relative_cassette_path/ip_cassette.yaml", ip_cassette)
    result = testdir.runpytest()
    # Then it should be properly loaded and used
    result.assert_outcomes(passed=1)


def test_recording_configure_hook(testdir):
    testdir.makeconftest(
        """
def pytest_recording_configure(config, vcr):
    print("HOOK IS CALLED")
        """
    )
    testdir.makepyfile(
        """
import pytest

@pytest.mark.vcr
def test_feature():
    pass
    """
    )
    result = testdir.runpytest("-s")
    assert "test_recording_configure_hook.py HOOK IS CALLED" in result.outlines
