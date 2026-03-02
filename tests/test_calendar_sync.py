"""
Unit tests for src/calendar_sync.py
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.calendar_sync import CalendarProvider, CalendarSyncManager, CalendarSyncResult


class TestCalendarSyncResult:
    def test_defaults(self):
        r = CalendarSyncResult(success=True, message="ok")
        assert r.synced_count == 0
        assert r.error_count == 0


class TestCalendarSyncManagerInit:
    def test_initial_state(self):
        mgr = CalendarSyncManager()
        assert mgr.provider == CalendarProvider.NONE
        assert mgr.connected is False
        assert mgr.last_sync is None
        assert mgr.last_error == ""


# ---------------------------------------------------------------------------
# SDK detection
# ---------------------------------------------------------------------------
class TestSDKDetection:
    def test_google_sdk_returns_bool(self):
        result = CalendarSyncManager.is_google_sdk_available()
        assert isinstance(result, bool)

    def test_outlook_sdk_returns_bool(self):
        result = CalendarSyncManager.is_outlook_sdk_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# connect_google
# ---------------------------------------------------------------------------
class TestConnectGoogle:
    def test_no_sdk_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_google_sdk_available", return_value=False):
            result = mgr.connect_google("/path/to/creds.json")
        assert result.success is False
        assert "google" in result.message.lower() or "install" in result.message.lower()

    def test_empty_credentials_path_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_google_sdk_available", return_value=True):
            result = mgr.connect_google("")
        assert result.success is False
        assert "credentials" in result.message.lower() or "path" in result.message.lower()

    def test_sdk_available_but_not_implemented(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_google_sdk_available", return_value=True):
            result = mgr.connect_google("/path/creds.json")
        assert result.success is False
        # provider should be set to GOOGLE even though not connected
        assert mgr.provider == CalendarProvider.GOOGLE
        assert mgr.connected is False


# ---------------------------------------------------------------------------
# connect_outlook
# ---------------------------------------------------------------------------
class TestConnectOutlook:
    def test_no_sdk_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_outlook_sdk_available", return_value=False):
            result = mgr.connect_outlook("cid", "csecret", "tid")
        assert result.success is False
        assert "install" in result.message.lower() or "msal" in result.message.lower()

    def test_missing_client_id_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_outlook_sdk_available", return_value=True):
            result = mgr.connect_outlook("", "secret", "tenant")
        assert result.success is False

    def test_missing_secret_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_outlook_sdk_available", return_value=True):
            result = mgr.connect_outlook("cid", "", "tenant")
        assert result.success is False

    def test_missing_tenant_returns_failure(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_outlook_sdk_available", return_value=True):
            result = mgr.connect_outlook("cid", "secret", "")
        assert result.success is False

    def test_sdk_available_but_not_implemented(self):
        mgr = CalendarSyncManager()
        with patch.object(CalendarSyncManager, "is_outlook_sdk_available", return_value=True):
            result = mgr.connect_outlook("cid", "secret", "tid")
        assert result.success is False


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------
class TestDisconnect:
    def test_disconnect_resets_state(self):
        mgr = CalendarSyncManager()
        mgr.provider = CalendarProvider.GOOGLE
        mgr.connected = True
        result = mgr.disconnect()
        assert result.success is True
        assert mgr.connected is False
        assert mgr.provider == CalendarProvider.NONE

    def test_disconnect_clears_clients(self):
        mgr = CalendarSyncManager()
        mgr._google_client = object()
        mgr._outlook_client = object()
        mgr.disconnect()
        assert mgr._google_client is None
        assert mgr._outlook_client is None

    def test_disconnect_message_mentions_provider(self):
        mgr = CalendarSyncManager()
        mgr.provider = CalendarProvider.GOOGLE
        result = mgr.disconnect()
        assert "google" in result.message.lower()


# ---------------------------------------------------------------------------
# sync_to_cloud / sync_from_cloud when not connected
# ---------------------------------------------------------------------------
class TestSyncNotConnected:
    def test_sync_to_cloud_not_connected(self):
        mgr = CalendarSyncManager()
        result = mgr.sync_to_cloud([])
        assert result.success is False
        assert "not connected" in result.message.lower()

    def test_sync_from_cloud_not_connected(self):
        mgr = CalendarSyncManager()
        result = mgr.sync_from_cloud()
        assert result.success is False
        assert "not connected" in result.message.lower()


# ---------------------------------------------------------------------------
# Internal scaffold sync methods (connected state forced)
# ---------------------------------------------------------------------------
class TestInternalSyncScaffold:
    def _connected_google(self) -> CalendarSyncManager:
        mgr = CalendarSyncManager()
        mgr.provider = CalendarProvider.GOOGLE
        mgr.connected = True
        return mgr

    def _connected_outlook(self) -> CalendarSyncManager:
        mgr = CalendarSyncManager()
        mgr.provider = CalendarProvider.OUTLOOK
        mgr.connected = True
        return mgr

    def test_sync_to_google_scaffold(self):
        mgr = self._connected_google()
        items = [object(), object()]
        result = mgr._sync_to_google(items)
        assert result.success is True
        assert result.synced_count == len(items)
        assert mgr.last_sync is not None

    def test_sync_to_outlook_scaffold(self):
        mgr = self._connected_outlook()
        items = [object()]
        result = mgr._sync_to_outlook(items)
        assert result.success is True
        assert result.synced_count == len(items)

    def test_sync_from_google_scaffold(self):
        mgr = self._connected_google()
        result = mgr._sync_from_google()
        assert result.success is True
        assert mgr.last_sync is not None

    def test_sync_from_outlook_scaffold(self):
        mgr = self._connected_outlook()
        result = mgr._sync_from_outlook()
        assert result.success is True

    def test_sync_to_cloud_dispatches_google(self):
        mgr = self._connected_google()
        result = mgr.sync_to_cloud([])
        assert result.success is True

    def test_sync_from_cloud_dispatches_google(self):
        mgr = self._connected_google()
        result = mgr.sync_from_cloud()
        assert result.success is True


# ---------------------------------------------------------------------------
# get_status_text
# ---------------------------------------------------------------------------
class TestGetStatusText:
    def test_not_connected(self):
        mgr = CalendarSyncManager()
        assert mgr.get_status_text() == "Not connected"

    def test_connected_without_last_sync(self):
        mgr = CalendarSyncManager()
        mgr.connected = True
        mgr.provider = CalendarProvider.GOOGLE
        status = mgr.get_status_text()
        assert "google" in status.lower()

    def test_connected_with_last_sync(self):
        mgr = CalendarSyncManager()
        mgr.connected = True
        mgr.provider = CalendarProvider.OUTLOOK
        mgr.last_sync = datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)
        status = mgr.get_status_text()
        assert "2024-06-15" in status
