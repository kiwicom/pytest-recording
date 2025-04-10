import pytest

pytest_plugins = "pytester"


@pytest.fixture
def pytester(pytester):
    original_runpytest = pytester.runpytest

    def runpytest(*args, **kwargs):
        args = ("-p no:pretty", *args)
        return original_runpytest(*args, **kwargs)

    pytester.runpytest = runpytest
    return pytester


@pytest.fixture
def create_file(testdir):
    def inner(path, content):
        path = testdir.tmpdir.join(path)
        path.ensure().write(content)
        return path

    return inner


CASSETTE_TEMPLATE = """
version: 1
interactions:
- request:
    body: null
    headers: {{}}
    method: GET
    uri: http://httpbin.org{}
  response:
    body: {{string: '{}'}}
    headers: {{}}
    status: {{code: 200, message: OK}}"""
GET_CASSETTE = CASSETTE_TEMPLATE.format("/get", '{"get": true}')
IP_CASSETTE = CASSETTE_TEMPLATE.format("/ip", '{"ip": true}')


@pytest.fixture
def get_cassette():
    return GET_CASSETTE


@pytest.fixture
def ip_cassette():
    return IP_CASSETTE


@pytest.fixture
def get_response_cassette(create_file, get_cassette):
    return create_file("get.yaml", get_cassette)


@pytest.fixture
def ip_response_cassette(create_file, ip_cassette):
    return create_file("ip.yaml", ip_cassette)
