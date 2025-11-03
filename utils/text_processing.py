#!/usr/bin/env python3
"""
text_processing.py
Text processing utilities for cleaning and formatting output.
"""

import re


def strip_ansi_codes(text):
    """
    Remove ANSI color codes from text.
    
    Args:
        text: String containing ANSI codes
        
    Returns:
        String with ANSI codes removed
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def process_backspaces(output):
    """
    Process backspace characters to simulate terminal behavior.
    
    When MML systems send output like "MVOO\x08:", the backspace character (\x08)
    should delete the previous character, resulting in "MVO:".
    
    Args:
        output: String potentially containing backspace characters
        
    Returns:
        String with backspaces processed
    """
    result = []
    for char in output:
        if char == '\b' or char == '\x08':  # Backspace character
            if result:
                result.pop()  # Remove last character
        else:
            result.append(char)
    return ''.join(result)

