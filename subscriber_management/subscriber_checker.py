#!/usr/bin/env python3
"""
subscriber_checker.py
Business logic for checking subscriber presence on MML systems.
"""

from .mml_client import MMLClient
from configs.config import (
    MML_COMMANDS,
    SUBSCRIBER_NOT_FOUND_PATTERNS,
    SUBSCRIBER_FOUND_PATTERNS
)


class SubscriberChecker:
    """Handles the logic for checking if a subscriber exists on MML servers."""

    def __init__(self, server_config):
        """
        Initialize subscriber checker.
        
        Args:
            server_config: Dictionary with server connection details
        """
        self.server = server_config
        self.client = MMLClient(server_config)

    def check_msisdn(self, msisdn):
        """
        Check if a MSISDN exists on the server.
        
        Args:
            msisdn: The MSISDN number to check
            
        Returns:
            Tuple of (found: bool, output_text: str)
        """
        # Connect to server
        if not self.client.connect():
            return False, "Connection failed"

        try:
            # Prepare commands with the MSISDN
            commands = [cmd.format(msisdn=msisdn) for cmd in MML_COMMANDS["CHECK_SUBSCRIBER"]]
            
            # Execute commands
            outputs, found_error = self.client.execute_commands(commands)
            
            # Combine all outputs
            output_text = self._format_outputs(outputs)
            
            # Determine presence based on patterns
            found = self._analyze_output(output_text)
            
            return found, output_text

        finally:
            self.client.disconnect()

    def _format_outputs(self, outputs):
        """
        Format command outputs into a readable string.
        
        Args:
            outputs: List of dictionaries with 'command' and 'output' keys
            
        Returns:
            Formatted string
        """
        formatted = []
        for item in outputs:
            formatted.append(f"\n>>> {item['command']}\n{item['output']}\n{'-'*80}\n")
        return "".join(formatted)

    def _analyze_output(self, output_text):
        """
        Analyze output to determine if subscriber was found.
        
        Args:
            output_text: Combined output from all commands
            
        Returns:
            bool: True if subscriber found, False otherwise
        """
        upper_output = output_text.upper()
        
        # Check for "not found" patterns first
        if any(pattern in upper_output for pattern in SUBSCRIBER_NOT_FOUND_PATTERNS):
            self.client.logger.info(
                "MSISDN NOT PRESENT on %s", self.server["ip"]
            )
            return False
        
        # Check for "found" patterns
        if any(pattern in upper_output for pattern in SUBSCRIBER_FOUND_PATTERNS):
            self.client.logger.info(
                "MSISDN PRESENT on %s", self.server["ip"]
            )
            return True
        
        # If neither pattern found, treat as not found
        self.client.logger.warning(
            "Could not definitively determine presence; treating as NOT FOUND."
        )
        return False
