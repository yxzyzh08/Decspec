"""Configuration Management Module.

Provides unified configuration management with layered overrides for DevSpec CLI tool.
Implements feat_config_management with a simple module-level design (no classes, no hot-reload).

Priority order (highest to lowest):
1. CLI parameters
2. System environment variables (DEVSPEC_* prefix)
3. .env file
4. YAML config file (.specgraph/config.yaml)
5. Default values

Public APIs:
- get_config(key, default): Get configuration value
- load_config(path): Load YAML config file
- load_env_file(path): Load .env file
- get_debug_mode(cli_flag): Get debug mode setting
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# === Constants ===

DEFAULT_CONFIG: Dict[str, Any] = {
    "database": {
        "path": ".specgraph/.runtime/specgraph.db",
    },
    "logging": {
        "level": "INFO",  # Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
        "format": "rich",
    },
    "spec": {
        "root": ".specgraph",
    },
    "debug": False,  # Default debug mode (boolean)
}

ENV_PREFIX = "DEVSPEC_"
CONFIG_FILE_NAME = "config.yaml"
ENV_FILE_NAME = ".env"
DEBUG_ENV_KEYS = ["DEBUG", "DEVSPEC_DEBUG"]
DEBUG_TRUE_VALUES = ["true", "1", "yes"]
DEBUG_FALSE_VALUES = ["false", "0", "no"]

# === Module-level state (lazy initialization) ===

_config: Optional[Dict[str, Any]] = None


# === Public APIs ===


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value by key with optional default.

    Args:
        key: Config key, supports dot notation (e.g., 'database.path')
        default: Default value if key not found

    Returns:
        Config value or default

    Example:
        >>> get_config('database.path')
        '.specgraph/.runtime/specgraph.db'
        >>> get_config('unknown.key', 'fallback')
        'fallback'
    """
    global _config
    if _config is None:
        _config = _init_config()

    # Navigate nested dict using dot notation
    keys = key.split(".")
    value = _config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value


def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to config file

    Returns:
        Loaded configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML syntax is invalid
    """
    content = path.read_text(encoding="utf-8")
    return yaml.safe_load(content) or {}


def load_env_file(path: Path = Path(".env")) -> None:
    """Load environment variables from .env file.

    Parses .env file manually (no python-dotenv dependency) and updates os.environ.
    Supports:
    - Comments (lines starting with #)
    - Empty lines
    - KEY=VALUE format
    - Quoted values: "value", 'value'
    - Escape sequences: \\n, \\t, \\\\, \\"

    Args:
        path: Path to .env file (default: project root .env)

    Example .env file:
        # Configuration
        DEBUG=true
        DEVSPEC_DATABASE_PATH="/custom/path"
    """
    if not path.exists():
        return

    try:
        content = path.read_text(encoding="utf-8")
        for line_num, line in enumerate(content.splitlines(), start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
            if not match:
                # Log warning for malformed lines (but continue)
                print(f"Warning: Malformed .env line {line_num}: {line}", file=os.sys.stderr)
                continue

            key, value = match.groups()

            # Handle quoted values
            value = value.strip()
            if value and value[0] in ('"', "'"):
                quote = value[0]
                if len(value) > 1 and value[-1] == quote:
                    value = value[1:-1]
                    # Process escape sequences
                    value = value.replace("\\n", "\n")
                    value = value.replace("\\t", "\t")
                    value = value.replace("\\\\", "\\")
                    value = value.replace(f"\\{quote}", quote)

            os.environ[key] = value

    except Exception as e:
        print(f"Warning: Failed to load .env file {path}: {e}", file=os.sys.stderr)


def get_debug_mode(cli_flag: Optional[bool] = None) -> bool:
    """Get debug mode setting with priority: CLI > env > default.

    Args:
        cli_flag: CLI --debug flag value (None if not provided)

    Returns:
        True if debug mode enabled

    Priority order:
    1. CLI flag (if provided)
    2. Environment variable DEBUG or DEVSPEC_DEBUG
    3. Default (False)
    """
    # Priority 1: CLI flag
    if cli_flag is not None:
        return cli_flag

    # Priority 2: Environment variables
    for env_key in DEBUG_ENV_KEYS:
        env_value = os.environ.get(env_key)
        if env_value:
            normalized = env_value.lower()
            if normalized in DEBUG_TRUE_VALUES:
                return True
            if normalized in DEBUG_FALSE_VALUES:
                return False

    # Priority 3: Default
    return False


# === Internal helper functions ===


def _init_config() -> Dict[str, Any]:
    """Initialize and return merged config dictionary.

    Loads configuration in priority order:
    1. Default values
    2. YAML config file (.specgraph/config.yaml)
    3. .env file
    4. System environment variables (DEVSPEC_*)

    Returns:
        Merged configuration dictionary
    """
    # Step 1: Start with default config
    import copy

    config = copy.deepcopy(DEFAULT_CONFIG)

    # Step 2: Load YAML config file (if exists)
    config_path = Path(".specgraph") / CONFIG_FILE_NAME
    if config_path.exists():
        try:
            yaml_config = load_config(config_path)
            config = _deep_merge(config, yaml_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {config_path}: {e}", file=os.sys.stderr)

    # Step 3: Load .env file (if exists)
    # Note: .env content updates os.environ, processed in step 4
    env_path = Path(ENV_FILE_NAME)
    load_env_file(env_path)

    # Step 4: Apply system environment variable overrides (including from .env)
    _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """Apply system environment variable overrides to config.

    Processes all DEVSPEC_* environment variables and converts them to config keys.
    Example: DEVSPEC_DATABASE_PATH -> database.path

    Args:
        config: Configuration dictionary to modify in-place
    """
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            # Remove prefix and convert to lowercase dot notation
            config_key = key[len(ENV_PREFIX) :].lower().replace("_", ".")
            _set_nested(config, config_key, value)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)

    Returns:
        Merged dictionary (new dict, doesn't modify inputs)
    """
    import copy

    result = copy.deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _set_nested(config: Dict[str, Any], key: str, value: Any) -> None:
    """Set a value in nested dict using dot notation.

    Args:
        config: Configuration dictionary to modify in-place
        key: Dot-notation key (e.g., 'database.path')
        value: Value to set
    """
    keys = key.split(".")
    current = config

    # Navigate to the parent dict
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            # Overwrite non-dict with dict to allow nested setting
            current[k] = {}
        current = current[k]

    # Set the final value
    current[keys[-1]] = value
