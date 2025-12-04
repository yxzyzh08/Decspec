"""CLI Debug Logger Module.

Provides CLI command execution logging with input/output capture for debug mode.
Implements feat_logging with a simple decorator design (no classes needed).

Public API:
- debug_command: Decorator for CLI commands to add debug logging

Usage:
    from devspec.infra.cli_debug_logger import debug_command

    @app.command()
    @debug_command  # No arguments needed!
    def monitor():
        ...
"""

import functools
import logging
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from devspec.infra.config import get_debug_mode

# === Constants ===

DEFAULT_LOG_FILE = Path("logs/devspec_cli_debug.log")
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_RESULT_LENGTH = 500  # Maximum characters for result output in log

# === Module-level state ===

_debug_logger: Optional[logging.Logger] = None


# === Internal helper functions ===


def _get_debug_logger() -> logging.Logger:
    """Get or initialize debug logger instance (lazy initialization).

    Returns:
        Configured debug logger that writes to DEFAULT_LOG_FILE
    """
    global _debug_logger

    if _debug_logger is not None:
        return _debug_logger

    # Create logs directory
    DEFAULT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create file handler
    try:
        file_handler = logging.FileHandler(
            DEFAULT_LOG_FILE, mode="a", encoding="utf-8"
        )
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter)

        # Create logger
        logger = logging.getLogger("devspec.cli.debug")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.propagate = False  # Don't propagate to root logger

        _debug_logger = logger
        return logger

    except Exception as e:
        # If logger creation fails, print warning and return a dummy logger
        print(f"Warning: Failed to create debug logger: {e}")
        dummy_logger = logging.getLogger("devspec.cli.debug.dummy")
        dummy_logger.addHandler(logging.NullHandler())
        _debug_logger = dummy_logger
        return dummy_logger


def _log_command_start(
    command_name: str, args: Dict[str, Any], options: Dict[str, Any]
) -> str:
    """Record command execution start.

    Args:
        command_name: Command name (e.g., 'monitor', 'sync')
        args: Positional arguments as dict
        options: Keyword arguments as dict

    Returns:
        Execution ID (timestamp-based)
    """
    execution_id = datetime.now().isoformat()
    logger = _get_debug_logger()

    # Format log message
    message = f"""
{'=' * 80}
COMMAND: {command_name}
├─ EXECUTION_ID: {execution_id}
├─ ARGS: {args}
├─ OPTIONS: {options}
└─ START: {datetime.now().strftime(DATE_FORMAT)}
"""
    logger.info(message)

    return execution_id


def _log_command_end(
    execution_id: str, result: Any, duration: float, success: bool = True
) -> None:
    """Record command execution end.

    Args:
        execution_id: Execution ID from _log_command_start
        result: Command return result (will be truncated to MAX_RESULT_LENGTH)
        duration: Execution duration in seconds
        success: Whether execution succeeded
    """
    logger = _get_debug_logger()

    # Convert result to string and truncate if needed
    result_str = str(result)
    if len(result_str) > MAX_RESULT_LENGTH:
        result_str = result_str[:MAX_RESULT_LENGTH] + "... (truncated)"

    # Format log message
    status = "SUCCESS" if success else "FAILED"
    message = f"""
RESULT: {execution_id}
├─ STATUS: {status}
├─ DURATION: {duration:.4f}s
├─ END: {datetime.now().strftime(DATE_FORMAT)}
└─ OUTPUT:
{result_str}
{'=' * 80}
"""

    if success:
        logger.info(message)
    else:
        logger.error(message)


# === Public API ===


def debug_command(func: Callable) -> Callable:
    """Decorator to add debug logging to CLI commands.

    Automatically checks if debug mode is enabled. If disabled, this is a no-op
    decorator with zero overhead. If enabled, logs command execution details to
    logs/devspec_cli_debug.log.

    Args:
        func: The CLI command function to decorate

    Returns:
        Wrapped function with debug logging

    Example:
        @app.command()
        @debug_command
        def monitor():
            # Your command logic
            return "Monitoring completed"
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if debug mode is enabled
        if not get_debug_mode():
            # Debug mode off - execute directly (zero overhead)
            return func(*args, **kwargs)

        # Debug mode on - log execution
        command_name = func.__name__

        # Convert args/kwargs to dict for logging
        args_dict = {f"arg{i}": arg for i, arg in enumerate(args)}
        options_dict = kwargs.copy()

        # Log command start
        execution_id = _log_command_start(command_name, args_dict, options_dict)
        start_time = time.time()

        try:
            # Execute command
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Log success
            _log_command_end(execution_id, result, duration, success=True)

            return result

        except Exception as e:
            # Log failure
            duration = time.time() - start_time
            error_details = f"{type(e).__name__}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            _log_command_end(execution_id, error_details, duration, success=False)

            # Re-raise the exception
            raise

    return wrapper
