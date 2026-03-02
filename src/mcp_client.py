"""
Lightweight MCP client scaffold.

The real MCP Python SDK (mcp[cli]) can be plugged in when available. This
manager keeps track of connection state and surfaces clear messaging so the UI
can reflect whether a server is reachable.
"""
from dataclasses import dataclass
import importlib.util


@dataclass
class MCPConnectionResult:
    """Result of an attempted MCP connection change."""

    connected: bool
    message: str


class MCPClientManager:
    """
    Minimal manager for MCP connectivity.

    When the official SDK is installed, this can be extended to hold the real
    client instance. For now it records intent and surfaces status text so the
    Settings UI can guide the user.
    """

    def __init__(self) -> None:
        self.server_url: str = ""
        self.connected: bool = False
        self.last_error: str = ""

    @staticmethod
    def _sdk_available() -> bool:
        """Return True if the official mcp package is importable."""
        return importlib.util.find_spec("mcp") is not None

    def connect(self, server_url: str) -> MCPConnectionResult:
        self.server_url = server_url.strip()
        if not self.server_url:
            self.connected = False
            self.last_error = "Server address is required."
            return MCPConnectionResult(False, self.last_error)

        if not self._sdk_available():
            self.connected = False
            self.last_error = "Install the official 'mcp[cli]' package to enable connections."
            return MCPConnectionResult(False, self.last_error)

        # Placeholder for a real client connection. The SDK is available, but
        # no actual connection logic has been implemented yet, so we do not
        # report a successful connection.
        self.connected = False
        self.last_error = "MCP SDK available, but connection is not implemented yet."
        return MCPConnectionResult(False, self.last_error)

    def disconnect(self) -> MCPConnectionResult:
        self.connected = False
        self.last_error = ""
        return MCPConnectionResult(False, "Disconnected from MCP server.")
