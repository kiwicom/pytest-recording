.. _changelog:

Changelog
=========

`Unreleased`_
-------------

Added
~~~~~

- A pytest mark to block all network requests, except for VCR recording.

`0.2.0`_ - 2019-07-18
---------------------

Added
~~~~~

- Reusable ``vcr_config`` fixture for ``VCR.use_cassette`` call. `#2`_

0.1.0 - 2019-07-16
------------------

- Initial public release

.. _Unreleased: https://github.com/kiwicom/pytest-recording/compare/0.2.0...HEAD
.. _0.2.0: https://github.com/kiwicom/pytest-recording/compare/0.1.0...0.2.0

.. _#2: https://github.com/kiwicom/pytest-recording/issues/2