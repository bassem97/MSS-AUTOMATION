#!/usr/bin/env python3
"""
phone_call_automation.py
Automates phone calls between mobile devices using ADB commands through STF.
"""

import subprocess
import time
import sys
from typing import Optional

from configs.logging_config import build_logger
from configs.config import PHONES


class PhoneCallAutomation:
    """Handles automated phone calls between mobile devices via ADB."""

    def __init__(self, logger=None, phones=None):
        # Use provided phones or load from config
        self.phones = phones or PHONES
        # Initialize logger
        self.logger = logger or build_logger("phone_call_automation")

    def clean_msisdn(self, msisdn: str) -> str:
        """Remove spaces from MSISDN and add prefix (+) if needed."""
        cleaned = msisdn.replace(" ", "")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned


    def connect_device(self, ip_port: str) -> bool:
        """Connect to a device via ADB."""
        try:
            self.logger.info(f"Connecting to device at {ip_port}...")
            result = subprocess.run(
                ["adb", "connect", ip_port],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout.strip()

            # Check for success indicators in the output
            # ADB returns 0 even on failure, so we need to parse the output text
            if "connected" in output.lower() and "unable to connect" not in output.lower():
                self.logger.info(f"✓ Successfully connected to {ip_port}")
                self.logger.debug(f"Output: {output}")
                return True
            else:
                self.logger.error(f"✗ Failed to connect to {ip_port}")
                self.logger.error(f"Output: {output}")
                if result.stderr.strip():
                    self.logger.error(f"Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Connection to {ip_port} timed out")
            return False
        except FileNotFoundError:
            self.logger.error("✗ ADB command not found. Please ensure ADB is installed and in PATH.")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error connecting to {ip_port}: {e}")
            return False

    def disconnect_device(self, ip_port: str):
        """Disconnect from a device via ADB."""
        try:
            self.logger.info(f"Disconnecting from {ip_port}...")
            subprocess.run(
                ["adb", "disconnect", ip_port],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception as e:
            self.logger.warning(f"Error disconnecting from {ip_port}: {e}")

    def make_call(self, caller_ip_port: str, caller_msisdn: str, recipient_msisdn: str) -> bool:
        """
        Make a phone call from caller device to recipient number.

        Args:
            caller_ip_port: IP:PORT of the calling device
            caller_msisdn: MSISDN of the caller
            recipient_msisdn: Phone number to call (with country code, no spaces)

        Returns:
            bool: True if call was initiated successfully
        """
        try:
            # Clean the recipient MSISDN (remove spaces, add + prefix if needed)
            cleaned_recipient = self.clean_msisdn(recipient_msisdn)

            self.logger.info(f"Initiating call from {caller_msisdn} to {cleaned_recipient}...")

            # ADB command to make a call
            # Using 'am start' to launch dialer with phone number
            call_command = f"am start -a android.intent.action.CALL -d tel:{cleaned_recipient}"

            result = subprocess.run(
                ["adb", "-s", caller_ip_port, "shell", call_command],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.logger.info(f"✓ Call initiated successfully!")
                self.logger.debug(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"✗ Failed to initiate call")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Call command timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error making call: {e}")
            return False

    def end_call(self, device_ip_port: str, end_all: bool = True) -> bool:
        """
        End the current call on a device.

        Args:
            device_ip_port: IP:PORT of the device
            end_all: If True, end call on all connected devices (default: True)

        Returns:
            bool: True if call was ended successfully
        """
        try:
            # First, check the call state
            call_state = self.get_call_state(device_ip_port)

            if call_state == 'IDLE':
                self.logger.warning(f"Cannot end call on {device_ip_port} - no active call (current state: {call_state})")
                return False

            if call_state == 'UNKNOWN':
                self.logger.warning(f"Cannot determine call state on {device_ip_port} - proceeding with caution")

            self.logger.info(f"Ending call on {device_ip_port}...")

            # Send keyevent to end call (KEYCODE_ENDCALL = 6)
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell", "input", "keyevent", "6"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.logger.info(f"✓ Call ended successfully on {device_ip_port}")

                # If end_all is True, end call on all other phones too
                if end_all:
                    for phone_key, phone_data in self.phones.items():
                        other_ip_port = phone_data['ip_port']
                        if other_ip_port != device_ip_port:
                            # Check state before ending call on other device
                            other_state = self.get_call_state(other_ip_port)
                            if other_state in ['RINGING', 'OFFHOOK']:
                                self.logger.info(f"Also ending call on {other_ip_port}...")
                                try:
                                    subprocess.run(
                                        ["adb", "-s", other_ip_port, "shell", "input", "keyevent", "6"],
                                        capture_output=True,
                                        text=True,
                                        timeout=5
                                    )
                                    self.logger.info(f"✓ Call ended on {other_ip_port}")
                                except Exception as e:
                                    self.logger.warning(f"Could not end call on {other_ip_port}: {e}")
                            else:
                                self.logger.debug(f"Skipping {other_ip_port} - not in a call (state: {other_state})")

                # Verify the call was ended by checking state again
                time.sleep(1)  # Give it a moment to transition
                new_state = self.get_call_state(device_ip_port)
                if new_state == 'IDLE':
                    self.logger.info(f"✓ Phone is now idle (state: {new_state})")
                else:
                    self.logger.warning(f"Call state after ending: {new_state}")

                return True
            else:
                self.logger.error(f"✗ Failed to end call")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            self.logger.error(f"✗ Error ending call: {e}")
            return False

    def answer_call(self, device_ip_port: str) -> bool:
        """
        Answer an incoming call on a device.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            bool: True if call was answered successfully
        """
        try:
            # First, check the call state
            call_state = self.get_call_state(device_ip_port)

            if call_state != 'RINGING':
                self.logger.warning(f"Cannot answer call on {device_ip_port} - phone is not ringing (current state: {call_state})")
                return False

            self.logger.info(f"Answering call on {device_ip_port}...")

            # Send keyevent to answer call (KEYCODE_CALL = 5)
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell", "input", "keyevent", "5"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.logger.info(f"✓ Call answered successfully on {device_ip_port}")

                # Verify the call was answered by checking state again
                time.sleep(1)  # Give it a moment to transition
                new_state = self.get_call_state(device_ip_port)
                if new_state == 'OFFHOOK':
                    self.logger.info(f"✓ Call is now active (state: {new_state})")
                else:
                    self.logger.warning(f"Call state after answering: {new_state}")

                return True
            else:
                self.logger.error(f"✗ Failed to answer call")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Answer call command timed out for {device_ip_port}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error answering call: {e}")
            return False

    def get_call_state(self, device_ip_port: str) -> str:
        """
        Get the current call state of a device.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            str: Call state - 'IDLE', 'RINGING', 'OFFHOOK', or 'UNKNOWN' on error
                - IDLE: No call activity
                - RINGING: Incoming call (not answered yet)
                - OFFHOOK: Call is active (answered or outgoing)
        """
        try:
            # Use dumpsys to get telephony state
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell", "dumpsys", "telephony.registry"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout.strip()

                # Parse the output to find call state
                # Looking for lines like: mCallState=0 (or 1, or 2)
                # 0 = IDLE, 1 = RINGING, 2 = OFFHOOK
                for line in output.split('\n'):
                    if 'mCallState=' in line:
                        # Extract the state number
                        if '=0' in line or 'IDLE' in line.upper():
                            self.logger.debug(f"Call state for {device_ip_port}: IDLE")
                            return 'IDLE'
                        elif '=1' in line or 'RINGING' in line.upper():
                            self.logger.debug(f"Call state for {device_ip_port}: RINGING")
                            return 'RINGING'
                        elif '=2' in line or 'OFFHOOK' in line.upper():
                            self.logger.debug(f"Call state for {device_ip_port}: OFFHOOK")
                            return 'OFFHOOK'

                # Default to IDLE if we can't find the state
                self.logger.warning(f"Could not parse call state for {device_ip_port}, defaulting to IDLE")
                return 'IDLE'
            else:
                self.logger.error(f"✗ Failed to get call state from {device_ip_port}")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return 'UNKNOWN'

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Get call state command timed out for {device_ip_port}")
            return 'UNKNOWN'
        except Exception as e:
            self.logger.error(f"✗ Error getting call state: {e}")
            return 'UNKNOWN'

    def check_adb_available(self) -> bool:
        """Check if ADB is available in the system."""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[4] if len(result.stdout.strip().split()) > 4 else "unknown"
                self.logger.info(f"✓ ADB is available (Version: {version})")
                return True
            return False
        except FileNotFoundError:
            self.logger.error("✗ ADB is not installed or not in PATH")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error checking ADB: {e}")
            return False

    def restart_adb_server(self) -> bool:
        """Restart the ADB server by killing and starting it again."""
        try:
            self.logger.info("Killing ADB server...")
            result_kill = subprocess.run(
                ["adb", "kill-server"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result_kill.returncode == 0:
                self.logger.info("✓ ADB server killed successfully")
            else:
                self.logger.warning(f"Warning: {result_kill.stderr.strip()}")

            time.sleep(1)

            self.logger.info("Starting ADB server...")
            result_start = subprocess.run(
                ["adb", "start-server"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result_start.returncode == 0:
                self.logger.info("✓ ADB server started successfully")
                self.logger.info("Note: You may need to authorize the connection on your device(s)")
                return True
            else:
                self.logger.error(f"✗ Failed to start ADB server: {result_start.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("✗ ADB server restart timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error restarting ADB server: {e}")
            return False

    def list_devices(self):
        """List all connected ADB devices."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.logger.info("=== Connected ADB Devices ===")
            for line in result.stdout.strip().split('\n'):
                self.logger.info(line)
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")

    def toggle_flight_mode(self, device_ip_port: str, enable: bool) -> bool:
        """
        Enable or disable flight mode on a device.

        Args:
            device_ip_port: IP:PORT of the device
            enable: True to enable flight mode, False to disable

        Returns:
            bool: True if successful
        """
        try:
            state = "1" if enable else "0"
            action = "Enabling" if enable else "Disabling"
            self.logger.info(f"{action} flight mode on {device_ip_port}...")

            # Use settings command to toggle airplane mode
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "settings", "put", "global", "airplane_mode_on", state],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                self.logger.error(f"✗ Failed to set flight mode setting")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return False

            # Broadcast the change to trigger the mode change
            result_broadcast = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE",
                 "--ez", "state", "true" if enable else "false"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result_broadcast.returncode == 0:
                mode_str = "enabled" if enable else "disabled"
                self.logger.info(f"✓ Flight mode {mode_str} successfully")
                return True
            else:
                self.logger.warning(f"Setting changed but broadcast may have failed")
                return True

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Flight mode toggle timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error toggling flight mode: {e}")
            return False

    def get_flight_mode_status(self, device_ip_port: str) -> Optional[bool]:
        """
        Get the current flight mode status.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            bool: True if enabled, False if disabled, None on error
        """
        try:
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "settings", "get", "global", "airplane_mode_on"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                status = result.stdout.strip()
                is_enabled = status == "1"
                status_str = "enabled" if is_enabled else "disabled"
                self.logger.info(f"Flight mode is {status_str} on {device_ip_port}")
                return is_enabled
            else:
                self.logger.error(f"✗ Failed to get flight mode status")
                return None

        except Exception as e:
            self.logger.error(f"✗ Error getting flight mode status: {e}")
            return None

    def set_network_type(self, device_ip_port: str, network_type: str) -> bool:
        """
        Set the preferred network type (2G, 3G, 4G, or AUTO).
        Uses Samsung-specific values for SM-A546U compatibility.

        Args:
            device_ip_port: IP:PORT of the device
            network_type: Network type - '2G', '3G', '4G', or 'AUTO'

        Returns:
            bool: True if successful
        """
        try:
            # Samsung SM-A546U specific network mode values
            network_map = {
                '2G': '1',      # GSM only
                '3G': '2',      # WCDMA only (3G)
                '4G': '11',     # LTE only (4G)
                'LTE': '11',    # LTE only (alias)
                'AUTO': '10',   # LTE/WCDMA/GSM auto (default)
                '5G': '23',     # NR/LTE (5G preferred)
            }

            if network_type.upper() not in network_map:
                self.logger.error(f"✗ Invalid network type: {network_type}")
                self.logger.error(f"Valid types: 2G, 3G, 4G, LTE, AUTO, 5G")
                return False

            network_value = network_map[network_type.upper()]
            self.logger.info(f"Setting network type to {network_type.upper()} (value: {network_value})...")

            # Method 1: Try settings command (most reliable for Samsung)
            self.logger.debug(f"Attempting Method 1: settings command...")
            result1 = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "settings", "put", "global", "preferred_network_mode", network_value],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Method 2: Try with subscription ID (for dual-SIM devices)
            self.logger.debug(f"Attempting Method 2: settings with subscription ID...")
            result2 = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "settings", "put", "global", "preferred_network_mode1", network_value],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Method 3: Try service call method (requires more permissions)
            self.logger.debug(f"Attempting Method 3: service call...")
            result3 = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "service", "call", "phone", "27", "i32", network_value],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Method 4: Try Samsung-specific service call
            self.logger.debug(f"Attempting Method 4: Samsung-specific service call...")
            result4 = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "service", "call", "phone", "27", "i32", "0", "i32", network_value],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check if any method succeeded
            success = False
            if result1.returncode == 0:
                self.logger.debug(f"✓ Method 1 succeeded")
                success = True
            else:
                self.logger.debug(f"✗ Method 1 failed: {result1.stderr.strip() or 'No error output'}")

            if result2.returncode == 0:
                self.logger.debug(f"✓ Method 2 succeeded")
                success = True
            else:
                self.logger.debug(f"✗ Method 2 failed: {result2.stderr.strip() or 'No error output'}")

            if result3.returncode == 0:
                self.logger.debug(f"✓ Method 3 succeeded")
                success = True
            else:
                self.logger.debug(f"✗ Method 3 failed: {result3.stderr.strip() or 'No error output'}")

            if result4.returncode == 0:
                self.logger.debug(f"✓ Method 4 succeeded")
                success = True
            else:
                self.logger.debug(f"✗ Method 4 failed: {result4.stderr.strip() or 'No error output'}")

            if success:
                self.logger.info(f"✓ Network type setting commands executed successfully")

                # Wait a moment and verify the change
                time.sleep(2)
                self.get_network_type(device_ip_port)
                return True
            else:
                self.logger.warning(f"⚠ All programmatic methods failed. Opening network settings UI...")
                self.logger.info(f"You will need to manually select '{network_type.upper()}' in the network settings.")

                # Open network settings UI as fallback
                if self.open_network_settings_ui(device_ip_port):
                    self.logger.info(f"✓ Network settings opened. Please manually select '{network_type.upper()}'")
                    input("\nPress Enter when you have changed the network type manually...")
                    return True
                else:
                    self.logger.error(f"✗ Failed to open network settings UI")
                    self.logger.error(f"Note: This may require root access or the device may have restricted ADB permissions")
                    return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Network type setting timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error setting network type: {e}")
            return False

    def open_network_settings_ui(self, device_ip_port: str) -> bool:
        """
        Open the network settings UI on the device as a fallback for manual configuration.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            bool: True if settings were opened successfully
        """
        try:
            self.logger.info(f"Opening network settings UI on {device_ip_port}...")

            # Try multiple intents to open network settings
            intents = [
                # Samsung-specific network settings
                "com.samsung.android.app.telephonyui/.netsettings.ui.NetSettingsActivity",
                # Standard Android network settings
                "android.settings.DATA_ROAMING_SETTINGS",
                # Mobile network settings
                "android.settings.NETWORK_OPERATOR_SETTINGS",
                # General wireless settings
                "android.settings.WIRELESS_SETTINGS",
            ]

            for intent in intents:
                self.logger.debug(f"Trying intent: {intent}")

                if "." in intent and "/" in intent:
                    # Component name format
                    result = subprocess.run(
                        ["adb", "-s", device_ip_port, "shell",
                         "am", "start", "-n", intent],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                else:
                    # Action format
                    result = subprocess.run(
                        ["adb", "-s", device_ip_port, "shell",
                         "am", "start", "-a", intent],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                if result.returncode == 0 and "Error" not in result.stdout:
                    self.logger.info(f"✓ Opened network settings UI")
                    return True

            self.logger.warning(f"Could not open network settings UI")
            return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Opening settings UI timed out")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error opening settings UI: {e}")
            return False

    def get_network_type(self, device_ip_port: str) -> Optional[str]:
        """
        Get the current preferred network type.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            str: Network type description, or None on error
        """
        try:
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "settings", "get", "global", "preferred_network_mode"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                mode_value = result.stdout.strip()

                # Samsung-specific network mode value mappings
                mode_descriptions = {
                    '0': 'WCDMA preferred',
                    '1': '2G only (GSM)',
                    '2': '3G only (WCDMA)',
                    '3': 'WCDMA preferred',
                    '9': 'LTE/WCDMA/GSM',
                    '10': 'LTE/WCDMA/GSM (AUTO)',
                    '11': '4G only (LTE)',
                    '20': '5G/LTE/WCDMA/GSM',
                    '23': '5G/LTE preferred',
                }

                description = mode_descriptions.get(mode_value, f'Unknown ({mode_value})')
                self.logger.info(f"Current network type: {description}")
                return description
            else:
                self.logger.error(f"✗ Failed to get network type")
                return None

        except Exception as e:
            self.logger.error(f"✗ Error getting network type: {e}")
            return None

    def get_network_info(self, device_ip_port: str) -> dict:
        """
        Get comprehensive network information from the device.

        Args:
            device_ip_port: IP:PORT of the device

        Returns:
            dict: Network information including operator, signal, type
        """
        info = {}

        try:
            # Get dumpsys telephony info
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell",
                 "dumpsys", "telephony.registry"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout

                # Parse relevant information
                data_network_type = None
                voice_network_type = None

                for line in output.split('\n'):
                    # Look for data network type
                    if 'mDataNetworkType' in line or 'mVoiceNetworkType' in line:
                        # Extract the network type number
                        if '=' in line:
                            type_value = line.split('=')[-1].strip()

                            # Map network type codes to readable names
                            # Reference: Android TelephonyManager constants
                            network_type_map = {
                                '0': 'Unknown',
                                '1': '2G (GPRS)',
                                '2': '2G (EDGE)',
                                '3': '3G (UMTS)',
                                '4': '2G (CDMA)',
                                '5': '2G (CDMA - EVDO rev. 0)',
                                '6': '2G (CDMA - EVDO rev. A)',
                                '7': '2G (1xRTT)',
                                '8': '3G (HSDPA)',
                                '9': '3G (HSUPA)',
                                '10': '3G (HSPA)',
                                '11': '2G (iDen)',
                                '12': '2G (CDMA - eHRPD)',
                                '13': '4G (LTE)',
                                '14': '3G (HSPA+)',
                                '15': '2G (GSM)',
                                '16': '3G (TD-SCDMA)',
                                '17': '3G (IWLAN)',
                                '18': '4G (LTE CA)',
                                '19': '5G (NR)',
                                '20': '5G (NR)',
                            }

                            if 'mDataNetworkType' in line:
                                data_network_type = network_type_map.get(type_value, f'Unknown ({type_value})')
                            elif 'mVoiceNetworkType' in line:
                                voice_network_type = network_type_map.get(type_value, f'Unknown ({type_value})')

                # Get current preferred network mode
                current_mode = self.get_network_type(device_ip_port)

                # Display clean information
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📡 Network Info for {device_ip_port}")
                self.logger.info(f"{'='*60}")

                if data_network_type:
                    self.logger.info(f"📶 Current Data Network: {data_network_type}")
                    info['data_network'] = data_network_type
                else:
                    self.logger.info(f"📶 Current Data Network: Not detected")

                if voice_network_type:
                    self.logger.info(f"📞 Voice Network: {voice_network_type}")
                    info['voice_network'] = voice_network_type

                if current_mode:
                    self.logger.info(f"⚙️  Preferred Mode: {current_mode}")
                    info['preferred_mode'] = current_mode

                self.logger.info(f"{'='*60}\n")

            return info

        except Exception as e:
            self.logger.error(f"✗ Error getting network info: {e}")
            return info

    def make_phone_call(self, caller_key: str, recipient_key: str, duration: Optional[int] = None) -> bool:
        """
        Make a phone call from one phone to another with optional auto-answer and duration.

        Args:
            caller_key: Key of the calling phone ('phoneA' or 'phoneB')
            recipient_key: Key of the recipient phone ('phoneA' or 'phoneB')
            duration: Optional call duration in seconds. If provided, call will be ended automatically.

        Returns:
            bool: True if call was successful
        """
        try:
            caller = self.phones[caller_key]
            recipient = self.phones[recipient_key]

            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Making call from {caller['msisdn']} to {recipient['msisdn']}")
            self.logger.info(f"{'='*60}")

            # Make the call
            if not self.make_call(caller['ip_port'], caller['msisdn'], recipient['msisdn']):
                return False

            self.logger.info("Waiting for call to connect...")
            time.sleep(3)

            # Check if recipient is ringing
            recipient_state = self.get_call_state(recipient['ip_port'])
            if recipient_state == 'RINGING':
                self.logger.info(f"📞 {recipient['msisdn']} is ringing!")

                # Ask if user wants to auto-answer
                answer = input("Do you want to auto-answer? (y/n): ").strip().lower()
                if answer == 'y':
                    time.sleep(1)
                    if self.answer_call(recipient['ip_port']):
                        self.logger.info("✓ Call answered successfully!")

                        # If duration is specified, wait and then end call
                        if duration:
                            self.logger.info(f"Call will end automatically in {duration} seconds...")
                            time.sleep(duration)
                            self.end_call(caller['ip_port'], end_all=True)
                            self.logger.info("✓ Call ended after duration")
                    else:
                        self.logger.error("✗ Failed to answer call")
                        return False
            else:
                self.logger.warning(f"Recipient state: {recipient_state} (expected RINGING)")

            return True

        except Exception as e:
            self.logger.error(f"✗ Error in make_phone_call: {e}")
            return False

    def interactive_menu(self):
        """Display an interactive menu for phone call automation."""
        self.logger.info("=" * 60)
        self.logger.info("=" * 19 + " PHONE CALL AUTOMATION " + "=" * 18)
        self.logger.info("=" * 60)
        self.logger.info(f"Phone A: {self.phones['phoneA']['msisdn']} @ {self.phones['phoneA']['ip_port']}")
        self.logger.info(f"Phone B: {self.phones['phoneB']['msisdn']} @ {self.phones['phoneB']['ip_port']}")
        self.logger.info("=" * 60)

        while True:
            print("\n" + "=" * 60)
            print(" " * 22 + "MAIN MENU")
            print("=" * 60)

            print("\n📞 CALL MANAGEMENT:")
            print("=" * 60)
            print("  1. Call from Phone A to Phone B")
            print("  2. Call from Phone B to Phone A")
            print("  3. Check call state (both phones)")
            print("  4. Answer call on Phone A")
            print("  5. Answer call on Phone B")
            print("  6. End call on Phone A")
            print("  7. End call on Phone B")

            print("\n📱 DEVICE MANAGEMENT:")
            print("=" * 60)
            print("  8. List connected devices")
            print("  9. Connect to both phones")
            print(" 10. Disconnect all devices")
            print(" 11. Restart ADB server")

            print("\n📡 NETWORK MANAGEMENT:")
            print("=" * 60)
            print(" 12. Toggle flight mode on Phone A")
            print(" 13. Toggle flight mode on Phone B")
            print(" 14. Get network info for Phone A")
            print(" 15. Get network info for Phone B")
            print(" 16. Set network type on Phone A")
            print(" 17. Set network type on Phone B")

            print("\n🚪 EXIT:")
            print("=" * 60)
            print("  0. Exit")
            print("=" * 60)

            choice = input("\nEnter your choice: ").strip()

            # Call Management
            if choice == "1":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phoneA', 'phoneB', duration)
                if not self._wait_for_continue():
                    break

            elif choice == "2":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phoneB', 'phoneA', duration)
                if not self._wait_for_continue():
                    break

            elif choice == "3":
                state_a = self.get_call_state(self.phones['phoneA']['ip_port'])
                state_b = self.get_call_state(self.phones['phoneB']['ip_port'])
                self.logger.info(f"📞 Phone A call state: {state_a}")
                self.logger.info(f"📞 Phone B call state: {state_b}")
                if not self._wait_for_continue():
                    break

            elif choice == "4":
                self.answer_call(self.phones['phoneA']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "5":
                self.answer_call(self.phones['phoneB']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "6":
                self.end_call(self.phones['phoneA']['ip_port'], end_all=True)
                if not self._wait_for_continue():
                    break

            elif choice == "7":
                self.end_call(self.phones['phoneB']['ip_port'], end_all=True)
                if not self._wait_for_continue():
                    break

            # Device Management
            elif choice == "8":
                self.list_devices()
                if not self._wait_for_continue():
                    break

            elif choice == "9":
                self.connect_device(self.phones['phoneA']['ip_port'])
                self.connect_device(self.phones['phoneB']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "10":
                subprocess.run(["adb", "disconnect"], capture_output=True)
                self.logger.info("✓ Disconnected all devices")
                if not self._wait_for_continue():
                    break

            elif choice == "11":
                self.restart_adb_server()
                if not self._wait_for_continue():
                    break

            # Network Management
            elif choice == "12":
                status = self.get_flight_mode_status(self.phones['phoneA']['ip_port'])
                if status is not None:
                    self.toggle_flight_mode(self.phones['phoneA']['ip_port'], not status)
                if not self._wait_for_continue():
                    break

            elif choice == "13":
                status = self.get_flight_mode_status(self.phones['phoneB']['ip_port'])
                if status is not None:
                    self.toggle_flight_mode(self.phones['phoneB']['ip_port'], not status)
                if not self._wait_for_continue():
                    break

            elif choice == "14":
                self.get_network_info(self.phones['phoneA']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "15":
                self.get_network_info(self.phones['phoneB']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "16":
                print("\nNetwork types: 2G, 3G, 4G, AUTO, 5G")
                network_type = input("Enter network type: ").strip()
                self.set_network_type(self.phones['phoneA']['ip_port'], network_type)
                if not self._wait_for_continue():
                    break

            elif choice == "17":
                print("\nNetwork types: 2G, 3G, 4G, AUTO, 5G")
                network_type = input("Enter network type: ").strip()
                self.set_network_type(self.phones['phoneB']['ip_port'], network_type)
                if not self._wait_for_continue():
                    break

            # Exit
            elif choice == "0":
                self.logger.info("Exiting...")
                break

            else:
                self.logger.warning("Invalid choice. Please try again.")

    def _wait_for_continue(self) -> bool:
        """
        Wait for user to press Enter to continue or 0 to exit.

        Returns:
            bool: True to continue to menu, False to exit
        """
        print()
        user_input = input("Press Enter to show the menu or 0 to exit: ").strip()
        if user_input == "0":
            self.logger.info("Exiting...")
            return False
        return True
