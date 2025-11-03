#!/usr/bin/env python3
"""
main.py
Main entry point for MSS automation tool.
Checks if a MSISDN exists on configured MML servers.
"""

import argparse

from config import SERVERS
from subscriber_checker import SubscriberChecker
from report_generator import ReportGenerator
from logging_config import build_logger


def search_msisdn(msisdn):
    """
    Search for a MSISDN across all configured servers.
    
    Args:
        msisdn: The MSISDN number to search for
        
    Returns:
        bool: True if found on any server, False otherwise
    """
    logger = build_logger()
    logger.info("Starting MSISDN lookup for %s", msisdn)

    # Initialize report
    report = ReportGenerator(msisdn)

    # Search each server
    for server in SERVERS:
        checker = SubscriberChecker(server)
        found, output = checker.check_msisdn(msisdn)
        
        # Add result to report
        report.add_result(server["name"], server["ip"], found)
        
        # If found, stop searching
        if found:
            logger.info("✅ Found MSISDN on %s (%s). Stopping search.", 
                       server["name"], server["ip"])
            report.finalize(True)
            return True
        else:
            logger.info("MSISDN not found on %s (%s). Checking next server...", 
                       server["name"], server["ip"])

    # Not found on any server
    logger.info("❌ MSISDN not found on any configured servers.")
    report.finalize(False)
    return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Check MSISDN presence on MML servers via SSH automation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --msisdn 4915781993214
  %(prog)s -m 4915781993214
        """
    )
    parser.add_argument(
        "--msisdn", "-m",
        required=True,
        help="MSISDN to check (e.g., 4915781993214)"
    )
    
    args = parser.parse_args()
    
    # Execute search
    found = search_msisdn(args.msisdn)
    
    # Exit with appropriate code
    exit(0 if found else 1)


if __name__ == "__main__":
    main()

