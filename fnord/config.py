"""
Fnord Configuration Module

The fnords live in many places. This module helps find them.

Configuration priority:
- PostgreSQL: FNORD_DB_HOST, FNORD_DB_PORT, FNORD_DB_NAME, FNORD_DB_USER, FNORD_DB_PASSWORD
- LM Studio: EMBEDDING_URL, EMBEDDING_MODEL, EMBEDDING_DIMENSION
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

    def get_postgres_uri(self) -> str:
        """
        Get PostgreSQL connection URI.

        Returns:
            str: PostgreSQL connection URI
        """
        host = os.getenv("FNORD_DB_HOST", "localhost")
        port = os.getenv("FNORD_DB_PORT", "5432")
        dbname = os.getenv("FNORD_DB_NAME", "fnord")
        user = os.getenv("FNORD_DB_USER", "fnord_user")
        password = os.getenv("FNORD_DB_PASSWORD", "")

        uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        logger.debug(f"PostgreSQL URI: {uri}")
        return uri

    def get_embedding_config(self) -> dict[str, str | int]:
        """
        Get LM Studio embedding configuration.

        Returns:
            dict: Embedding config with url, model, and dimension
        """
        return {
            "url": os.getenv("EMBEDDING_URL", "http://127.0.0.1:1338/v1"),
            "model": os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5-embedding"),
            "dimension": int(os.getenv("EMBEDDING_DIMENSION", "768")),
        }

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
