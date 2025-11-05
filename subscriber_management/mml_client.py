#!/usr/bin/env python3
"""
mml_client.py
SSH client for connecting to MML systems and executing commands.
"""

import paramiko
import time
import socket

from utils.text_processing import process_backspaces
from configs.logging_config import build_logger
from utils.colors import Colors
from configs.config import READ_TIMEOUT, CONNECT_TIMEOUT, SHELL_TIMEOUT


class MMLClient:
    """Client for connecting to MML systems via SSH."""

    def __init__(self, server_config):
        """
        Initialize MML client.
        
        Args:
            server_config: Dictionary with 'name', 'ip', 'user', 'password'
        """
        self.server = server_config
        self.logger = build_logger(server_config["ip"])
        self.client = None
        self.channel = None

    def connect(self):
        """
        Establish SSH connection to the MML system.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.logger.info("Connecting to %s (%s)...", self.server.get("name", ""), self.server["ip"])

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                self.server["ip"],
                username=self.server["user"],
                password=self.server["password"],
                look_for_keys=False,
                allow_agent=False,
                timeout=CONNECT_TIMEOUT
            )
            self.logger.info("Connected. Opening interactive shell...")
            self.channel = self.client.invoke_shell()
            self.channel.settimeout(SHELL_TIMEOUT)
            time.sleep(0.5)

            # Clear initial banner
            self._read_channel_output(timeout=1.0)
            return True

        except Exception as e:
            self.logger.error("SSH connection failed: %s", e)
            return False

    def _read_channel_output(self, timeout=READ_TIMEOUT):
        """
        Read output from the channel until timeout expires.
        
        Args:
            timeout: Seconds to wait for output
            
        Returns:
            String containing the output with backspaces processed
        """
        output = []
        start = time.time()
        
        while True:
            if self.channel.recv_ready():
                try:
                    data = self.channel.recv(4096).decode('utf-8', errors='ignore')
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
        
        raw_output = "".join(output)
        return process_backspaces(raw_output)

    def execute_command(self, command, timeout=READ_TIMEOUT):
        """
        Execute a single MML command and return the output.
        
        Args:
            command: Command string to execute
            timeout: Seconds to wait for output
            
        Returns:
            String containing the command output
        """
        if not self.channel:
            raise RuntimeError("Not connected. Call connect() first.")

        self.logger.info(
            f"{Colors.BRIGHT_MAGENTA}Executing command:{Colors.RESET} "
            f"{Colors.BRIGHT_GREEN}{command}{Colors.RESET}"
        )
        
        # Send command with MML line ending
        self.channel.send((command + "\r\n").encode('utf-8'))
        
        # Read output
        output = self._read_channel_output(timeout=timeout)
        
        # Display output in terminal with color
        self.logger.info(
            f"{Colors.BRIGHT_YELLOW}Command output:{Colors.RESET}\n"
            f"{Colors.YELLOW}%s{Colors.RESET}", output
        )
        
        return output

    def execute_commands(self, commands, stop_on_error=True):
        """
        Execute a sequence of MML commands.
        
        Args:
            commands: List of command strings
            stop_on_error: Stop execution if error detected
            
        Returns:
            Tuple of (all_outputs, found_error)
        """
        outputs = []
        found_error = False
        
        for cmd in commands:
            output = self.execute_command(cmd)
            outputs.append({"command": cmd, "output": output})
            
            # Check for errors
            upper_output = output.upper()
            if stop_on_error and any(pattern in upper_output for pattern in ["UNKNOWN SUBSCRIBER", "DX ERROR"]):
                self.logger.info(
                    f"{Colors.RED}Detected error pattern — stopping command sequence.{Colors.RESET}"
                )
                found_error = True
                break
        
        return outputs, found_error

    def disconnect(self):
        """Close the SSH connection."""
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
        self.logger.info("Disconnected from %s", self.server["ip"])

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
