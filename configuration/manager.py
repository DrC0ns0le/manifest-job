import yaml
import os
from typing import Dict, Any


class ConfigManager:
    """
    Handles loading and managing configuration from YAML file and environment variables
    """

    def __init__(self, config_path="config.yaml", env_mapping=None):
        """
        Initialize the configuration manager

        Args:
            config_path: Path to the YAML configuration file
            env_mapping: Optional custom environment variable mapping.
                         If None, the default mapping from env_mapping.py will be used.
        """
        self.config_path = config_path

        # Import the default mapping if none is provided
        if env_mapping is None:
            from configuration.env_mapping import ENV_MAPPING

            self.env_mapping = ENV_MAPPING
        else:
            self.env_mapping = env_mapping

        self.config = self.load_config()

    def load_config(self):
        """
        Load configuration from YAML file or create default if not found.
        Then override with environment variables if provided.

        Returns:
            dict: Configuration parameters
        """
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)
            print(f"Configuration loaded from {self.config_path}")

            # Apply environment variable overrides
            self._apply_env_overrides(config)

            return config
        except FileNotFoundError:
            raise ValueError(f"Configuration file {self.config_path} not found")

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """
        Apply environment variable overrides to the configuration.

        Args:
            config: The configuration dictionary to update
        """
        for env_var, config_path in self.env_mapping.items():
            # Check if the environment variable is set
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Split the configuration path and set the value
                self._set_nested_config(config, config_path, env_value)
                print(f"Overriding configuration with environment variable: {env_var}")

    def _set_nested_config(self, config: Dict[str, Any], path: str, value: str) -> None:
        """
        Set a value in a nested dictionary based on a dot-notation path.
        Creates nested dictionaries if they don't exist.

        Args:
            config: The configuration dictionary to update
            path: The dot-notation path (e.g., 'push_notification.telegram.token')
            value: The value to set
        """
        keys = path.split(".")

        # Navigate to the last level of the nested dictionary
        current = config
        for key in keys[:-1]:  # All keys except the last one
            if key not in current or current[key] is None:
                current[key] = {}
            current = current[key]
            if not isinstance(current, dict):
                raise ValueError(
                    f"Cannot set nested key '{path}' because '{key}' is not a dictionary"
                )

        # Set the value at the last key
        current[keys[-1]] = self._convert_env_value(value)

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type

        Args:
            value: The string value from the environment variable

        Returns:
            The converted value
        """
        # Try to convert to boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        elif value.lower() in ("false", "no", "0"):
            return False

        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string if no other conversion applies
        return value
