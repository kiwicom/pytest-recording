.. _changelog:

Changelog
=========

`Unreleased`_
-------------

`0.12.1`_ - 2022-06-20
----------------------

- Allow ``block_network.allowed_hosts`` configuration via ``vcr_config`` fixture. `#82`_

`0.12.0`_ - 2021-07-08
----------------------

Fixed
~~~~~

- Honor ``record_mode`` set via the ``vcr_config`` fixture or the ``vcr`` mark when ``block_network`` is applied. `#68`_

Changed
~~~~~~~

- Validate input arguments for the ``block_network`` pytest mark. `#69`_

`0.11.0`_ - 2020-11-25
----------------------

Added
~~~~~

- ``--disable-recording`` CLI option to completely disable the VCR.py integration. `#64`_

`0.10.0`_ - 2020-10-06
----------------------

Added
~~~~~

- The ``pytest.mark.default_cassette`` marker that overrides the default cassette name.

`0.9.0`_ - 2020-08-13
---------------------

Added
~~~~~

- Type annotations to the plugin's internals.

Fixed
~~~~~

- ``TypeError`` when using network blocking with address as ``bytes`` or ``bytearray``. `#55`_

Removed
~~~~~~~

- Python 2 support. `#53`_

`0.8.1`_ - 2020-06-13
---------------------

Fixed
~~~~~

- Honor ``record_mode`` passed via ``pytest.mark.vcr`` mark or in ``vcr_config`` fixture. `#47`_

`0.8.0`_ - 2020-06-06
---------------------

Added
~~~~~

- New ``pytest_recording_configure`` hook that can be used for registering custom matchers, persisters, etc. `#45`_

`0.7.0`_ - 2020-04-18
---------------------

Added
~~~~~

- New ``rewrite`` mode that removes cassette before recording. `#37`_

`0.6.0`_ - 2020-01-23
---------------------

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

.. _Unreleased: https://github.com/kiwicom/pytest-recording/compare/v0.12.1...HEAD
.. _0.12.1: https://github.com/kiwicom/pytest-recording/compare/v0.12.0...v0.12.1
.. _0.12.0: https://github.com/kiwicom/pytest-recording/compare/v0.11.0...v0.12.0
.. _0.11.0: https://github.com/kiwicom/pytest-recording/compare/v0.10.0...v0.11.0
.. _0.10.0: https://github.com/kiwicom/pytest-recording/compare/v0.9.0...v0.10.0
.. _0.9.0: https://github.com/kiwicom/pytest-recording/compare/v0.8.1...v0.9.0
.. _0.8.1: https://github.com/kiwicom/pytest-recording/compare/v0.8.0...v0.8.1
.. _0.8.0: https://github.com/kiwicom/pytest-recording/compare/v0.7.0...v0.8.0
.. _0.7.0: https://github.com/kiwicom/pytest-recording/compare/v0.6.0...v0.7.0
.. _0.6.0: https://github.com/kiwicom/pytest-recording/compare/v0.5.0...v0.6.0
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

.. _#82: https://github.com/kiwicom/pytest-recording/pull/82
.. _#69: https://github.com/kiwicom/pytest-recording/issues/69
.. _#68: https://github.com/kiwicom/pytest-recording/issues/68
.. _#64: https://github.com/kiwicom/pytest-recording/issues/64
.. _#55: https://github.com/kiwicom/pytest-recording/issues/55
.. _#53: https://github.com/kiwicom/pytest-recording/issues/53
.. _#47: https://github.com/kiwicom/pytest-recording/issues/47
.. _#45: https://github.com/kiwicom/pytest-recording/issues/45
.. _#37: https://github.com/kiwicom/pytest-recording/issues/37
.. _#34: https://github.com/kiwicom/pytest-recording/issues/34
.. _#20: https://github.com/kiwicom/pytest-recording/issues/20
.. _#10: https://github.com/kiwicom/pytest-recording/issues/10
.. _#8: https://github.com/kiwicom/pytest-recording/issues/8
.. _#7: https://github.com/kiwicom/pytest-recording/issues/7
.. _#2: https://github.com/kiwicom/pytest-recording/issues/2
