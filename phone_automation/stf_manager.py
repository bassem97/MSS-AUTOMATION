#!/usr/bin/env python3
"""
stf_manager.py
Manages STF (SmartPhone Test Farm) device connections for phone automation.
Integrates with OpenStf library from UDB project.
"""

import json
import requests
import subprocess
from typing import Optional, Dict, Any


class STFManager:
    """Manages STF device connections using the OpenSTF API."""

    def __init__(self, base_url: str, user_auth: str, logger=None):
        """
        Initialize STF Manager.

        Args:
            base_url: Base URL of the STF server (e.g., "http://172.29.42.44")
            user_auth: User authentication token (with "Bearer " prefix)
            logger: Logger instance for logging
        """
        self.base_url = base_url.rstrip('/')
        # Ensure auth token has Bearer prefix
        if user_auth and not user_auth.startswith('Bearer '):
            self.user_auth = f"Bearer {user_auth}"
        else:
            self.user_auth = user_auth
        self.logger = logger
        self.connected_devices = {}  # Track connected devices by serial

    def _log(self, level: str, message: str):
        """Internal logging helper."""
        if self.logger:
            if level.lower() == 'info':
                self.logger.info(message)
            elif level.lower() == 'debug':
                self.logger.debug(message)
            elif level.lower() == 'warning':
                self.logger.warning(message)
            elif level.lower() == 'error':
                self.logger.error(message)
        else:
            print(f"[{level.upper()}] {message}")

    def check_status(self, status_code: int, response_text: str = "") -> bool:
        """
        Check HTTP status code and log appropriate error.

        Returns:
            bool: True if success (200), False otherwise
        """
        if status_code == 200:
            return True
        elif status_code == 400:
            self._log('error', f"Bad Request: Some parameters are missing or invalid - {response_text}")
        elif status_code == 404:
            self._log('error', f"Not found: The item not available - {response_text}")
        elif status_code == 403:
            self._log('error', f"Forbidden: Device is being used or not available - {response_text}")
        else:
            self._log('error', f"Unknown error (status {status_code}): {response_text}")
        return False

    def get_device_list(self) -> Optional[list]:
        """
        List all STF devices (including disconnected or otherwise inaccessible devices).

        Returns:
            List of devices or None on error
        """
        try:
            headers = {'Authorization': self.user_auth}
            response = requests.get(f"{self.base_url}/api/v1/devices", headers=headers, timeout=10)
            
            if self.check_status(response.status_code, response.text):
                devices = response.json().get('devices', [])
                self._log('debug', f"Found {len(devices)} devices in STF")
                return devices
            return None
        except Exception as e:
            self._log('error', f"Error getting device list: {e}")
            return None

    def get_device_by_serial(self, serial: str) -> Optional[Dict[str, Any]]:
        """
        Get device information by serial number.

        Args:
            serial: Device serial number

        Returns:
            Device info dict or None
        """
        try:
            headers = {'Authorization': self.user_auth}
            response = requests.get(f"{self.base_url}/api/v1/devices/{serial}", headers=headers, timeout=10)
            
            if self.check_status(response.status_code, response.text):
                return response.json().get('device')
            return None
        except Exception as e:
            self._log('error', f"Error getting device {serial}: {e}")
            return None

    def find_device_by_ip_port(self, ip_port: str) -> Optional[str]:
        """
        Find device serial by IP:PORT address.

        Args:
            ip_port: Device IP:PORT (e.g., "172.29.42.44:7413")

        Returns:
            Device serial or None if not found
        """
        try:
            devices = self.get_device_list()
            if not devices:
                return None

            for device in devices:
                # Check if device has remoteConnectUrl matching the ip_port
                remote_url = device.get('remoteConnectUrl', '')
                if ip_port in remote_url:
                    serial = device.get('serial')
                    self._log('debug', f"Found device serial {serial} for {ip_port}")
                    return serial

            # If not found in remoteConnectUrl, check if already connected via ADB
            self._log('debug', f"Device with IP:PORT {ip_port} not found in STF device list")
            return None
        except Exception as e:
            self._log('error', f"Error finding device by IP:PORT: {e}")
            return None

    def add_device_to_user(self, serial: str) -> bool:
        """
        Add a device to the authenticated user's control.
        This is analogous to pressing "Use" in the UI.

        Args:
            serial: Device serial number

        Returns:
            bool: True if successful
        """
        try:
            payload = json.dumps({'serial': serial, 'timeout': 86400000})  # 24 hour timeout
            headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.base_url}/api/v1/user/devices",
                headers=headers,
                data=payload,
                timeout=10
            )
            
            if self.check_status(response.status_code, response.text):
                self._log('info', f"✓ Device {serial} added to user")
                return True
            return False
        except Exception as e:
            self._log('error', f"Error adding device {serial} to user: {e}")
            return False

    def remove_device_from_user(self, serial: str) -> bool:
        """
        Remove a device from the authenticated user's device list.
        This is analogous to pressing "Stop using" in the UI.

        Args:
            serial: Device serial number

        Returns:
            bool: True if successful
        """
        try:
            headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
            response = requests.delete(
                f"{self.base_url}/api/v1/user/devices/{serial}",
                headers=headers,
                timeout=10
            )
            
            if self.check_status(response.status_code, response.text):
                self._log('info', f"✓ Device {serial} removed from user")
                return True
            return False
        except Exception as e:
            self._log('error', f"Error removing device {serial} from user: {e}")
            return False

    def remote_connect_device(self, serial: str) -> Optional[str]:
        """
        Connect to a device remotely via ADB.
        Returns the remote connect URL (IP:PORT).

        Args:
            serial: Device serial number

        Returns:
            str: Remote connect URL (IP:PORT) or None on failure
        """
        try:
            headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.base_url}/api/v1/user/devices/{serial}/remoteConnect",
                headers=headers,
                timeout=10
            )
            
            if self.check_status(response.status_code, response.text):
                remote_url = response.json().get("remoteConnectUrl")
                if remote_url:
                    self._log('info', f"✓ Remote connect URL for {serial}: {remote_url}")
                    
                    # Connect via ADB (try twice as in original OpenStf)
                    for attempt in range(2):
                        self._log('debug', f"Connecting to {remote_url} via ADB (attempt {attempt + 1}/2)...")
                        result = subprocess.run(
                            ["adb", "connect", remote_url],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        self._log('debug', result.stdout.strip())
                    
                    # Store connection info
                    self.connected_devices[serial] = remote_url
                    return remote_url
            return None
        except Exception as e:
            self._log('error', f"Error remote connecting to device {serial}: {e}")
            return None

    def remote_disconnect_device(self, serial: str) -> bool:
        """
        Disconnect a remote debugging session.

        Args:
            serial: Device serial number

        Returns:
            bool: True if successful
        """
        try:
            headers = {'Authorization': self.user_auth, 'Content-Type': 'application/json'}
            response = requests.delete(
                f"{self.base_url}/api/v1/user/devices/{serial}/remoteConnect",
                headers=headers,
                timeout=10
            )
            
            if self.check_status(response.status_code, response.text):
                # Disconnect from ADB
                if serial in self.connected_devices:
                    remote_url = self.connected_devices[serial]
                    self._log('debug', f"Disconnecting {remote_url} from ADB...")
                    subprocess.run(["adb", "disconnect", remote_url], capture_output=True, timeout=5)
                    del self.connected_devices[serial]
                
                self._log('info', f"✓ Device {serial} disconnected")
                return True
            return False
        except Exception as e:
            self._log('error', f"Error disconnecting device {serial}: {e}")
            return False

    def connect_device_by_serial(self, serial: str) -> Optional[str]:
        """
        Full workflow to connect a device via STF:
        1. Add device to user
        2. Remote connect to device

        Args:
            serial: Device serial number

        Returns:
            str: Remote connect URL (IP:PORT) or None on failure
        """
        try:
            self._log('info', f"Connecting to STF device {serial}...")
            
            # Step 1: Add device to user
            if not self.add_device_to_user(serial):
                self._log('error', f"Failed to add device {serial} to user")
                return None
            
            # Step 2: Remote connect
            remote_url = self.remote_connect_device(serial)
            if not remote_url:
                self._log('error', f"Failed to remote connect to device {serial}")
                # Try to clean up
                self.remove_device_from_user(serial)
                return None
            
            self._log('info', f"✓ Successfully connected to device {serial} at {remote_url}")
            return remote_url
            
        except Exception as e:
            self._log('error', f"Error in connect workflow for {serial}: {e}")
            return None

    def disconnect_device_by_serial(self, serial: str) -> bool:
        """
        Full workflow to disconnect a device from STF:
        1. Remote disconnect
        2. Remove device from user

        Args:
            serial: Device serial number

        Returns:
            bool: True if successful
        """
        try:
            self._log('info', f"Disconnecting STF device {serial}...")
            
            # Step 1: Remote disconnect
            self.remote_disconnect_device(serial)
            
            # Step 2: Remove from user
            success = self.remove_device_from_user(serial)
            
            if success:
                self._log('info', f"✓ Successfully disconnected device {serial}")
            return success
            
        except Exception as e:
            self._log('error', f"Error in disconnect workflow for {serial}: {e}")
            return False



