pytest-recording
================

|codecov| |Build| |Version| |Python versions| |License|

**WIP**

A pytest plugin that allows to record network interactions via VCR.py.

Features
--------

- Straightforward ``pytest.mark.vcr``, that reflects ``VCR.use_cassettes`` API;
- Combining multiple VCR cassettes;

Usage
-----

.. code:: python

    import pytest
    import requests

    @pytest.mark.vcr("/path/to/ip.yaml", "/path/to/get.yaml")
    def test_multiple():
        assert requests.get("http://httpbin.org/get").text == "GET CONTENT"
        assert requests.get("http://httpbin.org/ip").text == "IP CONTENT"

    # cassettes/test_single.yaml will be used
    def test_single():
        assert requests.get("http://httpbin.org/get").text == "GET CONTENT"

Python support
--------------

Pytest-recording supports Python 2.7, 3.5, 3.6, 3.7 and 3.8.

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