"""
Fnord Configuration Module

The fnords live in many places. This module helps find them.

Configuration priority (most important first):
1. FNORD_DB_PATH environment variable
2. FNORD_DB_PATH in .env file
3. ./fnord.db (current directory)
4. ~/.config/fnord/fnord.db (the fnord sanctuary)
"""

import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration for the fnord tracker.

    The fnords need a home. This finds the best one.
    """

    def __init__(self) -> None:
        """Initialize configuration from environment and .env files."""
        # Load .env from current directory first
        load_dotenv()

        # Also try loading from ~/.config/fnord/.env
        config_dir = self._get_config_dir()
        config_env = config_dir / ".env"
        if config_env.exists():
            load_dotenv(config_env)

        logger.debug("Configuration loaded. The fnords are pleased.")

    def get_db_path(self) -> Path:
        """
        Get the fnord database path.

        Follows the sacred configuration hierarchy:
        1. FNORD_DB_PATH environment variable (highest priority)
        2. ./fnord.db in current directory
        3. ~/.config/fnord/fnord.db (the fnord sanctuary)

        Returns:
            Path: The path to the fnord database
        """
        # Priority 1: Environment variable
        if env_path := os.getenv("FNORD_DB_PATH"):
            path = Path(env_path).expanduser().absolute()
            logger.debug(f"Using database from FNORD_DB_PATH: {path}")
            return path

        # Priority 2: Current directory
        current_dir = Path.cwd()
        local_db = current_dir / "fnord.db"
        if local_db.exists():
            logger.debug(f"Using local database: {local_db}")
            return local_db

        # Priority 3: Config directory (the fnord sanctuary)
        config_dir = self._get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        config_db = config_dir / "fnord.db"

        logger.debug(f"Using config directory database: {config_db}")
        return config_db

    def get_config_dir(self) -> Path:
        """
        Get the fnord configuration directory.

        Returns:
            Path: The configuration directory path
        """
        return self._get_config_dir()

    @staticmethod
    def _get_config_dir() -> Path:
        """
        Get the config directory for fnord.

        Uses ~/.config/fnord on Unix-like systems.

        Returns:
            Path: The config directory path
        """
        # Cross-platform config directory
        config_base = Path.home() / ".config"
        fnord_config = config_base / "fnord"

        return fnord_config

    def get_mcp_server_name(self) -> str:
        """
        Get the MCP server name.

        Returns:
            str: MCP server name
        """
        return os.getenv("FNORD_MCP_NAME", "fnord-tracker")

    def get_mcp_server_version(self) -> str:
        """
        Get the MCP server version.

        Returns:
            str: MCP server version (23.5.0 is sacred)
        """
        return os.getenv("FNORD_MCP_VERSION", "23.5.0")

    def get_web_port(self) -> int:
        """
        Get the web server port.

        The fnords need a door to the outside world.

        Returns:
            int: Web server port number
        """
        return int(os.getenv("FNORD_WEB_PORT", "8000"))

    def get_log_level(self) -> str:
        """
        Get the log level.

        Returns:
            str: Log level (default: INFO)
        """
        return os.getenv("FNORD_LOG_LEVEL", "INFO")

    def get_tui_theme(self) -> str:
        """
        Get the TUI theme.

        Returns:
            str: Theme name (dark/light/auto)
        """
        return os.getenv("FNORD_THEME", "dark")

    def get_tui_page_size(self) -> int:
        """
        Get the TUI page size (number of fnords per page).

        23 is sacred, but user can override.

        Returns:
            int: Number of fnords per page
        """
        try:
            return int(os.getenv("FNORD_PAGE_SIZE", "23"))
        except ValueError:
            return 23


# Singleton instance for the whole application
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config: The configuration singleton
    """
    global _config
    if _config is None:
        _config = Config()
        logger.debug("Global configuration initialized. Hail Discordia!")
    return _config
