#!/usr/bin/env python3
"""
custom_call.py
Custom automated call scenario:
1. Restart ADB server
2. Auto-select two available STF devices by serial
3. Connect to both phones via STF (no IP:PORT needed in config)
4. Switch Phone A to 2G
5. Phone A calls Phone B
6. Phone B receives and answers after 5 seconds of ringing
7. Call lasts 30 seconds then ends
"""

import re
import time
import sys
from phone_automation.phone_call_automation import PhoneCallAutomation
from phone_automation.stf_manager import STFManager
from configs.logging_config import build_logger
from configs.config import STF_CONFIG


def extract_msisdn_from_device(device):
    """Try to extract an MSISDN from STF device metadata.

    Heuristics:
      - Look into device['notes'] if present
      - Fallback to provider info or other text fields
      - Return first 10+ digit number found (optionally with +49 prefix)
    """
    candidates = []

    # Notes field (commonly used in your STF to store MSISDN info)
    notes = device.get("notes") or device.get("note") or ""
    if isinstance(notes, str):
        candidates.append(notes)

    # Provider/carrier name sometimes embeds the number
    provider = device.get("provider") or {}
    if isinstance(provider, dict):
        name = provider.get("name")
        if isinstance(name, str):
            candidates.append(name)

    # Join all text and search for digit sequences that look like phone numbers
    text = " \n".join(candidates)

    # Prefer numbers starting with country code 49 or +49, but accept any 10+ digits
    patterns = [
        r"\+?49\d{8,}",   # +49XXXXXXXX or 49XXXXXXXX
        r"\d{10,}"        # generic 10+ digits
    ]

    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            raw = m.group(0)
            # Normalize to international format with leading '+'
            if not raw.startswith("+"):
                raw = "+" + raw
            return raw

    return None


def ask_msisdn_for_device(label, device):
    """Interactively ask user for MSISDN if it cannot be auto-detected."""
    serial = device.get("serial", "UNKNOWN")
    model = device.get("model", "UNKNOWN")

    print("\n" + "-" * 60)
    print(f"MSISDN for {label}")
    print("-" * 60)
    print(f"Selected device serial: {serial}")
    print(f"Model: {model}")
    notes = device.get("notes") or device.get("note")
    if notes:
        print(f"Notes: {notes}")

    while True:
        msisdn = input(f"Enter MSISDN for {label} (format 49XXXXXXXXXX or +49...): ").strip()
        if not msisdn:
            print("MSISDN is required. Please enter a value.")
            continue
        # Basic validation: must contain at least 8 digits
        digits = re.sub(r"\D", "", msisdn)
        if len(digits) < 8:
            print("Entered value does not look like a valid MSISDN, please try again.")
            continue
        if not msisdn.startswith("+"):
            msisdn = "+" + msisdn
        return msisdn


def pick_two_available_devices(stf_manager, logger):
    """Pick two available STF devices (present, ready, not in use).

    Returns a list of two device dicts or None if not enough devices.
    """
    devices = stf_manager.get_device_list()
    if not devices:
        logger.error("No devices returned from STF API")
        return None

    logger.info(f"Total devices in STF: {len(devices)}")

    # More robust filtering - check multiple conditions
    usable = []
    for d in devices:
        serial = d.get("serial", "UNKNOWN")
        present = d.get("present", False)
        ready = d.get("ready", False)
        using = d.get("using", False)
        owner = d.get("owner")

        # Log status of each device for debugging
        logger.debug(
            f"Device {serial}: present={present}, ready={ready}, "
            f"using={using}, owner={owner}"
        )

        # A device is available if:
        # - It's physically present
        # - It's in ready state
        # - It's not being used (using=False)
        # - It has no owner (owner is None or empty)
        is_available = (
            present
            and ready
            and not using
            and (owner is None or owner == "" or owner == {})
        )

        if is_available:
            usable.append(d)
            logger.info(f"✓ Device {serial} ({d.get('model')}) is available")
        else:
            reasons = []
            if not present:
                reasons.append("not present")
            if not ready:
                reasons.append("not ready")
            if using:
                reasons.append("in use")
            if owner:
                reasons.append(f"owned by {owner}")
            logger.debug(f"✗ Device {serial} unavailable: {', '.join(reasons)}")

    if len(usable) < 2:
        logger.error(
            f"Not enough available devices in STF (found {len(usable)}, need 2). "
            f"Total devices: {len(devices)}"
        )
        # Show available devices
        if usable:
            logger.info(f"Available devices: {[d.get('serial') for d in usable]}")
        return None

    # Sort for determinism (by model + serial)
    usable.sort(key=lambda d: (d.get("model", ""), d.get("serial", "")))

    phone_a_dev, phone_b_dev = usable[0], usable[1]

    logger.info("Selected STF devices:")
    logger.info(
        f"  Phone A: {phone_a_dev.get('serial')} - {phone_a_dev.get('model')} "
        f"(OS {phone_a_dev.get('version')})"
    )
    logger.info(
        f"  Phone B: {phone_b_dev.get('serial')} - {phone_b_dev.get('model')} "
        f"(OS {phone_b_dev.get('version')})"
    )

    return phone_a_dev, phone_b_dev


def run_custom_scenario():
    """Execute the custom call scenario using auto-selected STF devices."""
    # Build logger for custom scenario
    logger = build_logger("phone_call_automation")

    # Also print to console for Robot Framework visibility
    def log_and_print(msg, level="INFO"):
        """Log message and print to console for Robot Framework."""
        # Always print to stdout first (Robot Framework captures this)
        print(msg, flush=True)

        # Then log to file
        if level == "INFO":
            logger.info(msg)
        elif level == "ERROR":
            logger.error(msg)
        elif level == "WARNING":
            logger.warning(msg)
        elif level == "DEBUG":
            logger.debug(msg)

    # Initialize STF manager from config
    stf_cfg = STF_CONFIG
    if not stf_cfg or not stf_cfg.get("enabled", False):
        logger.error("STF is not enabled in PHONES.yaml (STF.enabled=false)")
        return False

    base_url = stf_cfg.get("base_url")
    user_auth = stf_cfg.get("user_auth")
    if not base_url or not user_auth:
        logger.error("STF configuration incomplete: base_url or user_auth missing")
        return False

    stf_manager = STFManager(base_url, user_auth, logger)

    log_and_print("=" * 60)
    log_and_print("=" * 15 + " CUSTOM CALL SCENARIO " + "=" * 23)
    log_and_print("=" * 60)
    log_and_print("Scenario Steps:")
    log_and_print("  1. Restart ADB server")
    log_and_print("  2. Auto-select two available STF devices")
    log_and_print("  3. Connect both via STF (serial → IP:PORT)")
    log_and_print("  4. Switch Phone A to 2G")
    log_and_print("  5. Phone A calls Phone B")
    log_and_print("  6. Phone B answers after 5 seconds of ringing")
    log_and_print("  7. Call lasts 30 seconds then ends")
    log_and_print("=" * 60)

    # Pick two available STF devices
    picked = pick_two_available_devices(stf_manager, logger)
    if not picked:
        logger.error("Cannot start scenario: failed to select two STF devices")
        return False

    phone_a_dev, phone_b_dev = picked
    phone_a_serial = phone_a_dev.get("serial")
    phone_b_serial = phone_b_dev.get("serial")

    # Derive MSISDNs from device metadata or prompt the user
    log_and_print("\n" + "=" * 60)
    log_and_print("STEP 0: Determining MSISDNs for the devices...")
    log_and_print("=" * 60)

    phone_a_msisdn = extract_msisdn_from_device(phone_a_dev)
    phone_b_msisdn = extract_msisdn_from_device(phone_b_dev)

    if not phone_a_msisdn:
        log_and_print("⚠ MSISDN for Phone A could not be auto-detected", "WARNING")
        phone_a_msisdn = ask_msisdn_for_device("Phone A", phone_a_dev)

    if not phone_b_msisdn:
        log_and_print("⚠ MSISDN for Phone B could not be auto-detected", "WARNING")
        phone_b_msisdn = ask_msisdn_for_device("Phone B", phone_b_dev)

    log_and_print(f"Using MSISDN for Phone A: {phone_a_msisdn}")
    log_and_print(f"Using MSISDN for Phone B: {phone_b_msisdn}")

    # Build a minimal phones dict compatible with PhoneCallAutomation.
    dynamic_phones = {
        "phoneA": {
            "name": f"STF-{phone_a_serial}",
            "msisdn": phone_a_msisdn,
            "ip_port": None,
            "serial": phone_a_serial,
        },
        "phoneB": {
            "name": f"STF-{phone_b_serial}",
            "msisdn": phone_b_msisdn,
            "ip_port": None,
            "serial": phone_b_serial,
        },
    }

    automation = PhoneCallAutomation(logger=logger, phones=dynamic_phones, stf_config=stf_cfg, auto_connect_stf=False)

    # Connect via STF using serial numbers and get ADB targets (IP:PORT)
    log_and_print("\n" + "=" * 60)
    log_and_print("STEP 0: Connecting selected STF devices via serial...")
    log_and_print("=" * 60)

    # Double-check device availability before attempting to connect
    log_and_print(f"Verifying Phone A ({phone_a_serial}) availability...")
    fresh_device_a = stf_manager.get_device_by_serial(phone_a_serial)
    if fresh_device_a:
        if fresh_device_a.get("using") or fresh_device_a.get("owner"):
            log_and_print(
                f"⚠ WARNING: Phone A ({phone_a_serial}) appears to be in use! "
                f"using={fresh_device_a.get('using')}, owner={fresh_device_a.get('owner')}",
                "WARNING"
            )
            log_and_print("Attempting to connect anyway...", "WARNING")

    phone_a_ip_port = stf_manager.connect_device_by_serial(phone_a_serial)
    if not phone_a_ip_port:
        log_and_print(f"✗ Failed to connect Phone A (serial {phone_a_serial}) via STF", "ERROR")
        log_and_print("This usually means the device is already in use by another user", "ERROR")
        return False

    log_and_print(f"Verifying Phone B ({phone_b_serial}) availability...")
    fresh_device_b = stf_manager.get_device_by_serial(phone_b_serial)
    if fresh_device_b:
        if fresh_device_b.get("using") or fresh_device_b.get("owner"):
            log_and_print(
                f"⚠ WARNING: Phone B ({phone_b_serial}) appears to be in use! "
                f"using={fresh_device_b.get('using')}, owner={fresh_device_b.get('owner')}",
                "WARNING"
            )
            log_and_print("Attempting to connect anyway...", "WARNING")

    phone_b_ip_port = stf_manager.connect_device_by_serial(phone_b_serial)
    if not phone_b_ip_port:
        log_and_print(f"✗ Failed to connect Phone B (serial {phone_b_serial}) via STF", "ERROR")
        log_and_print("This usually means the device is already in use by another user", "ERROR")
        # Clean up A
        log_and_print("Cleaning up Phone A connection...", "WARNING")
        stf_manager.disconnect_device_by_serial(phone_a_serial)
        return False

    log_and_print(f"Phone A ADB target: {phone_a_ip_port}")
    log_and_print(f"Phone B ADB target: {phone_b_ip_port}")

    # Update automation phones with resolved IP:PORTs
    dynamic_phones["phoneA"]["ip_port"] = phone_a_ip_port
    dynamic_phones["phoneB"]["ip_port"] = phone_b_ip_port

    phone_a = dynamic_phones["phoneA"]
    phone_b = dynamic_phones["phoneB"]

    log_and_print(f"Phone A: {phone_a['msisdn']} @ {phone_a['ip_port']} (serial {phone_a_serial})")
    log_and_print(f"Phone B: {phone_b['msisdn']} @ {phone_b['ip_port']} (serial {phone_b_serial})")


    try:
        # Step 1: Restart ADB server
        log_and_print("\n" + "=" * 60)
        log_and_print("STEP 1: Restarting ADB server...")
        log_and_print("=" * 60)
        if not automation.restart_adb_server():
            log_and_print("✗ Failed to restart ADB server. Aborting scenario.", "ERROR")
            return False
        log_and_print("✓ ADB server restarted successfully")
        time.sleep(2)  # Wait for ADB to stabilize

        # Step 2: Connect to both phones (using resolved IP:PORT)
        log_and_print("\n" + "=" * 60)
        log_and_print("STEP 2: Connecting to both phones (via ADB)...")
        log_and_print("=" * 60)

        log_and_print(f"Connecting to Phone A ({phone_a['msisdn']})...")
        if not automation.connect_device(phone_a["ip_port"]):
            log_and_print("✗ Failed to connect to Phone A. Aborting scenario.", "ERROR")
            return False

        log_and_print(f"Connecting to Phone B ({phone_b['msisdn']})...")
        if not automation.connect_device(phone_b["ip_port"]):
            log_and_print("✗ Failed to connect to Phone B. Aborting scenario.", "ERROR")
            return False

        log_and_print("✓ Both phones connected successfully")
        time.sleep(2)  # Wait for connections to stabilize

        # Step 3: Switch Phone A to 2G
        log_and_print("\n" + "=" * 60)
        log_and_print(f"STEP 3: Switching Phone A ({phone_a['msisdn']}) to 2G...")
        log_and_print("=" * 60)
        if not automation.set_network_type(phone_a["ip_port"], "2G"):
            log_and_print("⚠ Failed to switch to 2G, but continuing with scenario...", "WARNING")
        else:
            log_and_print("✓ Successfully switched Phone A to 2G")
            log_and_print("Waiting for network to stabilize...")
            time.sleep(3)

        # Step 4: Phone A calls Phone B
        log_and_print("\n" + "=" * 60)
        log_and_print(
            f"STEP 4: Phone A ({phone_a['msisdn']}) calling Phone B ({phone_b['msisdn']})..."
        )
        log_and_print("=" * 60)

        if not automation.make_call(phone_a["ip_port"], phone_a["msisdn"], phone_b["msisdn"]):
            log_and_print("✗ Failed to initiate call. Aborting scenario.", "ERROR")
            return False

        log_and_print("✓ Call initiated successfully")

        # Step 5: Wait for Phone B to ring, then answer after 5 seconds
        log_and_print("\n" + "=" * 60)
        log_and_print("STEP 5: Waiting for Phone B to ring...")
        log_and_print("=" * 60)

        max_ring_wait = 30  # Maximum wait time for recipient to start ringing
        phone_b_ringing = False
        ring_start_time = None

        for attempt in range(max_ring_wait):
            time.sleep(1)
            phone_b_state = automation.get_call_state(phone_b["ip_port"], phone_b["msisdn"])

            if phone_b_state == "RINGING":
                if not phone_b_ringing:
                    phone_b_ringing = True
                    ring_start_time = time.time()
                    log_and_print(
                        f"📞 Phone B ({phone_b['msisdn']}) is ringing! (after {attempt + 1} seconds)"
                    )

                # Calculate how long it has been ringing
                ring_duration = time.time() - ring_start_time

                # Answer after 5 seconds of ringing
                if ring_duration >= 5:
                    log_and_print(f"\n⏱️  Phone B has been ringing for {ring_duration:.1f} seconds")
                    log_and_print(f"Answering call on Phone B ({phone_b['msisdn']})...")

                    if automation.answer_call(phone_b["ip_port"], phone_b["msisdn"]):
                        log_and_print("✓ Call answered successfully!")
                        break
                    else:
                        log_and_print("✗ Failed to answer call. Aborting scenario.", "ERROR")
                        return False
                else:
                    # Still waiting for 5 seconds to pass
                    remaining = 5 - ring_duration
                    log_and_print(f"⏳ Waiting to answer... ({remaining:.1f}s remaining)")
            elif phone_b_state == "OFFHOOK":
                log_and_print(f"📞 Phone B ({phone_b['msisdn']}) already answered!")
                phone_b_ringing = True
                break
            else:
                if (attempt + 1) % 3 == 0:
                    log_and_print(f"⏳ Still waiting for ring... ({attempt + 1}/{max_ring_wait}s)")

        if not phone_b_ringing:
            log_and_print(
                f"✗ Phone B never started ringing after {max_ring_wait} seconds. Aborting scenario."
            )
            return False

        # Wait for call to be fully connected
        log_and_print("\n" + "=" * 60)
        log_and_print("Waiting for call to be fully connected...")
        log_and_print("=" * 60)

        max_connect_wait = 10
        connected = False

        for attempt in range(max_connect_wait):
            time.sleep(1)
            phone_a_state = automation.get_call_state(phone_a["ip_port"], phone_a["msisdn"])
            phone_b_state = automation.get_call_state(phone_b["ip_port"], phone_b["msisdn"])

            if phone_a_state == "OFFHOOK" and phone_b_state == "OFFHOOK":
                connected = True
                log_and_print(
                    f"✓ Call is now fully connected! (OFFHOOK on both sides after {attempt + 1}s)"
                )
                break
            else:
                if (attempt + 1) % 2 == 0:
                    log_and_print(
                        f"Phone A: {phone_a_state}, Phone B: {phone_b_state} - waiting...", "DEBUG"
                    )

        if not connected:
            log_and_print("⚠ Call may not be fully connected, but continuing...", "WARNING")

        # Step 6: Call lasts 30 seconds then ends
        log_and_print("\n" + "=" * 60)
        log_and_print("STEP 6: Call in progress...")
        log_and_print("=" * 60)
        log_and_print("⏱️  Call timer started! Call will last 30 seconds...")

        # Count down with progress updates
        for remaining in range(30, 0, -5):
            log_and_print(f"⏳ Call in progress... {remaining}s remaining")
            time.sleep(5)

        log_and_print("\n⏱️  30 seconds elapsed. Ending call...")

        if automation.end_call(phone_a["ip_port"], end_all=True, phone_number=phone_a["msisdn"]):
            log_and_print("✓ Call ended successfully")
        else:
            log_and_print("⚠ Call end command sent (may have already ended)", "WARNING")

        # Final summary
        log_and_print("\n" + "=" * 60)
        log_and_print("=" * 17 + " SCENARIO COMPLETE " + "=" * 24)
        log_and_print("=" * 60)
        log_and_print("✓ All steps completed successfully!")
        log_and_print("  • Both phones connected via STF (serial-based)")
        log_and_print("  • Phone A switched to 2G")
        log_and_print("  • Call initiated from Phone A to Phone B")
        log_and_print("  • Phone B answered after 5 seconds of ringing")
        log_and_print("  • Call lasted 30 seconds and ended")
        log_and_print("=" * 60)

        return True

    except KeyboardInterrupt:
        log_and_print("\n\n⚠ Scenario interrupted by user (Ctrl+C)", "WARNING")
        log_and_print("Attempting to clean up...", "WARNING")
        try:
            automation.end_call(phone_a["ip_port"], end_all=True, phone_number=phone_a["msisdn"])
        except Exception:
            pass
        return False

    except Exception as e:
        log_and_print(f"\n✗ Error during scenario execution: {e}", "ERROR")
        logger.exception("Full traceback:")
        return False
    finally:
        # Always try to disconnect STF sessions
        try:
            stf_manager.disconnect_device_by_serial(phone_a_serial)
        except Exception:
            pass
        try:
            stf_manager.disconnect_device_by_serial(phone_b_serial)
        except Exception:
            pass


def main():
    """Main entry point for custom scenario."""
    try:
        success = run_custom_scenario()
        if success:
            print("\n✓ Scenario completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Scenario failed or was cancelled")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
