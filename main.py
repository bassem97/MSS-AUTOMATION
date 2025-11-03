#!/usr/bin/env python3
"""
main.py
SSH automation to check if a MSISDN exists on given servers by running interactive commands.
All output from each command is written into per-server logs for traceability.
"""

import paramiko
import time
import logging
import argparse
import sys
import os
import socket
import re
from datetime import datetime

# ---- ANSI Color Codes ----
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

def strip_ansi_codes(text):
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.BRIGHT_BLACK,
        logging.INFO: Colors.BRIGHT_CYAN,
        logging.WARNING: Colors.BRIGHT_YELLOW,
        logging.ERROR: Colors.BRIGHT_RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }

    def format(self, record):
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
    """Custom formatter that strips ANSI color codes from log messages"""

    def format(self, record):
        result = logging.Formatter.format(self, record)
        return strip_ansi_codes(result)

# ---- Configuration ----
SERVERS = [
    {"name": "MSSTB4", "ip": "172.29.108.42",  "user": "AUTOMA", "password": "AUTOMA-1"},
    {"name": "MSSTB5", "ip": "172.29.108.106", "user": "AUTOMA", "password": "AUTOMA-1"},
]

READ_TIMEOUT = 6.0
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ---- Logging ----
def build_logger(server_ip=None):
    """Create a composite logger (console + optional file)."""
    logger = logging.getLogger(server_ip or "msisdn-check")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with colors
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    colored_formatter = ColoredFormatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(colored_formatter)
    logger.addHandler(ch)

    # File handler - mode='w' to overwrite instead of append (no colors in file)
    if server_ip:
        fh = logging.FileHandler(os.path.join(LOG_DIR, f"{server_ip}.log"), mode="w")
        fh.setLevel(logging.DEBUG)
        plain_formatter = PlainFormatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        fh.setFormatter(plain_formatter)
        logger.addHandler(fh)

    return logger


def stream_channel_output(chan, timeout=READ_TIMEOUT):
    """Continuously read shell output until timeout expires."""
    output = []
    start = time.time()
    while True:
        if chan.recv_ready():
            try:
                data = chan.recv(4096).decode('utf-8', errors='ignore')
            except socket.timeout:
                break
            if not data:
                break
            output.append(data)
            start = time.time()
        else:
            time.sleep(0.1)
        if time.time() - start > timeout:
            break
    return "".join(output)


def connect_and_check(server, msisdn):
    """Connects via SSH, executes commands, returns (found, output_text)."""
    logger = build_logger(server["ip"])
    logger.info("Connecting to %s (%s)...", server.get("name", ""), server["ip"])

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            server["ip"],
            username=server["user"],
            password=server["password"],
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
    except Exception as e:
        logger.error("SSH connection failed: %s", e)
        return False, str(e)

    logger.info("Connected. Opening interactive shell...")
    chan = client.invoke_shell()
    chan.settimeout(2.0)
    time.sleep(0.5)

    banner = stream_channel_output(chan, timeout=1.0)
    logger.debug("Initial prompt:\n%s", banner)

    commands = [
        "ZMVO",
        f"MSISDN={msisdn}",
        f";"
    ]

    full_output = []
    for cmd in commands:
        logger.info(f"{Colors.BRIGHT_MAGENTA}Executing command:{Colors.RESET} {Colors.BRIGHT_GREEN}{cmd}{Colors.RESET}")
        chan.send((cmd + "\r\n").encode('utf-8'))
        out = stream_channel_output(chan, timeout=READ_TIMEOUT)
        full_output.append(f"\n>>> {cmd}\n{out}\n{'-'*80}\n")
        # also log output for transparency
        logger.debug("Command output:\n%s", out)
        if "UNKNOWN SUBSCRIBER" in out.upper() or "DX ERROR" in out.upper():
            logger.info(f"{Colors.RED}Detected UNKNOWN SUBSCRIBER pattern — stopping command sequence.{Colors.RESET}")
            break

    chan.close()
    client.close()

    output_text = "".join(full_output)

    # --- Determine presence ---
    upper_out = output_text.upper()
    if "UNKNOWN SUBSCRIBER" in upper_out or "COMMAND EXECUTION FAILED" in upper_out:
        found = False
        logger.info("MSISDN %s NOT PRESENT on %s", msisdn, server["ip"])
    elif "SUBSCRIBER INFORMATION" in upper_out or "MOBILE COUNTRY CODE" in upper_out:
        found = True
        logger.info("MSISDN %s PRESENT on %s", msisdn, server["ip"])
    else:
        found = False
        logger.warning("Could not definitively determine presence; treating as NOT FOUND.")

    return found, output_text


def main(msisdn):
    root_logger = build_logger()
    root_logger.info("Starting MSISDN lookup for %s", msisdn)

    # Clear summary file at start of new run
    summary_file = os.path.join(LOG_DIR, "summary.txt")
    with open(summary_file, "w", encoding="utf-8") as sf:
        sf.write(f"MSISDN Lookup Report - {datetime.now().isoformat()}\n")
        sf.write(f"Searching for: {msisdn}\n")
        sf.write("="*60 + "\n\n")

    for server in SERVERS:
        found, output = connect_and_check(server, msisdn)
        with open(summary_file, "a", encoding="utf-8") as sf:
            sf.write(f"{server['name']} ({server['ip']}) - Found={found}\n")
        if found:
            root_logger.info("✅ Found MSISDN on %s (%s). Stopping search.", server["name"], server["ip"])
            return
        else:
            root_logger.info("MSISDN not found on %s (%s). Checking next server...", server["name"], server["ip"])

    root_logger.info("❌ MSISDN not found on any configured servers.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check MSISDN presence via SSH automation.")
    parser.add_argument("--msisdn", "-m", required=True, help="MSISDN to check (e.g., 4915781993214)")
    args = parser.parse_args()
    main(args.msisdn)
