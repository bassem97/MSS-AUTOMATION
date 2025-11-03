#!/usr/bin/env python3
"""
logging_config.py
Logging configuration and custom formatters.
"""

import logging
import sys
import os

from utils.colors import Colors
from utils.text_processing import strip_ansi_codes
from config import LOG_DIR, LOG_FORMAT_CONSOLE, LOG_FORMAT_FILE, LOG_DATE_FORMAT


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels for console output."""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.BRIGHT_BLACK,
        logging.INFO: Colors.BRIGHT_CYAN,
        logging.WARNING: Colors.BRIGHT_YELLOW,
        logging.ERROR: Colors.BRIGHT_RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }

    def format(self, record):
        """Format log record with colors based on level."""
        # Save the original format
        original_format = self._style._fmt

        # Add color to the level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)

        # Color the entire log message based on level
        if record.levelno == logging.DEBUG:
            self._style._fmt = f'{Colors.BRIGHT_BLACK}%(asctime)s{Colors.RESET} [{level_color}%(levelname)s{Colors.RESET}] {Colors.BRIGHT_BLACK}%(message)s{Colors.RESET}'
        elif record.levelno == logging.INFO:
            self._style._fmt = f'{Colors.BRIGHT_WHITE}%(asctime)s{Colors.RESET} [{level_color}%(levelname)s{Colors.RESET}] %(message)s'
        elif record.levelno == logging.WARNING:
            self._style._fmt = f'{Colors.BRIGHT_WHITE}%(asctime)s{Colors.RESET} [{level_color}%(levelname)s{Colors.RESET}] {Colors.YELLOW}%(message)s{Colors.RESET}'
        elif record.levelno >= logging.ERROR:
            self._style._fmt = f'{Colors.BRIGHT_WHITE}%(asctime)s{Colors.RESET} [{level_color}%(levelname)s{Colors.RESET}] {Colors.RED}%(message)s{Colors.RESET}'

        result = logging.Formatter.format(self, record)

        # Restore the original format
        self._style._fmt = original_format

        return result


class PlainFormatter(logging.Formatter):
    """Custom formatter that strips ANSI color codes from log messages."""

    def format(self, record):
        """Format log record without colors."""
        result = logging.Formatter.format(self, record)
        return strip_ansi_codes(result)


def build_logger(server_ip=None):
    """
    Create a composite logger with console and optional file handlers.
    
    Args:
        server_ip: Optional IP address for file logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(server_ip or "msisdn-check")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with colors
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    colored_formatter = ColoredFormatter(LOG_FORMAT_CONSOLE, LOG_DATE_FORMAT)
    ch.setFormatter(colored_formatter)
    logger.addHandler(ch)

    # File handler - mode='w' to overwrite instead of append (no colors in file)
    if server_ip:
        fh = logging.FileHandler(os.path.join(LOG_DIR, f"{server_ip}.log"), mode="w")
        fh.setLevel(logging.DEBUG)
        plain_formatter = PlainFormatter(LOG_FORMAT_FILE, LOG_DATE_FORMAT)
        fh.setFormatter(plain_formatter)
        logger.addHandler(fh)

    return logger

