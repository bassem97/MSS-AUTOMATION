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

    def make_phone_call(self, from_phone: str, to_phone: str, duration: Optional[int] = None):
        """
        Make a phone call from one device to another.

        Args:
            from_phone: Caller phone ID ('phone1' or 'phone2')
            to_phone: Recipient phone ID ('phone1' or 'phone2')
            duration: Optional duration in seconds to keep the call active before ending

        Returns:
            bool: True if call was initiated successfully
        """
        if from_phone not in self.phones or to_phone not in self.phones:
            self.logger.error(f"✗ Invalid phone ID. Use 'phone A' or 'phone B'")
            return False

        caller = self.phones[from_phone]
        recipient = self.phones[to_phone]

        self.logger.info("=" * 60)
        self.logger.info(f"CALLING: {from_phone.upper()} → {to_phone.upper()}")
        self.logger.info(f"From: {caller['msisdn']} ({caller['ip_port']})")
        self.logger.info(f"To: {recipient['msisdn']}")
        self.logger.info("=" * 60)

        # Connect to caller device
        if not self.connect_device(caller['ip_port']):
            return False

        # Make the call
        success = self.make_call(
            caller['ip_port'],
            caller['msisdn'],
            recipient['msisdn']
        )

        if success and duration:
            self.logger.info(f"Call will remain active for {duration} seconds...")
            time.sleep(duration)
            self.end_call(caller['ip_port'])

        return success

    def interactive_menu(self):
        """Display an interactive menu for phone call automation."""
        self.logger.info("=" * 60)
        self.logger.info("=" * 19 + " PHONE CALL AUTOMATION " + "=" * 18)
        self.logger.info("=" * 60)
        self.logger.info(f"Phone A: {self.phones['phoneA']['msisdn']} @ {self.phones['phoneA']['ip_port']}")
        self.logger.info(f"Phone B: {self.phones['phoneB']['msisdn']} @ {self.phones['phoneB']['ip_port']}")
        self.logger.info("=" * 60)

        while True:
            print("\n--- MENU ---")
            print("1. Call from Phone A to Phone B")
            print("2. Call from Phone B to Phone A")
            print("3. Check call state (both phones)")
            print("4. Answer call on Phone A")
            print("5. Answer call on Phone B")
            print("6. End call on Phone A")
            print("7. End call on Phone B")
            print("8. List connected devices")
            print("9. Connect to both phones")
            print("10. Disconnect all devices")
            print("11. Restart ADB server")
            print("0. Exit")
            print()

            choice = input("Enter your choice: ").strip()

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


def main():
    """Main function to run the phone call automation."""
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
