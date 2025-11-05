#!/usr/bin/env python3
"""
run_phone_automation.py
Entry point for phone call automation module.
"""

from phone_automation.phone_call_automation import PhoneCallAutomation
from configs.logging_config import build_logger
import sys


def main():
    """Main entry point for phone call automation."""
    # Build logger for phone call automation
    logger = build_logger("phone_call_automation")
    automation = PhoneCallAutomation(logger)

    # Check if ADB is available
    if not automation.check_adb_available():
        logger.error("\nPlease install ADB and ensure it's in your system PATH.")
        logger.error("On Ubuntu/Debian: sudo apt-get install adb")
        logger.error("Or download Android Platform Tools from: https://developer.android.com/studio/releases/platform-tools")
        sys.exit(1)

    # Run interactive menu
    automation.interactive_menu()


if __name__ == "__main__":
    main()

