# server/lib/config.py
import copy
import logging
from pathlib import Path
import tomllib
from typing import Any, cast

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_USER_CONFIG_DIR_NAME = ".wiffzack_additions"
DEFAULT_CONFIG_FILENAME = "config.toml"


class ConfigLoader:
    """
    Handles loading and merging of base and user-specific TOML configuration files.
    """

    def __init__(
        self,
        base_config_dir: Path | None = None,
        user_config_dir_name: str = DEFAULT_USER_CONFIG_DIR_NAME,
        config_filename: str = DEFAULT_CONFIG_FILENAME,
    ) -> None:
        """
        Initializes the ConfigLoader and loads the configuration.

        Args:
            base_config_dir: Directory of the base config. Defaults to the
                             parent directory of this file's location.
            user_config_dir_name: Name of the directory within the user's home
                                  directory for user-specific config.
            config_filename: The name of the configuration file (e.g., "config.toml").
        """
        # Determine base path (assuming this file is in server/lib)
        if base_config_dir is None:
            self.base_config_dir: Path = Path(__file__).resolve().parent.parent
        else:
            self.base_config_dir: Path = base_config_dir

        self.user_config_dir: Path = Path.home() / user_config_dir_name
        self.config_filename: str = config_filename

        self.base_config_path: Path = self.base_config_dir / self.config_filename
        self.user_config_path: Path = self.user_config_dir / self.config_filename

        self._config: dict[str, Any] = self._load_and_merge_configs()

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merges the override dictionary into the base dictionary."""
        merged = copy.deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and key in merged and isinstance(merged.get(key), dict):
                merged[key] = self._merge_configs(
                    merged[key], cast(dict[str, Any], value))
            else:
                merged[key] = value
        return merged

    def _load_and_merge_configs(self) -> dict[str, Any]:
        """Loads the base config and merges the user config if it exists."""
        # Load base configuration
        base_config: dict[str, Any] = {}
        try:
            with open(self.base_config_path, "rb") as f:
                base_config = tomllib.load(f)
            logger.info(
                f"Loaded base configuration from: {self.base_config_path}")
        except FileNotFoundError:
            logger.critical(
                f"Base configuration file not found at {self.base_config_path}. Exiting.")
            exit(1)
        except tomllib.TOMLDecodeError as e:
            logger.critical(
                f"Error decoding base configuration file {self.base_config_path}: {e}. Exiting.")
            exit(1)
        except Exception as e:
            logger.critical(
                f"Error reading base configuration file {self.base_config_path}: {e}. Exiting.")
            exit(1)

        # Load and merge user configuration if it exists
        if self.user_config_path.exists() and self.user_config_path.is_file():
            try:
                with open(self.user_config_path, "rb") as f:
                    user_config: dict[str, Any] = tomllib.load(f)
                merged_config: dict[str, Any] = self._merge_configs(
                    base_config, user_config)
                logger.info(
                    f"Loaded and merged user configuration from: {self.user_config_path}")
                return merged_config
            except tomllib.TOMLDecodeError as e:
                logger.warning(
                    f"Could not parse user configuration file at {self.user_config_path}: {e}. Using base configuration only.")
            except Exception as e:
                logger.warning(
                    f"Could not read user configuration file at {self.user_config_path}: {e}. Using base configuration only.")

        logger.info(
            f"User configuration file not found or unreadable at {self.user_config_path}. Using base configuration only.")
        return base_config  # Return only base config if user config fails or doesn't exist

    @property
    def config(self) -> dict[str, Any]:
        """Returns the fully loaded and merged configuration dictionary."""
        # Ensures that consumers always get the final, merged config object
        return self._config
