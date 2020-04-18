pytest-recording
================

|codecov| |Build| |Version| |Python versions| |License|

A pytest plugin that allows to record network interactions via VCR.py.

Features
--------

- Straightforward ``pytest.mark.vcr``, that reflects ``VCR.use_cassettes`` API;
- Combining multiple VCR cassettes;
- Network access blocking.

Usage
-----

.. code:: python

    import pytest
    import requests

    # cassettes/{module_name}/test_single.yaml will be used
    @pytest.mark.vcr
    def test_single():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'

    # these cassettes will be used in addition to the default one
    @pytest.mark.vcr("/path/to/ip.yaml", "/path/to/get.yaml")
    def test_multiple():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'
        assert requests.get("http://httpbin.org/ip").text == '{"ip": true}'

Configuration
~~~~~~~~~~~~~

The recording configuration could be provided with ``vcr_config`` fixture, which could be any scope - ``session``,
``package``, ``module`` or ``function``. It should return a dictionary that will be passed directly to ``VCR.use_cassettes``
under the hood.

.. code:: python

    import pytest

    @pytest.fixture(scope="module")
    def vcr_config():
        return {"filter_headers": ["authorization"]}

For more granular control you need to pass these keyword arguments to individual ``pytest.mark.vcr`` marks, and in this case
all arguments will be merged into a single dictionary with the following priority (low -> high):

- ``vcr_config`` fixture
- all marks from the most broad scope ("session") to the most narrow one ("function")

Example:

.. code:: python

    import pytest

    pytestmark = [pytest.mark.vcr(ignore_localhost=True)]

    @pytest.fixture(scope="module")
    def vcr_config():
        return {"filter_headers": ["authorization"]}

    @pytest.mark.vcr(filter_headers=[])
    def test_one():
        ...

    @pytest.mark.vcr(filter_query_parameters=["api_key"])
    def test_two():
        ...

Resulting VCR configs for each test:

- ``test_one`` - ``{"ignore_localhost": True, "filter_headers": []}``
- ``test_two`` - ``{"ignore_localhost": True, "filter_headers": ["authorization"], "filter_query_parameters": ["api_key"]}``


`rewrite` record mode
~~~~~~~~~~~~~~~~~~~~~


It possible to rewrite cassette from scratch,
and not to to append as it is done with ``all`` record mode in current ``VCR.py`` implementation.

However, it will rewrite only default first cassette, any extra cassettes provided will not be touched.

.. code:: python

    import pytest

    @pytest.fixture(scope="module")
    def vcr_config():
        return {"record_mode": "rewrite"}

Or via command line option:

.. code:: bash

    $ pytest --record-mode=rewrite tests/


Blocking network access
~~~~~~~~~~~~~~~~~~~~~~~

To have more confidence that your tests will not go over the wire, you can block it with ``pytest.mark.block_network`` mark:

.. code:: python

    import pytest
    import requests

    @pytest.mark.block_network
    def test_multiple():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'

    ...
    # in case of access
    RuntimeError: Network is disabled

Besides marks, the network access could be blocked globally with ``--block-network`` command-line option.

However, if VCR.py recording is enabled then, the network is not blocked for tests, that have ``pytest.mark.vcr``.

Example:

.. code:: python

    import pytest
    import requests

    @pytest.mark.vcr
    def test_multiple():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'

Run ``pytest``:

.. code:: bash

    $ pytest --record-mode=once --block-network tests/

The network blocking feature supports ``socket``-based transports and ``pycurl``.

It is possible to allow access to specified hosts during network blocking:

.. code:: python

    import pytest
    import requests

    @pytest.mark.block_network(allowed_hosts=["httpbin.*"])
    def test_access():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'
        with pytest.raises(RuntimeError, match=r"^Network is disabled$"):
            requests.get("http://example.com")

Or via command line option:

.. code:: bash

    $ pytest --record-mode=once --block-network --allowed-hosts=httpbin.*,localhost tests/

Contributing
------------

To run the tests:

.. code:: bash

    $ tox -p all

If you have troubles with installing ``pycurl`` with ``tox``, you could try to pass ``CPPFLAGS`` and ``LDFLAGS``
with the ``tox`` command:

.. code:: bash

    $  CPPFLAGS="-I/usr/local/opt/openssl/include" LDFLAGS="-L/usr/local/opt/openssl/lib" tox -p all

Python support
--------------

Pytest-recording supports:

- CPython 2.7, 3.5, 3.6, 3.7 and 3.8.
- PyPy 7 (2.7 & 3.6)

License
-------

The code in this project is licensed under `MIT license`_. By contributing to ``pytest-recording``, you agree that your contributions will be licensed under its MIT license.


.. |codecov| image:: https://codecov.io/gh/kiwicom/pytest-recording/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/kiwicom/pytest-recording
.. |Build| image:: https://travis-ci.org/kiwicom/pytest-recording.svg?branch=master
   :target: https://travis-ci.org/kiwicom/pytest-recording
.. |Version| image:: https://img.shields.io/pypi/v/pytest-recording.svg
   :target: https://pypi.org/project/pytest-recording/
.. |Python versions| image:: https://img.shields.io/pypi/pyversions/pytest-recording.svg
   :target: https://pypi.org/project/pytest-recording/
.. |License| image:: https://img.shields.io/pypi/l/pytest-recording.svg
   :target: https://opensource.org/licenses/MIT

.. _MIT license: https://opensource.org/licenses/MIT
