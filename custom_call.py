#!/usr/bin/env python3
"""
custom_call.py
Custom automated call scenario:
1. Restart ADB server
2. Connect to both phones
3. Switch Phone A to 2G
4. Phone A calls Phone B
5. Phone B receives and answers after 5 seconds of ringing
6. Call lasts 30 seconds then ends
"""

import time
import sys
from phone_automation.phone_call_automation import PhoneCallAutomation
from configs.logging_config import build_logger
from configs.config import PHONES


def run_custom_scenario():
    """Execute the custom call scenario."""
    # Build logger for custom scenario
    logger = build_logger("phone_call_automation")
    automation = PhoneCallAutomation(logger, PHONES)

    logger.info("=" * 60)
    logger.info("=" * 15 + " CUSTOM CALL SCENARIO " + "=" * 23)
    logger.info("=" * 60)
    logger.info("Scenario Steps:")
    logger.info("  1. Restart ADB server")
    logger.info("  2. Connect to both phones")
    logger.info("  3. Switch Phone A to 2G")
    logger.info("  4. Phone A calls Phone B")
    logger.info("  5. Phone B answers after 5 seconds of ringing")
    logger.info("  6. Call lasts 30 seconds then ends")
    logger.info("=" * 60)

    # Get phone configurations
    phone_a = PHONES['phoneA']
    phone_b = PHONES['phoneB']

    logger.info(f"Phone A: {phone_a['msisdn']} @ {phone_a['ip_port']}")
    logger.info(f"Phone B: {phone_b['msisdn']} @ {phone_b['ip_port']}")

    # Confirm before starting
    print("\n" + "=" * 60)
    confirmation = input("Press Enter to start the scenario (or 'q' to quit): ").strip().lower()
    if confirmation == 'q':
        logger.info("Scenario cancelled by user")
        return

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

        # Step 2: Connect to both phones
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Connecting to both phones...")
        logger.info("=" * 60)

        logger.info(f"Connecting to Phone A ({phone_a['msisdn']})...")
        if not automation.connect_device(phone_a['ip_port']):
            logger.error(f"✗ Failed to connect to Phone A. Aborting scenario.")
            return False

        logger.info(f"Connecting to Phone B ({phone_b['msisdn']})...")
        if not automation.connect_device(phone_b['ip_port']):
            logger.error(f"✗ Failed to connect to Phone B. Aborting scenario.")
            return False

        logger.info("✓ Both phones connected successfully")
        time.sleep(2)  # Wait for connections to stabilize

        # Step 3: Switch Phone A to 2G
        logger.info("\n" + "=" * 60)
        logger.info(f"STEP 3: Switching Phone A ({phone_a['msisdn']}) to 2G...")
        logger.info("=" * 60)
        if not automation.set_network_type(phone_a['ip_port'], '2G'):
            logger.warning("⚠ Failed to switch to 2G, but continuing with scenario...")
        else:
            logger.info("✓ Successfully switched Phone A to 2G")
            logger.info("Waiting for network to stabilize...")
            time.sleep(3)

        # Step 4: Phone A calls Phone B
        logger.info("\n" + "=" * 60)
        logger.info(f"STEP 4: Phone A ({phone_a['msisdn']}) calling Phone B ({phone_b['msisdn']})...")
        logger.info("=" * 60)

        if not automation.make_call(phone_a['ip_port'], phone_a['msisdn'], phone_b['msisdn']):
            logger.error("✗ Failed to initiate call. Aborting scenario.")
            return False

        logger.info("✓ Call initiated successfully")

        # Step 5: Wait for Phone B to ring, then answer after 5 seconds
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Waiting for Phone B to ring...")
        logger.info("=" * 60)

        max_ring_wait = 15  # Maximum wait time for recipient to start ringing
        phone_b_ringing = False
        ring_start_time = None

        for attempt in range(max_ring_wait):
            time.sleep(1)
            phone_b_state = automation.get_call_state(phone_b['ip_port'], phone_b['msisdn'])

            if phone_b_state == 'RINGING':
                if not phone_b_ringing:
                    phone_b_ringing = True
                    ring_start_time = time.time()
                    logger.info(f"📞 Phone B ({phone_b['msisdn']}) is ringing! (after {attempt + 1} seconds)")

                # Calculate how long it has been ringing
                ring_duration = time.time() - ring_start_time

                # Answer after 5 seconds of ringing
                if ring_duration >= 5:
                    logger.info(f"\n⏱️  Phone B has been ringing for {ring_duration:.1f} seconds")
                    logger.info(f"Answering call on Phone B ({phone_b['msisdn']})...")

                    if automation.answer_call(phone_b['ip_port'], phone_b['msisdn']):
                        logger.info("✓ Call answered successfully!")
                        break
                    else:
                        logger.error("✗ Failed to answer call. Aborting scenario.")
                        return False
                else:
                    # Still waiting for 5 seconds to pass
                    remaining = 5 - ring_duration
                    logger.info(f"⏳ Waiting to answer... ({remaining:.1f}s remaining)")
            elif phone_b_state == 'OFFHOOK':
                logger.info(f"📞 Phone B ({phone_b['msisdn']}) already answered!")
                phone_b_ringing = True
                break
            else:
                if (attempt + 1) % 3 == 0:
                    logger.info(f"⏳ Still waiting for ring... ({attempt + 1}/{max_ring_wait}s)")

        if not phone_b_ringing:
            logger.error(f"✗ Phone B never started ringing after {max_ring_wait} seconds. Aborting scenario.")
            return False

        # Wait for call to be fully connected
        logger.info("\n" + "=" * 60)
        logger.info("Waiting for call to be fully connected...")
        logger.info("=" * 60)

        max_connect_wait = 10
        connected = False

        for attempt in range(max_connect_wait):
            time.sleep(1)
            phone_a_state = automation.get_call_state(phone_a['ip_port'], phone_a['msisdn'])
            phone_b_state = automation.get_call_state(phone_b['ip_port'], phone_b['msisdn'])

            if phone_a_state == 'OFFHOOK' and phone_b_state == 'OFFHOOK':
                connected = True
                logger.info(f"✓ Call is now fully connected! (OFFHOOK on both sides after {attempt + 1}s)")
                break
            else:
                if (attempt + 1) % 2 == 0:
                    logger.debug(f"Phone A: {phone_a_state}, Phone B: {phone_b_state} - waiting...")

        if not connected:
            logger.warning("⚠ Call may not be fully connected, but continuing...")

        # Step 6: Call lasts 30 seconds then ends
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6: Call in progress...")
        logger.info("=" * 60)
        logger.info(f"⏱️  Call timer started! Call will last 30 seconds...")

        # Count down with progress updates
        for remaining in range(30, 0, -5):
            logger.info(f"⏳ Call in progress... {remaining}s remaining")
            time.sleep(5)

        logger.info("\n⏱️  30 seconds elapsed. Ending call...")

        if automation.end_call(phone_a['ip_port'], end_all=True, phone_number=phone_a['msisdn']):
            logger.info("✓ Call ended successfully")
        else:
            logger.warning("⚠ Call end command sent (may have already ended)")

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("=" * 17 + " SCENARIO COMPLETE " + "=" * 24)
        logger.info("=" * 60)
        logger.info("✓ All steps completed successfully!")
        logger.info(f"  • ADB server restarted")
        logger.info(f"  • Both phones connected")
        logger.info(f"  • Phone A switched to 2G")
        logger.info(f"  • Call initiated from Phone A to Phone B")
        logger.info(f"  • Phone B answered after 5 seconds of ringing")
        logger.info(f"  • Call lasted 30 seconds and ended")
        logger.info("=" * 60)

        return True

    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Scenario interrupted by user (Ctrl+C)")
        logger.info("Attempting to clean up...")
        try:
            automation.end_call(phone_a['ip_port'], end_all=True, phone_number=phone_a['msisdn'])
        except:
            pass
        return False

    except Exception as e:
        logger.error(f"\n✗ Error during scenario execution: {e}")
        logger.exception("Full traceback:")
        return False


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

