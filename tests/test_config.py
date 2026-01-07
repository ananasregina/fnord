"""
Tests for fnord configuration.

The fnords need a home. We test the configuration hierarchy.
"""

import pytest
import os
from pathlib import Path
from typing import Generator

from fnord.config import Config, get_config


class TestConfig:
    """Test the Config class."""

    def test_get_db_path_default(self, temp_config: Config, monkeypatch: pytest.MonkeyPatch):
        """Test getting default database path (current directory)."""
        # Clear any environment variable
        monkeypatch.delenv("FNORD_DB_PATH", raising=False)

        config = Config()
        path = config.get_db_path()

        # Should be in current directory (since no db exists yet)
        assert path.name == "fnord.db"
        # The actual parent depends on whether the db exists in current dir or ~/.config/fnord/
        # We just check it's the right filename

    def test_get_db_path_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test getting database path from environment variable."""
        test_path = "/tmp/test_fnord.db"
        monkeypatch.setenv("FNORD_DB_PATH", test_path)

        config = Config()
        path = config.get_db_path()

        assert str(path) == test_path

    def test_get_db_path_expands_tilde(self, monkeypatch: pytest.MonkeyPatch):
        """Test that ~ is expanded in database path."""
        test_path = "~/test_fnord.db"
        monkeypatch.setenv("FNORD_DB_PATH", test_path)

        config = Config()
        path = config.get_db_path()

        assert str(path) == os.path.expanduser(test_path)
        assert str(path).startswith(str(Path.home()))

    def test_get_config_dir(self, monkeypatch: pytest.MonkeyPatch):
        """Test getting config directory."""
        monkeypatch.delenv("FNORD_DB_PATH", raising=False)

        config = Config()
        config_dir = config.get_config_dir()

        # Should be ~/.config/fnord
        expected = Path.home() / ".config" / "fnord"
        assert config_dir == expected

    def test_get_mcp_server_name_default(self, monkeypatch: pytest.MonkeyPatch):
        """Test default MCP server name."""
        monkeypatch.delenv("FNORD_MCP_NAME", raising=False)

        config = Config()
        name = config.get_mcp_server_name()

        assert name == "fnord-tracker"

    def test_get_mcp_server_name_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test MCP server name from environment variable."""
        test_name = "my-fnord-server"
        monkeypatch.setenv("FNORD_MCP_NAME", test_name)

        config = Config()
        name = config.get_mcp_server_name()

        assert name == test_name

    def test_get_mcp_server_version_default(self, monkeypatch: pytest.MonkeyPatch):
        """Test default MCP server version."""
        monkeypatch.delenv("FNORD_MCP_VERSION", raising=False)

        config = Config()
        version = config.get_mcp_server_version()

        # 23.5.0 is the sacred version
        assert version == "23.5.0"

    def test_get_mcp_server_version_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test MCP server version from environment variable."""
        test_version = "23.0.0"
        monkeypatch.setenv("FNORD_MCP_VERSION", test_version)

        config = Config()
        version = config.get_mcp_server_version()

        assert version == test_version

    def test_get_log_level_default(self, monkeypatch: pytest.MonkeyPatch):
        """Test default log level."""
        monkeypatch.delenv("FNORD_LOG_LEVEL", raising=False)

        config = Config()
        level = config.get_log_level()

        assert level == "INFO"

    def test_get_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test log level from environment variable."""
        test_level = "DEBUG"
        monkeypatch.setenv("FNORD_LOG_LEVEL", test_level)

        config = Config()
        level = config.get_log_level()

        assert level == test_level

    def test_get_tui_theme_default(self, monkeypatch: pytest.MonkeyPatch):
        """Test default TUI theme."""
        monkeypatch.delenv("FNORD_THEME", raising=False)

        config = Config()
        theme = config.get_tui_theme()

        # fnords prefer dark themes
        assert theme == "dark"

    def test_get_tui_theme_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test TUI theme from environment variable."""
        test_theme = "light"
        monkeypatch.setenv("FNORD_THEME", test_theme)

        config = Config()
        theme = config.get_tui_theme()

        assert theme == test_theme

    def test_get_tui_page_size_default(self, monkeypatch: pytest.MonkeyPatch):
        """Test default TUI page size."""
        monkeypatch.delenv("FNORD_PAGE_SIZE", raising=False)

        config = Config()
        page_size = config.get_tui_page_size()

        # 23 is sacred
        assert page_size == 23

    def test_get_tui_page_size_from_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test TUI page size from environment variable."""
        test_size = "42"
        monkeypatch.setenv("FNORD_PAGE_SIZE", test_size)

        config = Config()
        page_size = config.get_tui_page_size()

        assert page_size == 42

    def test_get_tui_page_size_invalid_env(self, monkeypatch: pytest.MonkeyPatch):
        """Test TUI page size with invalid environment variable."""
        monkeypatch.setenv("FNORD_PAGE_SIZE", "not-a-number")

        config = Config()
        page_size = config.get_tui_page_size()

        # Should fall back to default
        assert page_size == 23


class TestConfigSingleton:
    """Test the config singleton pattern."""

    def test_get_config_singleton(self, monkeypatch: pytest.MonkeyPatch):
        """Test that get_config returns the same instance."""
        monkeypatch.delenv("FNORD_DB_PATH", raising=False)

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_singleton_with_different_env(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Test that singleton persists despite env changes."""
        # Reset the global config
        from fnord import config

        config._config = None

        # Get first config
        config1 = get_config()
        monkeypatch.setenv("FNORD_DB_PATH", "/tmp/test.db")

        # Get second config - should be the same instance
        config2 = get_config()

        assert config1 is config2

        # Reset for other tests
        config._config = None
