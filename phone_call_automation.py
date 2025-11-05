#!/usr/bin/env python3
"""
phone_call_automation.py
Automates phone calls between mobile devices using ADB commands through STF.
"""

import subprocess
import time
import sys
from typing import Optional


class PhoneCallAutomation:
    """Handles automated phone calls between mobile devices via ADB."""

    def __init__(self):
        self.phones = {
            "phone1": {
                "msisdn": "49 159 001 03141",
                "msisdn_cleaned": "4915900103141",
                "ip_port": "172.29.42.44:7437"
            },
            "phone2": {
                "msisdn": "49 157 819 93213",
                "msisdn_cleaned": "4915781993213",
                "ip_port": "172.29.42.44:7445"
            }
        }

    def clean_msisdn(self, msisdn: str) -> str:
        """Remove spaces from MSISDN."""
        return msisdn.replace(" ", "")

    def connect_device(self, ip_port: str) -> bool:
        """Connect to a device via ADB."""
        try:
            print(f"Connecting to device at {ip_port}...")
            result = subprocess.run(
                ["adb", "connect", ip_port],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✓ Successfully connected to {ip_port}")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print(f"✗ Failed to connect to {ip_port}")
                print(f"  Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ Connection to {ip_port} timed out")
            return False
        except FileNotFoundError:
            print("✗ ADB command not found. Please ensure ADB is installed and in PATH.")
            return False
        except Exception as e:
            print(f"✗ Error connecting to {ip_port}: {e}")
            return False

    def disconnect_device(self, ip_port: str):
        """Disconnect from a device via ADB."""
        try:
            print(f"Disconnecting from {ip_port}...")
            subprocess.run(
                ["adb", "disconnect", ip_port],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception as e:
            print(f"Warning: Error disconnecting from {ip_port}: {e}")

    def make_call(self, caller_ip_port: str, recipient_msisdn: str) -> bool:
        """
        Make a phone call from caller device to recipient number.

        Args:
            caller_ip_port: IP:PORT of the calling device
            recipient_msisdn: Phone number to call (with country code, no spaces)

        Returns:
            bool: True if call was initiated successfully
        """
        try:
            print(f"\nInitiating call from {caller_ip_port} to {recipient_msisdn}...")

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
                print(f"✓ Call initiated successfully!")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print(f"✗ Failed to initiate call")
                print(f"  Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ Call command timed out")
            return False
        except Exception as e:
            print(f"✗ Error making call: {e}")
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
            print(f"\nEnding call on {device_ip_port}...")

            # Send keyevent to end call (KEYCODE_ENDCALL = 6)
            result = subprocess.run(
                ["adb", "-s", device_ip_port, "shell", "input", "keyevent", "6"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"✓ Call ended successfully")
                return True
            else:
                print(f"✗ Failed to end call")
                print(f"  Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"✗ Error ending call: {e}")
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
                print(f"✓ ADB is available")
                print(f"  Version: {result.stdout.strip().split()[4]}")
                return True
            return False
        except FileNotFoundError:
            print("✗ ADB is not installed or not in PATH")
            return False
        except Exception as e:
            print(f"✗ Error checking ADB: {e}")
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
            print("\n=== Connected ADB Devices ===")
            print(result.stdout)
        except Exception as e:
            print(f"Error listing devices: {e}")

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
            print(f"✗ Invalid phone ID. Use 'phone1' or 'phone2'")
            return False

        caller = self.phones[from_phone]
        recipient = self.phones[to_phone]

        print("\n" + "="*60)
        print(f"CALLING: {from_phone.upper()} → {to_phone.upper()}")
        print(f"From: {caller['msisdn']} ({caller['ip_port']})")
        print(f"To: {recipient['msisdn']}")
        print("="*60)

        # Connect to caller device
        if not self.connect_device(caller['ip_port']):
            return False

        # Make the call
        success = self.make_call(
            caller['ip_port'],
            recipient['msisdn_cleaned']
        )

        if success and duration:
            print(f"\nCall will remain active for {duration} seconds...")
            time.sleep(duration)
            self.end_call(caller['ip_port'])

        return success

    def interactive_menu(self):
        """Display an interactive menu for phone call automation."""
        print("\n" + "="*60)
        print("PHONE CALL AUTOMATION - STF")
        print("="*60)
        print(f"Phone 1: {self.phones['phone1']['msisdn']} @ {self.phones['phone1']['ip_port']}")
        print(f"Phone 2: {self.phones['phone2']['msisdn']} @ {self.phones['phone2']['ip_port']}")
        print("="*60)

        while True:
            print("\n--- MENU ---")
            print("1. Call from Phone 1 to Phone 2")
            print("2. Call from Phone 2 to Phone 1")
            print("3. End call on Phone 1")
            print("4. End call on Phone 2")
            print("5. List connected devices")
            print("6. Connect to both phones")
            print("7. Disconnect all devices")
            print("0. Exit")
            print()

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phone1', 'phone2', duration)

            elif choice == "2":
                duration_str = input("Enter call duration in seconds (or press Enter to skip auto-end): ").strip()
                duration = int(duration_str) if duration_str else None
                self.make_phone_call('phone2', 'phone1', duration)

            elif choice == "3":
                self.end_call(self.phones['phone1']['ip_port'])

            elif choice == "4":
                self.end_call(self.phones['phone2']['ip_port'])

            elif choice == "5":
                self.list_devices()

            elif choice == "6":
                self.connect_device(self.phones['phone1']['ip_port'])
                self.connect_device(self.phones['phone2']['ip_port'])

            elif choice == "7":
                subprocess.run(["adb", "disconnect"], capture_output=True)
                print("✓ Disconnected all devices")

            elif choice == "0":
                print("\nExiting...")
                break

            else:
                print("Invalid choice. Please try again.")


def main():
    """Main function to run the phone call automation."""
    automation = PhoneCallAutomation()

    # Check if ADB is available
    if not automation.check_adb_available():
        print("\nPlease install ADB and ensure it's in your system PATH.")
        print("On Ubuntu/Debian: sudo apt-get install adb")
        print("Or download Android Platform Tools from: https://developer.android.com/studio/releases/platform-tools")
        sys.exit(1)

    # Run interactive menu
    automation.interactive_menu()


if __name__ == "__main__":
    main()
