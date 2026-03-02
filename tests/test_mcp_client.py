"""
Unit tests for src/mcp_client.py
"""
import pytest
from unittest.mock import patch

from src.mcp_client import MCPClientManager, MCPConnectionResult


class TestMCPConnectionResult:
    def test_dataclass_fields(self):
        r = MCPConnectionResult(connected=True, message="OK")
        assert r.connected is True
        assert r.message == "OK"


class TestMCPClientManagerInit:
    def test_initial_state(self):
        mgr = MCPClientManager()
        assert mgr.server_url == ""
        assert mgr.connected is False
        assert mgr.last_error == ""


class TestMCPClientManagerConnect:
    def test_connect_empty_url_fails(self):
        mgr = MCPClientManager()
        result = mgr.connect("")
        assert result.connected is False
        assert "required" in result.message.lower()
        assert mgr.connected is False

    def test_connect_whitespace_url_fails(self):
        mgr = MCPClientManager()
        result = mgr.connect("   ")
        assert result.connected is False

    def test_connect_without_sdk_fails(self):
        mgr = MCPClientManager()
        with patch.object(MCPClientManager, "_sdk_available", return_value=False):
            result = mgr.connect("http://localhost:8080")
        assert result.connected is False
        assert "mcp" in result.message.lower() or "install" in result.message.lower()

    def test_connect_with_sdk_returns_not_implemented(self):
        """SDK present but connection is not yet implemented."""
        mgr = MCPClientManager()
        with patch.object(MCPClientManager, "_sdk_available", return_value=True):
            result = mgr.connect("http://localhost:8080")
        assert result.connected is False
        assert mgr.connected is False

    def test_connect_stores_url(self):
        mgr = MCPClientManager()
        with patch.object(MCPClientManager, "_sdk_available", return_value=False):
            mgr.connect("http://mcp.example.com")
        assert mgr.server_url == "http://mcp.example.com"

    def test_connect_strips_whitespace_from_url(self):
        mgr = MCPClientManager()
        with patch.object(MCPClientManager, "_sdk_available", return_value=False):
            mgr.connect("  http://host  ")
        assert mgr.server_url == "http://host"


class TestMCPClientManagerDisconnect:
    def test_disconnect_clears_state(self):
        mgr = MCPClientManager()
        mgr.connected = True
        mgr.server_url = "http://host"
        result = mgr.disconnect()
        assert mgr.connected is False

    def test_disconnect_returns_result(self):
        mgr = MCPClientManager()
        result = mgr.disconnect()
        assert isinstance(result, MCPConnectionResult)
        assert result.connected is False

    def test_disconnect_message_mentions_disconnected(self):
        mgr = MCPClientManager()
        result = mgr.disconnect()
        assert "disconnect" in result.message.lower()


class TestSDKAvailable:
    def test_sdk_available_when_mcp_importable(self):
        import importlib.util
        spec = importlib.util.find_spec("mcp")
        expected = spec is not None
        assert MCPClientManager._sdk_available() == expected
