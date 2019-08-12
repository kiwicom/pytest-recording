import pytest

from pytest_recording import mutations


def test_status_code(testdir, get_response_cassette):
    # When status_code mutation is specified
    testdir.makepyfile(
        """
import pytest
import requests
from pytest_recording import mutations

STATUS_CODES = (400, 401, 418, 500, 501)

@pytest.mark.vcr_mutations(mutations=mutations.status_code(code=STATUS_CODES))
@pytest.mark.vcr("{}")
def test_status_code(mutation):
    assert requests.get("http://httpbin.org/get").status_code == mutation.context["code"]
    """.format(
            get_response_cassette
        )
    )
    # Then 5 tests should be generated with mutated cassettes
    result = testdir.runpytest()
    result.assert_outcomes(passed=5)


@pytest.mark.parametrize("mutation", ("malform_body", "empty_body"))
def test_change_body(testdir, get_response_cassette, mutation):
    # When body-changing mutation is specified
    testdir.makepyfile(
        """
try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
import pytest
import requests
from pytest_recording import mutations

@pytest.mark.vcr_mutations(mutations=mutations.{})
@pytest.mark.vcr("{}")
def test_change_body(mutation):
    try:
        requests.get("http://httpbin.org/get").json()
    except JSONDecodeError:
        pass
    """.format(
            mutation, get_response_cassette
        )
    )
    # Then cassettes should be mutated - body is changed
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_combined(testdir, get_response_cassette):
    # When mutations are combined with "|" symbol
    testdir.makepyfile(
        """
# Remove try/except after dropping Python 2
try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
import pytest
import requests
from pytest_recording import mutations

@pytest.mark.vcr_mutations(
    mutations=[
        mutations.empty_body,
        mutations.malform_body, 
        mutations.status_code(code=502),
        mutations.status_code(code=[400, 401])
    ]
)
@pytest.mark.vcr("{}")
def test_combined(mutation):
    try:
        response = requests.get("http://httpbin.org/get")
        response.json()
    except JSONDecodeError:
        pass
    """.format(
            get_response_cassette
        )
    )
    # Then all mutations should be applied and N test cases should be generated
    result = testdir.runpytest()
    result.assert_outcomes(passed=5)


def test_mutation_context(testdir, get_response_cassette):
    # When mutation is called with some arguments in the mark
    testdir.makepyfile(
        """
import pytest
from pytest_recording import mutations

@mutations.mutation
def mut(cassette, test):
    print("CONTEXT:", test)

@pytest.mark.vcr_mutations(mutations=mut(test=123))
@pytest.mark.vcr("{}")
def test_mutation_context(mutation):
    pass

    """.format(
            get_response_cassette
        )
    )
    # Then these arguments should be passed in mutation when mutation is applied
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*CONTEXT*:* 123*"])


@pytest.mark.parametrize("kwargs", ({}, {"a": 1}))
def test_signature(kwargs):
    # When an invalid argument is passed to a mutation
    with pytest.raises(TypeError):
        # Then TypeError should happen early, not during the test run
        mutations.status_code(**kwargs)


def test_mark_signature(testdir, get_response_cassette):
    # When `vcr_mutations` mark is applied with wrong arguments
    testdir.makepyfile(
        """
import pytest
from pytest_recording import mutations

@mutations.mutation
def mut(cassette, test):
    print("CONTEXT:", test)

@pytest.mark.vcr_mutations(mutationZ=mutations.empty_body)  # A typo
@pytest.mark.vcr("{}")
def test_mark_signature(mutation):
    pass

    """.format(
            get_response_cassette
        )
    )
    # Then tests should fail early
    result = testdir.runpytest()
    result.assert_outcomes(error=1)


# TODO. what about different content types in cassettes?
# What if it is gzipped?
