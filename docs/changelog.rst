.. _changelog:

Changelog
=========

`Unreleased`_
-------------

Changed
~~~~~~~

- Restore undocumented ability to use relative paths in ``pytest.mark.vcr``. `#34`_

`0.5.0`_ - 2020-01-09
---------------------

Changed
~~~~~~~

- Default cassette (usually named as the test function name) always exists. This changes the behavior in two ways.
  Firstly, recording will happen only to the default cassette and will not happen to any cassette passed as an argument to ``pytest.mark.vcr``
  Secondly, it will allow "shared" + "specific" usage pattern, when the default cassette contains data relevant only to
  the specific test and the custom one contains shared data, which is currently only possible with specifying full paths
  to both cassettes in ``pytest.mark.vcr``.

`0.4.0`_ - 2019-12-19
---------------------

Added
~~~~~

- Ability to list allowed hosts for ``block_network``. `#7`_

`0.3.6`_ - 2019-12-17
---------------------

Fixed
~~~~~

- Setting attributes on ``pycurl.Curl`` instances

`0.3.5`_ - 2019-11-18
---------------------

Fixed
~~~~~

- Broken packaging in ``0.3.4``.

`0.3.4`_ - 2019-10-21
---------------------

Added
~~~~~

- An error is raised if ``pytest-vcr`` is installed. ``pytest-recording`` is not compatible with it. `#20`_

`0.3.3`_ - 2019-08-18
---------------------

Added
~~~~~

- Pytest assertion rewriting for not matched requests.

`0.3.2`_ - 2019-08-01
---------------------

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

.. _Unreleased: https://github.com/kiwicom/pytest-recording/compare/v0.5.0...HEAD
.. _0.5.0: https://github.com/kiwicom/pytest-recording/compare/v0.4.0...v0.5.0
.. _0.4.0: https://github.com/kiwicom/pytest-recording/compare/v0.3.6...v0.4.0
.. _0.3.6: https://github.com/kiwicom/pytest-recording/compare/v0.3.4...v0.3.6
.. _0.3.5: https://github.com/kiwicom/pytest-recording/compare/v0.3.4...v0.3.4
.. _0.3.4: https://github.com/kiwicom/pytest-recording/compare/v0.3.3...v0.3.4
.. _0.3.3: https://github.com/kiwicom/pytest-recording/compare/v0.3.2...v0.3.3
.. _0.3.2: https://github.com/kiwicom/pytest-recording/compare/v0.3.1...v0.3.2
.. _0.3.1: https://github.com/kiwicom/pytest-recording/compare/v0.3.0...v0.3.1
.. _0.3.0: https://github.com/kiwicom/pytest-recording/compare/v0.2.0...v0.3.0
.. _0.2.0: https://github.com/kiwicom/pytest-recording/compare/v0.1.0...v0.2.0

.. _#34: https://github.com/kiwicom/pytest-recording/issues/34
.. _#20: https://github.com/kiwicom/pytest-recording/issues/20
.. _#10: https://github.com/kiwicom/pytest-recording/issues/10
.. _#8: https://github.com/kiwicom/pytest-recording/issues/8
.. _#7: https://github.com/kiwicom/pytest-recording/issues/7
.. _#2: https://github.com/kiwicom/pytest-recording/issues/2
