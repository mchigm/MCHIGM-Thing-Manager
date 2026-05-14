from unittest.mock import MagicMock, patch

import src.updater as updater


def test_is_newer_version():
    assert updater.is_newer_version("1.0.0", "1.0.1") is True
    assert updater.is_newer_version("1.2.0", "1.2.0") is False
    assert updater.is_newer_version("1.2.9", "v1.3.0") is True


def test_check_for_updates_available_release():
    with patch.object(
        updater,
        "_fetch_json",
        return_value={
            "tag_name": "v1.1.0",
            "html_url": "https://example.com/release",
            "assets": [{"name": "app.pkg", "browser_download_url": "https://example.com/app.pkg"}],
        },
    ):
        result = updater.check_for_updates("1.0.0", "owner", "repo")
    assert result.success is True
    assert result.has_update is True
    assert result.latest_version == "v1.1.0"
    assert result.release_url == "https://example.com/release"
    assert result.download_url == "https://example.com/app.pkg"


def test_check_for_updates_no_update():
    with patch.object(
        updater,
        "_fetch_json",
        return_value={
            "tag_name": "v1.0.0",
            "html_url": "https://example.com/release",
            "assets": [],
        },
    ):
        result = updater.check_for_updates("1.0.0", "owner", "repo")
    assert result.success is True
    assert result.has_update is False


def test_check_for_updates_failure():
    with patch.object(updater, "_fetch_json", side_effect=RuntimeError("boom")):
        result = updater.check_for_updates("1.0.0", "owner", "repo")
    assert result.success is False
    assert result.has_update is False
    assert "boom" in result.message


def test_fetch_json_uses_certifi_ca_bundle():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"{}"
    response.__exit__.return_value = False

    with (
        patch.object(updater.certifi, "where", return_value="/bundle/cacert.pem"),
        patch.object(updater.ssl, "create_default_context", return_value="CTX") as create_context,
        patch.object(updater, "urlopen", return_value=response) as mock_urlopen,
    ):
        payload = updater._fetch_json("https://example.com/releases/latest")

    assert payload == {}
    create_context.assert_called_once_with(cafile="/bundle/cacert.pem")
    assert mock_urlopen.call_args.kwargs["context"] == "CTX"


def test_asset_download_url_prefers_linux_appimage():
    release = {
        "assets": [
            {"name": "thing-manager.tar.gz", "browser_download_url": "https://example.com/archive"},
            {"name": "thing-manager-x86_64.AppImage", "browser_download_url": "https://example.com/appimage"},
        ]
    }

    with patch.object(updater.platform, "system", return_value="Linux"):
        download_url = updater._asset_download_url(release)

    assert download_url == "https://example.com/appimage"
