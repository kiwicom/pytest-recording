pytest-recording
================

|codecov| |Build| |Version| |Python versions| |License|

A pytest plugin that records network interactions in your tests via VCR.py.

Features
--------

- Straightforward ``pytest.mark.vcr``, that reflects ``VCR.use_cassettes`` API;
- Combining multiple VCR cassettes;
- Network access blocking;
- The ``rewrite`` recording mode that rewrites cassettes from scratch.

Usage
-----

.. code:: python

    import pytest
    import requests

    # cassettes/{module_name}/test_single.yaml will be used
    @pytest.mark.vcr
    def test_single():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'

    # cassettes/{module_name}/example.yaml will be used
    @pytest.mark.default_cassette("example.yaml")
    @pytest.mark.vcr
    def test_default():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'

    # these cassettes will be used in addition to the default one
    @pytest.mark.vcr("/path/to/ip.yaml", "/path/to/get.yaml")
    def test_multiple():
        assert requests.get("http://httpbin.org/get").text == '{"get": true}'
        assert requests.get("http://httpbin.org/ip").text == '{"ip": true}'

Run your tests:

.. code:: bash

    pytest --record-mode=once test_network.py

Default recording mode
~~~~~~~~~~~~~~~~~~~~~~

``pytest-recording`` uses the ``none`` VCR recording mode by default to prevent unintentional network requests.
To allow them you need to pass a different recording mode (e.g. ``once``) via the ``--record-mode`` CLI option to your test command.
See more information about available recording modes in the `official VCR documentation <https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes>`_

Configuration
~~~~~~~~~~~~~

You can provide the recording configuration with the ``vcr_config`` fixture, which could be any scope - ``session``,
``package``, ``module``, or ``function``. It should return a dictionary that will be passed directly to ``VCR.use_cassettes``
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

You can get access to the used ``VCR`` instance via ``pytest_recording_configure`` hook. It might be useful for registering
custom matchers, persisters, etc.:

.. code:: python

    # conftest.py

    def jurassic_matcher(r1, r2):
        assert r1.uri == r2.uri and "JURASSIC PARK" in r1.body, \
            "required string (JURASSIC PARK) not found in request body"

    def pytest_recording_configure(config, vcr):
        vcr.register_matcher("jurassic", jurassic_matcher)

You can disable the VCR.py integration entirely by passing the ``--disable-recording`` CLI option.

Rewrite record mode
~~~~~~~~~~~~~~~~~~~

It is possible to rewrite a cassette from scratch and not extend it with new entries as it works now with the ``all`` record mode from VCR.py.

However, it will rewrite only the default cassette and won't touch extra cassettes.

.. code:: python

    import pytest

    @pytest.fixture(scope="module")
    def vcr_config():
        return {"record_mode": "rewrite"}

Or via command-line option:

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

However, if VCR.py recording is enabled, the network is not blocked for tests with ``pytest.mark.vcr``.

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

Or via command-line option:

.. code:: bash

    $ pytest --record-mode=once --block-network --allowed-hosts=httpbin.*,localhost tests/


Or via `vcr_config` fixture:

.. code:: python

    import pytest

    @pytest.fixture(autouse=True)
    def vcr_config():
        return {"allowed_hosts": ["httpbin.*"]}

Additional resources
--------------------

Looking for more examples? Check out `this article <https://code.kiwi.com/pytest-cassettes-forget-about-mocks-or-live-requests-a9336e1caee6>`_ about ``pytest-recording``.

Contributing
------------

To run the tests:

.. code:: bash

    $ tox -p all

For more information, take a look at `our contributing guide <https://github.com/kiwicom/pytest-recording/blob/master/CONTRIBUTING.rst>`_

Python support
--------------

Pytest-recording supports:

- CPython 3.5, 3.6, 3.7, 3.8, 3.9, 3.10 and 3.11
- PyPy 7 (3.6)

License
-------

The code in this project is licensed under `MIT license`_. By contributing to ``pytest-recording``, you agree that your contributions will be licensed under its MIT license.


.. |codecov| image:: https://codecov.io/gh/kiwicom/pytest-recording/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/kiwicom/pytest-recording
.. |Build| image:: https://github.com/kiwicom/pytest-recording/actions/workflows/build.yml/badge.svg
   :target: https://github.com/kiwicom/pytest-recording/actions?query=workflow%3Abuild
.. |Version| image:: https://img.shields.io/pypi/v/pytest-recording.svg
   :target: https://pypi.org/project/pytest-recording/
.. |Python versions| image:: https://img.shields.io/pypi/pyversions/pytest-recording.svg
   :target: https://pypi.org/project/pytest-recording/
.. |License| image:: https://img.shields.io/pypi/l/pytest-recording.svg
   :target: https://opensource.org/licenses/MIT

.. _MIT license: https://opensource.org/licenses/MIT
