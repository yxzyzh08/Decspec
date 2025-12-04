"""Logger Factory Module.

Provides unified logging capabilities with structured output for DevSpec CLI tool.
Implements feat_logging with a simple module-level design (no classes, no runtime adjustment).

Public APIs:
- get_logger(name): Get a named logger instance
- configure_logging(level, format, log_file): Configure global logging settings
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# === Constants ===

DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LEVEL = "INFO"
DEFAULT_FORMAT_TYPE = "rich"

# === Module-level state ===

_loggers: Dict[str, logging.Logger] = {}
_configured: bool = False


# === Public APIs ===


def configure_logging(
    level: str = "INFO", format: str = "rich", log_file: Optional[Path] = None
) -> None:
    """Configure global logging settings.

    Called once at CLI entry point (main.py). Configures the root logger,
    and all child loggers automatically inherit the configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format - 'rich' (console with colors) or 'plain' (simple)
        log_file: Optional file path for log output

    Example:
        >>> configure_logging(level='DEBUG', format='rich')
        >>> configure_logging(level='INFO', format='plain', log_file=Path('app.log'))
    """
    global _configured

    # Prevent duplicate configuration
    if _configured:
        return

    # Get root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers (avoid duplicates)
    root_logger.handlers.clear()

    # Validate and set level
    if level.upper() not in LOG_LEVELS:
        print(
            f"Warning: Invalid log level '{level}', using {DEFAULT_LEVEL}",
            file=sys.stderr,
        )
        level = DEFAULT_LEVEL

    root_logger.setLevel(level.upper())

    # Configure console handler based on format
    if format == "rich" and RICH_AVAILABLE:
        # Use Rich handler for beautiful console output
        console_handler = RichHandler(
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
        )
    else:
        # Fall back to plain StreamHandler
        if format == "rich" and not RICH_AVAILABLE:
            print(
                "Warning: Rich library not available, using plain format", file=sys.stderr
            )

        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(DEFAULT_FORMAT)
        console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        try:
            # Create log file directory if needed
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(
                log_file, mode="a", encoding="utf-8"
            )
            formatter = logging.Formatter(DEFAULT_FORMAT)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(
                f"Warning: Failed to create log file handler for {log_file}: {e}",
                file=sys.stderr,
            )

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get or create a named logger instance.

    Loggers are cached to avoid creating duplicates. Child loggers automatically
    inherit configuration from the root logger (configured by configure_logging()).

    Args:
        name: Logger name, typically module path (e.g., 'devspec.core.sync')

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger('devspec.commands.monitor')
        >>> logger.info('Monitoring started')
        >>> logger.debug('Debug details')
    """
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]

    # Create new logger (inherits from root logger)
    logger = logging.getLogger(name)

    # Cache it
    _loggers[name] = logger

    return logger
