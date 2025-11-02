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
from datetime import datetime

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

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if server_ip:
        fh = logging.FileHandler(os.path.join(LOG_DIR, f"{server_ip}.log"), mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
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
        f"MSISDN={msisdn}::;"
    ]

    full_output = []
    for cmd in commands:
        logger.info("Executing command: %s", cmd)
        chan.send(cmd + "\n")
        out = stream_channel_output(chan, timeout=READ_TIMEOUT)
        full_output.append(f"\n>>> {cmd}\n{out}\n{'-'*80}\n")
        # also log output for transparency
        logger.debug("Command output:\n%s", out)
        if "UNKNOWN SUBSCRIBER" in out.upper() or "DX ERROR" in out.upper():
            logger.info("Detected UNKNOWN SUBSCRIBER pattern — stopping command sequence.")
            break

    chan.close()
    client.close()

    output_text = "".join(full_output)

    # --- write everything into log file explicitly ---
    log_path = os.path.join(LOG_DIR, f"{server['ip']}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n\n==== SESSION START %s ====\n" % datetime.now().isoformat())
        f.write(output_text)
        f.write("\n==== SESSION END ====\n")

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

    for server in SERVERS:
        found, output = connect_and_check(server, msisdn)
        summary_file = os.path.join(LOG_DIR, "summary.txt")
        with open(summary_file, "a", encoding="utf-8") as sf:
            sf.write(f"{datetime.now().isoformat()} - {server['ip']} - Found={found}\n")
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
