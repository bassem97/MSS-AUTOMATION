#!/usr/bin/env python3
"""
report_generator.py
Generate summary reports for MSISDN lookups.
"""

import os
from datetime import datetime
from configs.config import LOG_DIR


class ReportGenerator:
    """Handles creation of summary reports."""

    def __init__(self, msisdn):
        """
        Initialize report generator.
        
        Args:
            msisdn: The MSISDN being searched
        """
        self.msisdn = msisdn
        self.summary_file = os.path.join(LOG_DIR, "summary.txt")
        self._initialize_report()

    def _initialize_report(self):
        """Create a new report file with header."""
        with open(self.summary_file, "w", encoding="utf-8") as f:
            f.write(f"MSISDN Lookup Report - {datetime.now().isoformat()}\n")
            f.write(f"Searching for: {self.msisdn}\n")
            f.write("=" * 60 + "\n\n")

    def add_result(self, server_name, server_ip, found):
        """
        Add a search result to the report.
        
        Args:
            server_name: Name of the server
            server_ip: IP address of the server
            found: Whether the MSISDN was found
        """
        with open(self.summary_file, "a", encoding="utf-8") as f:
            status = "FOUND" if found else "NOT FOUND"
            f.write(f"{server_name} ({server_ip}) - {status}\n")

    def finalize(self, overall_found):
        """
        Finalize the report with overall result.
        
        Args:
            overall_found: Whether the MSISDN was found on any server
        """
        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            if overall_found:
                f.write("RESULT: MSISDN found on one or more servers\n")
            else:
                f.write("RESULT: MSISDN not found on any server\n")

    def get_report_path(self):
        """Get the path to the summary report file."""
        return self.summary_file
