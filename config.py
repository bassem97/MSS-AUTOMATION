#!/usr/bin/env python3
"""
config.py
Configuration settings for the MSS automation tool.
"""

import os

# ---- Server Configuration ----
SERVERS = [
    {"name": "MSSTB4", "ip": "172.29.108.42", "user": "AUTOMA", "password": "AUTOMA-1"},
    {"name": "MSSTB5", "ip": "172.29.108.106", "user": "AUTOMA", "password": "AUTOMA-1"}
]

# ---- Timeout Settings ----
READ_TIMEOUT = 6.0  # Seconds to wait for command output
CONNECT_TIMEOUT = 10  # Seconds to wait for SSH connection
SHELL_TIMEOUT = 2.0  # Seconds for shell channel timeout

# ---- Logging Configuration ----
LOG_DIR = "logs"
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"
LOG_FORMAT_CONSOLE = "%(asctime)s %(levelname)s %(message)s"
LOG_FORMAT_FILE = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---- MML Command Configuration ----
MML_COMMANDS = {
    "CHECK_SUBSCRIBER": [
        "ZMVO:MSISDN={msisdn}::;"
    ]
}

# ---- Detection Patterns ----
SUBSCRIBER_NOT_FOUND_PATTERNS = ["UNKNOWN SUBSCRIBER", "DX ERROR", "COMMAND EXECUTION FAILED"]
SUBSCRIBER_FOUND_PATTERNS = ["SUBSCRIBER INFORMATION", "MOBILE COUNTRY CODE"]

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

