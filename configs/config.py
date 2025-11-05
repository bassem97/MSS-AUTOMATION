#!/usr/bin/env python3
"""
config.py
Configuration settings for the MSS automation tool.
"""

import os
import yaml
import sys

# Get the directory where this config file is located
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- Load Server Configuration from YAML ----
def load_servers():
    """Load server configuration from SERVERS.yaml"""
    servers_file = os.path.join(CONFIG_DIR, 'SERVERS.yaml')
    try:
        with open(servers_file, 'r') as f:
            data = yaml.safe_load(f)
            servers = data.get('SERVERS', {})
            if not servers:
                raise ValueError("No servers found in SERVERS.yaml")
            # Add the server key as 'name' field for backward compatibility
            servers_list = []
            for server_key, server_data in servers.items():
                server_data['name'] = server_key
                servers_list.append(server_data)
            return servers_list
    except FileNotFoundError:
        print(f"ERROR: {servers_file} not found!")
        print("Please create configs/SERVERS.yaml with your server configuration.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading SERVERS.yaml: {e}")
        sys.exit(1)

# ---- Load Phone Configuration from YAML ----
def load_phones():
    """Load phone configuration from PHONES.yaml"""
    phones_file = os.path.join(CONFIG_DIR, 'PHONES.yaml')
    try:
        with open(phones_file, 'r') as f:
            data = yaml.safe_load(f)
            phones = data.get('PHONES', {})
            if not phones:
                raise ValueError("No phones found in PHONES.yaml")
            return phones
    except FileNotFoundError:
        print(f"ERROR: {phones_file} not found!")
        print("Please create configs/PHONES.yaml with your phone configuration.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading PHONES.yaml: {e}")
        sys.exit(1)

# Load configurations
SERVERS = load_servers()
PHONES = load_phones()

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
