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

    usable = [
        d for d in devices
        if d.get("present") and d.get("ready") and not d.get("using")
    ]

    if len(usable) < 2:
        logger.error(f"Not enough usable devices in STF (found {len(usable)}, need 2)")
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

    logger.info("=" * 60)
    logger.info("=" * 15 + " CUSTOM CALL SCENARIO " + "=" * 23)
    logger.info("=" * 60)
    logger.info("Scenario Steps:")
    logger.info("  1. Restart ADB server")
    logger.info("  2. Auto-select two available STF devices")
    logger.info("  3. Connect both via STF (serial → IP:PORT)")
    logger.info("  4. Switch Phone A to 2G")
    logger.info("  5. Phone A calls Phone B")
    logger.info("  6. Phone B answers after 5 seconds of ringing")
    logger.info("  7. Call lasts 30 seconds then ends")
    logger.info("=" * 60)

    # Pick two available STF devices
    picked = pick_two_available_devices(stf_manager, logger)
    if not picked:
        logger.error("Cannot start scenario: failed to select two STF devices")
        return False

    phone_a_dev, phone_b_dev = picked
    phone_a_serial = phone_a_dev.get("serial")
    phone_b_serial = phone_b_dev.get("serial")

    # Derive MSISDNs from device metadata or prompt the user
    logger.info("\n" + "=" * 60)
    logger.info("STEP 0: Determining MSISDNs for the devices...")
    logger.info("=" * 60)

    phone_a_msisdn = extract_msisdn_from_device(phone_a_dev)
    phone_b_msisdn = extract_msisdn_from_device(phone_b_dev)

    if not phone_a_msisdn:
        logger.warning("⚠ MSISDN for Phone A could not be auto-detected")
        phone_a_msisdn = ask_msisdn_for_device("Phone A", phone_a_dev)

    if not phone_b_msisdn:
        logger.warning("⚠ MSISDN for Phone B could not be auto-detected")
        phone_b_msisdn = ask_msisdn_for_device("Phone B", phone_b_dev)

    logger.info(f"Using MSISDN for Phone A: {phone_a_msisdn}")
    logger.info(f"Using MSISDN for Phone B: {phone_b_msisdn}")

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
    logger.info("\n" + "=" * 60)
    logger.info("STEP 0: Connecting selected STF devices via serial...")
    logger.info("=" * 60)

    phone_a_ip_port = stf_manager.connect_device_by_serial(phone_a_serial)
    if not phone_a_ip_port:
        logger.error(f"Failed to connect Phone A (serial {phone_a_serial}) via STF")
        return False

    phone_b_ip_port = stf_manager.connect_device_by_serial(phone_b_serial)
    if not phone_b_ip_port:
        logger.error(f"Failed to connect Phone B (serial {phone_b_serial}) via STF")
        # Clean up A
        stf_manager.disconnect_device_by_serial(phone_a_serial)
        return False

    logger.info(f"Phone A ADB target: {phone_a_ip_port}")
    logger.info(f"Phone B ADB target: {phone_b_ip_port}")

    # Update automation phones with resolved IP:PORTs
    dynamic_phones["phoneA"]["ip_port"] = phone_a_ip_port
    dynamic_phones["phoneB"]["ip_port"] = phone_b_ip_port

    phone_a = dynamic_phones["phoneA"]
    phone_b = dynamic_phones["phoneB"]

    logger.info(f"Phone A: {phone_a['msisdn']} @ {phone_a['ip_port']} (serial {phone_a_serial})")
    logger.info(f"Phone B: {phone_b['msisdn']} @ {phone_b['ip_port']} (serial {phone_b_serial})")

    # Confirm before starting
    print("\n" + "=" * 60)
    confirmation = input("Press Enter to start the scenario (or 'q' to quit): ").strip().lower()
    if confirmation == "q":
        logger.info("Scenario cancelled by user")
        return False

    try:
        # Step 1: Restart ADB server
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: Restarting ADB server...")
        logger.info("=" * 60)
        if not automation.restart_adb_server():
            logger.error("✗ Failed to restart ADB server. Aborting scenario.")
            return False
        logger.info("✓ ADB server restarted successfully")
        time.sleep(2)  # Wait for ADB to stabilize

        # Step 2: Connect to both phones (using resolved IP:PORT)
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Connecting to both phones (via ADB)...")
        logger.info("=" * 60)

        logger.info(f"Connecting to Phone A ({phone_a['msisdn']})...")
        if not automation.connect_device(phone_a["ip_port"]):
            logger.error("✗ Failed to connect to Phone A. Aborting scenario.")
            return False

        logger.info(f"Connecting to Phone B ({phone_b['msisdn']})...")
        if not automation.connect_device(phone_b["ip_port"]):
            logger.error("✗ Failed to connect to Phone B. Aborting scenario.")
            return False

        logger.info("✓ Both phones connected successfully")
        time.sleep(2)  # Wait for connections to stabilize

        # Step 3: Switch Phone A to 2G
        logger.info("\n" + "=" * 60)
        logger.info(f"STEP 3: Switching Phone A ({phone_a['msisdn']}) to 2G...")
        logger.info("=" * 60)
        if not automation.set_network_type(phone_a["ip_port"], "2G"):
            logger.warning("⚠ Failed to switch to 2G, but continuing with scenario...")
        else:
            logger.info("✓ Successfully switched Phone A to 2G")
            logger.info("Waiting for network to stabilize...")
            time.sleep(3)

        # Step 4: Phone A calls Phone B
        logger.info("\n" + "=" * 60)
        logger.info(
            f"STEP 4: Phone A ({phone_a['msisdn']}) calling Phone B ({phone_b['msisdn']})..."
        )
        logger.info("=" * 60)

        if not automation.make_call(phone_a["ip_port"], phone_a["msisdn"], phone_b["msisdn"]):
            logger.error("✗ Failed to initiate call. Aborting scenario.")
            return False

        logger.info("✓ Call initiated successfully")

        # Step 5: Wait for Phone B to ring, then answer after 5 seconds
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Waiting for Phone B to ring...")
        logger.info("=" * 60)

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
                    logger.info(
                        f"📞 Phone B ({phone_b['msisdn']}) is ringing! (after {attempt + 1} seconds)"
                    )

                # Calculate how long it has been ringing
                ring_duration = time.time() - ring_start_time

                # Answer after 5 seconds of ringing
                if ring_duration >= 5:
                    logger.info(f"\n⏱️  Phone B has been ringing for {ring_duration:.1f} seconds")
                    logger.info(f"Answering call on Phone B ({phone_b['msisdn']})...")

                    if automation.answer_call(phone_b["ip_port"], phone_b["msisdn"]):
                        logger.info("✓ Call answered successfully!")
                        break
                    else:
                        logger.error("✗ Failed to answer call. Aborting scenario.")
                        return False
                else:
                    # Still waiting for 5 seconds to pass
                    remaining = 5 - ring_duration
                    logger.info(f"⏳ Waiting to answer... ({remaining:.1f}s remaining)")
            elif phone_b_state == "OFFHOOK":
                logger.info(f"📞 Phone B ({phone_b['msisdn']}) already answered!")
                phone_b_ringing = True
                break
            else:
                if (attempt + 1) % 3 == 0:
                    logger.info(f"⏳ Still waiting for ring... ({attempt + 1}/{max_ring_wait}s)")

        if not phone_b_ringing:
            logger.error(
                f"✗ Phone B never started ringing after {max_ring_wait} seconds. Aborting scenario."
            )
            return False

        # Wait for call to be fully connected
        logger.info("\n" + "=" * 60)
        logger.info("Waiting for call to be fully connected...")
        logger.info("=" * 60)

        max_connect_wait = 10
        connected = False

        for attempt in range(max_connect_wait):
            time.sleep(1)
            phone_a_state = automation.get_call_state(phone_a["ip_port"], phone_a["msisdn"])
            phone_b_state = automation.get_call_state(phone_b["ip_port"], phone_b["msisdn"])

            if phone_a_state == "OFFHOOK" and phone_b_state == "OFFHOOK":
                connected = True
                logger.info(
                    f"✓ Call is now fully connected! (OFFHOOK on both sides after {attempt + 1}s)"
                )
                break
            else:
                if (attempt + 1) % 2 == 0:
                    logger.debug(
                        f"Phone A: {phone_a_state}, Phone B: {phone_b_state} - waiting..."
                    )

        if not connected:
            logger.warning("⚠ Call may not be fully connected, but continuing...")

        # Step 6: Call lasts 30 seconds then ends
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6: Call in progress...")
        logger.info("=" * 60)
        logger.info("⏱️  Call timer started! Call will last 30 seconds...")

        # Count down with progress updates
        for remaining in range(30, 0, -5):
            logger.info(f"⏳ Call in progress... {remaining}s remaining")
            time.sleep(5)

        logger.info("\n⏱️  30 seconds elapsed. Ending call...")

        if automation.end_call(phone_a["ip_port"], end_all=True, phone_number=phone_a["msisdn"]):
            logger.info("✓ Call ended successfully")
        else:
            logger.warning("⚠ Call end command sent (may have already ended)")

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("=" * 17 + " SCENARIO COMPLETE " + "=" * 24)
        logger.info("=" * 60)
        logger.info("✓ All steps completed successfully!")
        logger.info("  • Both phones connected via STF (serial-based)")
        logger.info("  • Phone A switched to 2G")
        logger.info("  • Call initiated from Phone A to Phone B")
        logger.info("  • Phone B answered after 5 seconds of ringing")
        logger.info("  • Call lasted 30 seconds and ended")
        logger.info("=" * 60)

        return True

    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Scenario interrupted by user (Ctrl+C)")
        logger.info("Attempting to clean up...")
        try:
            automation.end_call(phone_a["ip_port"], end_all=True, phone_number=phone_a["msisdn"])
        except Exception:
            pass
        return False

    except Exception as e:
        logger.error(f"\n✗ Error during scenario execution: {e}")
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
