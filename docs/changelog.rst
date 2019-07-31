.. _changelog:

Changelog
=========

`Unreleased`_
-------------

Fixed
~~~~~

- Do not add "yaml" extension to cassettes if JSON serializer is used. `#10`_

`0.3.1`_ - 2019-07-28
---------------------

Added
~~~~~

- ``network.block`` / ``network.unblock`` functions for manual network blocking manipulations. `#8`_

`0.3.0`_ - 2019-07-20
---------------------

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

.. _Unreleased: https://github.com/kiwicom/pytest-recording/compare/v0.3.0...HEAD
.. _0.3.0: https://github.com/kiwicom/pytest-recording/compare/v0.2.0...v0.3.0
.. _0.2.0: https://github.com/kiwicom/pytest-recording/compare/v0.1.0...v0.2.0

.. _#10: https://github.com/kiwicom/pytest-recording/issues/10
.. _#8: https://github.com/kiwicom/pytest-recording/issues/8
.. _#2: https://github.com/kiwicom/pytest-recording/issues/2