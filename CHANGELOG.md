# Changelog

## [Unreleased]

### Added

- `transports` argument for `network.block`, `network.unblock` and `network.blocking_context` to select socket and/or pycurl blocking. [#16]
- `allow_private_ips` option that allows connections to private IP addresses while network is blocked. [#74]
- Allowed hosts in the `Network is disabled` error message. [#63]

### Changed

- A failure to remove an existing cassette in the `rewrite` record mode emits a warning instead of being silently ignored. [#198]
- Minimum supported versions are `vcrpy` 4.0.2 and `pytest` 6.2.5.

### Documentation

- Overriding the `vcr_cassette_dir` fixture to change where cassettes are looked up. [#151]
- `allowed_hosts` matching IP addresses for socket-based clients. [#40]

## [0.14.1] - 2026-11-02

### Added

- Blocked host in the `Network is disabled` error message. [#190]

### Fixed

- Blocked `socket.socketpair()` inside the blocking context, which prevented building asyncio event loops on Windows. [#212]

## [0.14.0] - 2026-10-02

### Added

- Support for Python 3.14 and 3.15. [#185]

### Fixed

- `ValueError: 'rewrite' is not a valid record_mode` raised by VCR.py 8.2.1+ when the `rewrite` mode is set via the `vcr_config` fixture or the `vcr` mark. [#205]

### Removed

- Support for Python 3.9. [#185]

### Documentation

- `ignore_hosts` in the `vcr_config` fixture example. [#170]

## [0.13.4] - 2025-04-24

### Fixed

- `AttributeError` on Windows. [#174]

## [0.13.3] - 2025-04-24

### Fixed

- `OSError` caused by too long generated cassette names. [#172]

## [0.13.2] - 2024-07-09

### Changed

- Lazy loading of VCR.py to reduce plugin overhead. [#145]

### Documentation

- General improvements.

## [0.13.1] - 2023-12-07

### Added

- Support for Python 3.12.
- Trove classifier for license.

## [0.13.0] - 2023-08-01

### Added

- Support for VCR.py 5.0.0. [#118]

### Changed

- [Hatch](https://hatch.pypa.io/) as the build backend.

### Removed

- Support for Python 3.5 and 3.6. [#97]
- Direct dependency on `attrs`.

## [0.12.2] - 2023-02-16

### Added

- Support for Python 3.10 and 3.11. [#99]

## [0.12.1] - 2022-06-20

### Added

- `block_network.allowed_hosts` configuration via the `vcr_config` fixture. [#82]

## [0.12.0] - 2021-07-08

### Fixed

- Honor `record_mode` set via the `vcr_config` fixture or the `vcr` mark when `block_network` is applied. [#68]

### Changed

- Validate input arguments for the `block_network` pytest mark. [#69]

## [0.11.0] - 2020-11-25

### Added

- `--disable-recording` CLI option to completely disable the VCR.py integration. [#64]

## [0.10.0] - 2020-10-06

### Added

- The `pytest.mark.default_cassette` marker that overrides the default cassette name.

## [0.9.0] - 2020-08-13

### Added

- Type annotations to the plugin's internals.

### Fixed

- `TypeError` when using network blocking with address as `bytes` or `bytearray`. [#55]

### Removed

- Python 2 support. [#53]

## [0.8.1] - 2020-06-13

### Fixed

- Honor `record_mode` passed via `pytest.mark.vcr` mark or in `vcr_config` fixture. [#47]

## [0.8.0] - 2020-06-06

### Added

- New `pytest_recording_configure` hook that can be used for registering custom matchers, persisters, etc. [#45]

## [0.7.0] - 2020-04-18

### Added

- New `rewrite` mode that removes cassette before recording. [#37]

## [0.6.0] - 2020-01-23

### Changed

- Restore undocumented ability to use relative paths in `pytest.mark.vcr`. [#34]

## [0.5.0] - 2020-01-09

### Changed

- Default cassette (usually named as the test function name) always exists. This changes the behavior in two ways.
  Firstly, recording will happen only to the default cassette and will not happen to any cassette passed as an argument to `pytest.mark.vcr`
  Secondly, it will allow "shared" + "specific" usage pattern, when the default cassette contains data relevant only to
  the specific test and the custom one contains shared data, which is currently only possible with specifying full paths
  to both cassettes in `pytest.mark.vcr`.

## [0.4.0] - 2019-12-19

### Added

- Ability to list allowed hosts for `block_network`. [#7]

## [0.3.6] - 2019-12-17

### Fixed

- Setting attributes on `pycurl.Curl` instances

## 0.3.5 - 2019-11-18

### Fixed

- Broken packaging in `0.3.4`.

## [0.3.4] - 2019-10-21

### Added

- An error is raised if `pytest-vcr` is installed. `pytest-recording` is not compatible with it. [#20]

## [0.3.3] - 2019-08-18

### Added

- Pytest assertion rewriting for not matched requests.

## [0.3.2] - 2019-08-01

### Fixed

- Do not add "yaml" extension to cassettes if JSON serializer is used. [#10]

## [0.3.1] - 2019-07-28

### Added

- `network.block` / `network.unblock` functions for manual network blocking manipulations. [#8]

## [0.3.0] - 2019-07-20

### Added

- A pytest mark to block all network requests, except for VCR recording.

## [0.2.0] - 2019-07-18

### Added

- Reusable `vcr_config` fixture for `VCR.use_cassette` call. [#2]

## 0.1.0 - 2019-07-16

- Initial public release

[Unreleased]: https://github.com/kiwicom/pytest-recording/compare/v0.14.1...HEAD
[0.14.1]: https://github.com/kiwicom/pytest-recording/compare/v0.14.0...v0.14.1
[0.14.0]: https://github.com/kiwicom/pytest-recording/compare/v0.13.4...v0.14.0
[0.13.4]: https://github.com/kiwicom/pytest-recording/compare/v0.13.3...v0.13.4
[0.13.3]: https://github.com/kiwicom/pytest-recording/compare/v0.13.2...v0.13.3
[0.13.2]: https://github.com/kiwicom/pytest-recording/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/kiwicom/pytest-recording/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/kiwicom/pytest-recording/compare/v0.12.2...v0.13.0
[0.12.2]: https://github.com/kiwicom/pytest-recording/compare/v0.12.1...v0.12.2
[0.12.1]: https://github.com/kiwicom/pytest-recording/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/kiwicom/pytest-recording/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/kiwicom/pytest-recording/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/kiwicom/pytest-recording/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/kiwicom/pytest-recording/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/kiwicom/pytest-recording/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/kiwicom/pytest-recording/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/kiwicom/pytest-recording/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/kiwicom/pytest-recording/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/kiwicom/pytest-recording/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/kiwicom/pytest-recording/compare/v0.3.6...v0.4.0
[0.3.6]: https://github.com/kiwicom/pytest-recording/compare/v0.3.4...v0.3.6
[0.3.4]: https://github.com/kiwicom/pytest-recording/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/kiwicom/pytest-recording/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/kiwicom/pytest-recording/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/kiwicom/pytest-recording/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/kiwicom/pytest-recording/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kiwicom/pytest-recording/compare/v0.1.0...v0.2.0

[#212]: https://github.com/kiwicom/pytest-recording/issues/212
[#205]: https://github.com/kiwicom/pytest-recording/pull/205
[#198]: https://github.com/kiwicom/pytest-recording/issues/198
[#190]: https://github.com/kiwicom/pytest-recording/pull/190
[#185]: https://github.com/kiwicom/pytest-recording/pull/185
[#174]: https://github.com/kiwicom/pytest-recording/issues/174
[#172]: https://github.com/kiwicom/pytest-recording/issues/172
[#170]: https://github.com/kiwicom/pytest-recording/issues/170
[#151]: https://github.com/kiwicom/pytest-recording/issues/151
[#145]: https://github.com/kiwicom/pytest-recording/issues/145
[#118]: https://github.com/kiwicom/pytest-recording/pull/118
[#99]: https://github.com/kiwicom/pytest-recording/pull/99
[#97]: https://github.com/kiwicom/pytest-recording/issues/97
[#82]: https://github.com/kiwicom/pytest-recording/pull/82
[#74]: https://github.com/kiwicom/pytest-recording/issues/74
[#69]: https://github.com/kiwicom/pytest-recording/issues/69
[#68]: https://github.com/kiwicom/pytest-recording/issues/68
[#64]: https://github.com/kiwicom/pytest-recording/issues/64
[#63]: https://github.com/kiwicom/pytest-recording/issues/63
[#55]: https://github.com/kiwicom/pytest-recording/issues/55
[#53]: https://github.com/kiwicom/pytest-recording/issues/53
[#47]: https://github.com/kiwicom/pytest-recording/issues/47
[#45]: https://github.com/kiwicom/pytest-recording/issues/45
[#40]: https://github.com/kiwicom/pytest-recording/issues/40
[#37]: https://github.com/kiwicom/pytest-recording/issues/37
[#34]: https://github.com/kiwicom/pytest-recording/issues/34
[#20]: https://github.com/kiwicom/pytest-recording/issues/20
[#16]: https://github.com/kiwicom/pytest-recording/issues/16
[#10]: https://github.com/kiwicom/pytest-recording/issues/10
[#8]: https://github.com/kiwicom/pytest-recording/issues/8
[#7]: https://github.com/kiwicom/pytest-recording/issues/7
[#2]: https://github.com/kiwicom/pytest-recording/issues/2
