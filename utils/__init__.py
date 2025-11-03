#!/usr/bin/env python3
"""
utils package
Utility functions and helpers.
"""

from .colors import Colors
from .text_processing import strip_ansi_codes, process_backspaces

__all__ = ['Colors', 'strip_ansi_codes', 'process_backspaces']

