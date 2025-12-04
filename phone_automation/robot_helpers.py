#!/usr/bin/env python3
"""
robot_helpers.py
Helper functions to instantiate Python classes for Robot Framework tests.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from robot.api.deco import keyword
from phone_automation.stf_manager import STFManager
from phone_automation.phone_call_automation import PhoneCallAutomation


# Robot Framework library scope
ROBOT_LIBRARY_SCOPE = "GLOBAL"


@keyword("Create STF Manager")
def create_stf_manager(base_url: str, user_auth: str, logger=None):
    """
    Create an STF Manager instance.

    Args:
        base_url: STF server base URL
        user_auth: STF authentication token
        logger: Optional logger instance (default: None)

    Returns:
        STFManager instance
    """
    return STFManager(base_url, user_auth, logger)


@keyword("Create Phone Call Automation")
def create_phone_call_automation(logger=None, phones=None, stf_config=None, auto_connect_stf=False):
    """
    Create a PhoneCallAutomation instance.

    Args:
        logger: Optional logger instance (default: None)
        phones: Phone configuration dict (default: None)
        stf_config: STF configuration dict (default: None)
        auto_connect_stf: Whether to auto-connect via STF (default: False)

    Returns:
        PhoneCallAutomation instance
    """
    return PhoneCallAutomation(logger, phones, stf_config, auto_connect_stf)

