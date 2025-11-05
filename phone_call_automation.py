#!/usr/bin/env python3
"""
phone_call_automation.py
Automates phone calls between mobile devices using ADB commands through STF.
"""

import subprocess
import time
import sys
from typing import Optional

from logging_config import build_logger


class PhoneCallAutomation:
    """Handles automated phone calls between mobile devices via ADB."""

    def __init__(self, logger=None):
        self.phones = {
            "phoneA": {
                "msisdn": "4915900103141",
                "ip_port": "172.29.42.44:7437"
            },
            "phoneB": {
                "msisdn": "4915781993213",
                "ip_port": "172.29.42.44:7445"
            }
        }
        # Initialize logger
        self.logger = logger or build_logger("phone_call_automation")

    def clean_msisdn(self, msisdn: str) -> str:
        """Remove spaces from MSISDN."""
        return msisdn.replace(" ", "")

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

            if result.returncode == 0:
                self.logger.info(f"✓ Successfully connected to {ip_port}")
                self.logger.debug(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"✗ Failed to connect to {ip_port}")
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
            self.logger.info(f"Initiating call from {caller_msisdn} to {recipient_msisdn}...")

            # ADB command to make a call
            # Using 'am start' to launch dialer with phone number
            call_command = f"am start -a android.intent.action.CALL -d tel:{recipient_msisdn}"

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

    def end_call(self, device_ip_port: str) -> bool:
        """
        End the current call on a device.

        Args:
            device_ip_port: IP:PORT of the device

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
                self.logger.info(f"✓ Call ended successfully")
                return True
            else:
                self.logger.error(f"✗ Failed to end call")
                self.logger.error(f"Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            self.logger.error(f"✗ Error ending call: {e}")
            return False

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
            self.logger.error(f"✗ Invalid phone ID. Use 'phone1' or 'phone2'")
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
        print("\n" + "="*60)
        print("="*19+" PHONE CALL AUTOMATION "+"="*18)
        print("="*60)
        print(f"Phone A: {self.phones['phoneA']['msisdn']} @ {self.phones['phoneA']['ip_port']}")
        print(f"Phone B: {self.phones['phoneB']['msisdn']} @ {self.phones['phoneB']['ip_port']}")
        print("="*60)

        while True:
            print("\n--- MENU ---")
            print("1. Call from Phone A to Phone B")
            print("2. Call from Phone B to Phone A")
            print("3. End call on Phone A")
            print("4. End call on Phone B")
            print("5. List connected devices")
            print("6. Connect to both phones")
            print("7. Disconnect all devices")
            print("8. Restart ADB server")
            print("0. Exit")
            print()

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phone A', 'phone B', duration)
                if not self._wait_for_continue():
                    break

            elif choice == "2":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phone B', 'phone A', duration)
                if not self._wait_for_continue():
                    break

            elif choice == "3":
                self.end_call(self.phones['phoneA']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "4":
                self.end_call(self.phones['phoneB']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "5":
                self.list_devices()
                if not self._wait_for_continue():
                    break

            elif choice == "6":
                self.connect_device(self.phones['phoneA']['ip_port'])
                self.connect_device(self.phones['phoneB']['ip_port'])
                if not self._wait_for_continue():
                    break

            elif choice == "7":
                subprocess.run(["adb", "disconnect"], capture_output=True)
                self.logger.info("✓ Disconnected all devices")
                if not self._wait_for_continue():
                    break

            elif choice == "8":
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
