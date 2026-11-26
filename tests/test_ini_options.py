import pytest


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        pytest.param("pytest.ini", "[pytest]\nblock_network = true\n", id="pytest.ini"),
        pytest.param("tox.ini", "[pytest]\nblock_network = true\n", id="tox.ini"),
        pytest.param("setup.cfg", "[tool:pytest]\nblock_network = true\n", id="setup.cfg"),
        pytest.param("pyproject.toml", "[tool.pytest.ini_options]\nblock_network = true\n", id="pyproject.toml"),
    ],
)
def test_block_network_from_config_file(testdir, filename, content):
    testdir.tmpdir.join(filename).write(content)
    # Parametrized cases share a test name, so give each module its own name.
    module_name = "test_blocked_from_" + filename.replace(".", "_")
    testdir.makepyfile(
        **{
            module_name: """
        import pytest
        import requests

        def test_blocked(httpbin):
            with pytest.raises(RuntimeError, match=r"^Network is disabled for host '127.0.0.1'$"):
                requests.get(httpbin.url + "/ip")
        """
        }
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_cli_block_network_overrides_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nblock_network = false\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        def test_blocked(httpbin):
            with pytest.raises(RuntimeError, match=r"^Network is disabled for host '127.0.0.1'$"):
                requests.get(httpbin.url + "/ip")
        """
    )

    result = testdir.runpytest("--block-network")
    result.assert_outcomes(passed=1)


def test_allowed_hosts_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write(
        "[pytest]\nblock_network = true\nallowed_hosts =\n    127.0.0.*\n    127.0.1.1\n"
    )
    testdir.makepyfile(
        """
        import pytest
        import requests

        def test_allowed(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200

        def test_blocked():
            with pytest.raises(RuntimeError) as exc:
                requests.get("http://192.0.2.1")
            assert str(exc.value) == (
                "Network is disabled for host '192.0.2.1' (allowed hosts: '127.0.0.*', '127.0.1.1')"
            )
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_cli_allowed_hosts_overrides_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nblock_network = true\nallowed_hosts =\n    10.0.0.1\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        def test_allowed(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200

        def test_blocked():
            with pytest.raises(RuntimeError) as exc:
                requests.get("http://192.0.2.1")
            assert str(exc.value) == "Network is disabled for host '192.0.2.1' (allowed hosts: '127.0.0.1')"
        """
    )

    result = testdir.runpytest("--allowed-hosts=127.0.0.1")
    result.assert_outcomes(passed=2)


def test_vcr_config_allowed_hosts_overrides_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nblock_network = true\nallowed_hosts =\n    10.0.0.1\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.fixture(autouse=True)
        def vcr_config():
            return {"allowed_hosts": ["127.0.0.1"]}

        def test_allowed(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_allow_private_ips_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nblock_network = true\nallow_private_ips = true\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        def test_allowed(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200

        def test_blocked():
            with pytest.raises(RuntimeError) as exc:
                requests.get("http://8.8.8.8")
            assert str(exc.value) == "Network is disabled for host '8.8.8.8' (allowed hosts: private IPs)"
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_cli_allow_private_ips_overrides_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nblock_network = true\nallow_private_ips = false\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        def test_allowed(httpbin):
            assert requests.get(httpbin.url + "/ip").status_code == 200
        """
    )

    result = testdir.runpytest("--allow-private-ips")
    result.assert_outcomes(passed=1)


def test_record_mode_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nrecord_mode = once\n")
    testdir.makepyfile(
        """
        import pytest
        import requests

        @pytest.mark.vcr
        def test_record_mode(httpbin):
            assert requests.get(httpbin.url + "/get").status_code == 200
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_record_mode_ini/test_record_mode.yaml")
    assert cassette_path.size()


def test_cli_record_mode_overrides_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nrecord_mode = once\n")
    testdir.makepyfile(
        """
        import pytest
        import requests
        import vcr.errors

        @pytest.mark.vcr
        def test_no_recording(httpbin):
            with pytest.raises(vcr.errors.CannotOverwriteExistingCassetteException):
                requests.get(httpbin.url + "/get")
        """
    )

    result = testdir.runpytest("--record-mode=none")
    result.assert_outcomes(passed=1)
    cassette_path = testdir.tmpdir.join("cassettes/test_cli_record_mode_overrides_ini/test_no_recording.yaml")
    assert not cassette_path.exists()


def test_invalid_record_mode_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nrecord_mode = sometimes\n")
    testdir.makepyfile(
        """
        def test_():
            pass
        """
    )

    result = testdir.runpytest()
    assert result.ret == 4
    result.stderr.fnmatch_lines(["*Invalid record_mode 'sometimes'*"])


def test_ignore_localhost_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nignore_localhost = true\n")
    testdir.makepyfile(
        """
        import pytest

        def make_request(**kwargs):
            return type("Request", (), kwargs)

        @pytest.mark.vcr
        def test_ignored(vcr):
            assert vcr._before_record_request(make_request(host="127.0.0.1")) is None
            assert vcr._before_record_request(make_request(host="example.com")) is not None
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_vcr_config_overrides_ignore_localhost_ini(testdir):
    testdir.tmpdir.join("pytest.ini").write("[pytest]\nignore_localhost = true\n")
    testdir.makepyfile(
        """
        import pytest

        @pytest.fixture
        def vcr_config():
            return {"ignore_localhost": False}

        def make_request(**kwargs):
            return type("Request", (), kwargs)

        @pytest.mark.vcr
        def test_not_ignored(vcr):
            assert vcr._before_record_request(make_request(host="127.0.0.1")) is not None
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_pyproject_toml_options(testdir):
    testdir.tmpdir.join("pyproject.toml").write(
        "\n".join(
            [
                "[tool.pytest.ini_options]",
                'record_mode = "new_episodes"',
                "block_network = true",
                "allow_private_ips = true",
                "ignore_localhost = true",
                'allowed_hosts = ["127.0.0.1", "::1"]',
                "",
            ]
        )
    )
    testdir.makepyfile(
        """
        def test_values(record_mode, allowed_hosts, allow_private_ips, pytestconfig):
            assert record_mode == "new_episodes"
            assert allowed_hosts == ["127.0.0.1", "::1"]
            assert allow_private_ips is True
            assert pytestconfig.getini("block_network") is True
            assert pytestconfig.getini("ignore_localhost") is True
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
