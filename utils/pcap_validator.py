"""
PCAP Validation Module for BSSAP/MAP Call Flow Analysis

This module validates:
1. BSSAP/MAP flow in Location Update Procedure (LuP)
2. BSSAP originated call via SETUP and proper release
3. MT Call setup and release

"""

import pyshark
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationResult(Enum):
    """Validation result status"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_FOUND = "NOT_FOUND"


@dataclass
class ValidationCheck:
    """Single validation check result"""
    check_name: str
    status: ValidationResult
    details: str
    packet_numbers: List[int] = None
    
    def __post_init__(self):
        if self.packet_numbers is None:
            self.packet_numbers = []


class BSSAPMAPValidator:
    """
    Validates BSSAP/MAP flows in PCAP files for 2G call scenarios
    Also supports VoLTE/IMS (4G/5G) call validation
    """
    
    def __init__(self, pcap_path: str):
        """
        Initialize validator with PCAP file path
        
        Args:
            pcap_path: Path to the PCAP file to validate
        """
        self.pcap_path = pcap_path
        self.validation_results: List[ValidationCheck] = []
        self.call_type = None  # Will be detected: '2G' or 'VoLTE'
        logging.info(f"Initialized BSSAPMAPValidator with PCAP: {pcap_path}")
    
    def detect_call_type(self) -> str:
        """
        Detect if the PCAP contains 2G (BSSAP) or VoLTE/IMS (SIP) call

        Returns:
            'BSSAP' for 2G calls, 'VoLTE' for 4G/5G calls, 'UNKNOWN' if neither
        """
        logging.info("Detecting call type in PCAP...")

        try:
            # Quick scan to detect protocols
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='bssap || sip.Method',
                keep_packets=False
            )

            has_bssap = False
            has_sip = False

            for pkt in cap:
                if hasattr(pkt, 'bssap'):
                    has_bssap = True
                    break
                if hasattr(pkt, 'sip'):
                    has_sip = True
                    break

            cap.close()

            if has_bssap:
                self.call_type = 'BSSAP'
                logging.info("Detected 2G/BSSAP call")
            elif has_sip:
                self.call_type = 'VoLTE'
                logging.info("Detected VoLTE/IMS call")
            else:
                self.call_type = 'UNKNOWN'
                logging.warning("Could not detect call type")

            return self.call_type

        except Exception as e:
            logging.error(f"Error detecting call type: {e}")
            self.call_type = 'UNKNOWN'
            return self.call_type

    def validate_location_update_procedure(self) -> ValidationCheck:
        """
        Validate BSSAP/MAP flow in Location Update Procedure (LuP)
        
        Checks for:
        - BSSAP: Location Update Request
        - MAP: UpdateLocation (MAP_UPDATE_LOCATION)
        - MAP: InsertSubscriberData
        - BSSAP: Location Update Accept
        
        Returns:
            ValidationCheck with result
        """
        logging.info("Validating Location Update Procedure...")
        
        try:
            # Filter for BSSAP and MAP messages
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='bssap || gsm_map',
                keep_packets=False
            )
            
            found_messages = {
                'location_update_request': False,
                'map_update_location': False,
                'map_insert_subscriber_data': False,
                'location_update_accept': False
            }
            packet_numbers = []
            
            for pkt in cap:
                pkt_num = int(pkt.number)
                
                # Check for BSSAP Location Update Request
                if hasattr(pkt, 'bssap'):
                    if hasattr(pkt.bssap, 'msgtype'):
                        msg_type = pkt.bssap.msgtype
                        
                        # Location Update Request (0x08)
                        if msg_type == '0x08':
                            found_messages['location_update_request'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found Location Update Request in packet {pkt_num}")
                        
                        # Location Update Accept (0x09)
                        elif msg_type == '0x09':
                            found_messages['location_update_accept'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found Location Update Accept in packet {pkt_num}")
                
                # Check for MAP messages
                if hasattr(pkt, 'gsm_map'):
                    # UpdateLocation
                    if hasattr(pkt.gsm_map, 'updateLocation_element'):
                        found_messages['map_update_location'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found MAP UpdateLocation in packet {pkt_num}")
                    
                    # InsertSubscriberData
                    if hasattr(pkt.gsm_map, 'insertSubscriberData_element'):
                        found_messages['map_insert_subscriber_data'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found MAP InsertSubscriberData in packet {pkt_num}")
            
            cap.close()
            
            # Determine result
            all_found = all(found_messages.values())
            
            if all_found:
                status = ValidationResult.PASS
                details = "✓ Complete Location Update Procedure found with BSSAP/MAP flow"
            else:
                missing = [k for k, v in found_messages.items() if not v]
                status = ValidationResult.FAIL
                details = f"✗ Missing messages in LuP: {', '.join(missing)}"
            
            result = ValidationCheck(
                check_name="Location Update Procedure (BSSAP/MAP)",
                status=status,
                details=details,
                packet_numbers=packet_numbers
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            logging.error(f"Error validating Location Update Procedure: {e}")
            result = ValidationCheck(
                check_name="Location Update Procedure (BSSAP/MAP)",
                status=ValidationResult.FAIL,
                details=f"✗ Error during validation: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_mo_call_setup_release(self) -> ValidationCheck:
        """
        Validate Mobile Originated (MO) Call Setup and Release
        
        Checks for:
        - BSSAP: SETUP message (call origination)
        - BSSAP: CONNECT (call answered)
        - BSSAP: DISCONNECT with normal release cause from A-party
        - BSSAP: RELEASE COMPLETE
        
        Returns:
            ValidationCheck with result
        """
        logging.info("Validating MO Call Setup and Release...")
        
        try:
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='bssap',
                keep_packets=False
            )
            
            found_messages = {
                'setup': False,
                'connect': False,
                'disconnect': False,
                'release_complete': False
            }
            packet_numbers = []
            release_cause = None
            release_pkt_num = None
            
            for pkt in cap:
                pkt_num = int(pkt.number)
                
                if hasattr(pkt, 'bssap'):
                    if hasattr(pkt.bssap, 'msgtype'):
                        msg_type = pkt.bssap.msgtype
                        
                        # SETUP (0x05)
                        if msg_type == '0x05':
                            found_messages['setup'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found SETUP message in packet {pkt_num}")
                        
                        # CONNECT (0x07)
                        elif msg_type == '0x07':
                            found_messages['connect'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found CONNECT message in packet {pkt_num}")
                        
                        # DISCONNECT (0x25)
                        elif msg_type == '0x25':
                            found_messages['disconnect'] = True
                            packet_numbers.append(pkt_num)
                            release_pkt_num = pkt_num
                            
                            # Extract release cause
                            if hasattr(pkt.bssap, 'cause'):
                                release_cause = pkt.bssap.cause
                                logging.info(f"Found DISCONNECT in packet {pkt_num}, cause: {release_cause}")
                            else:
                                logging.info(f"Found DISCONNECT in packet {pkt_num}")
                        
                        # RELEASE COMPLETE (0x2a)
                        elif msg_type == '0x2a':
                            found_messages['release_complete'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found RELEASE COMPLETE in packet {pkt_num}")
            
            cap.close()
            
            # Determine result
            all_found = all(found_messages.values())
            
            if all_found:
                # Check if release cause is normal (0x10 = Normal call clearing)
                if release_cause and '0x10' in str(release_cause):
                    status = ValidationResult.PASS
                    details = f"✓ MO Call properly setup and released with normal cause (packet {release_pkt_num})"
                else:
                    status = ValidationResult.WARNING
                    details = f"⚠ MO Call setup/released but cause may not be normal: {release_cause}"
            else:
                missing = [k for k, v in found_messages.items() if not v]
                status = ValidationResult.FAIL
                details = f"✗ Missing messages in MO call flow: {', '.join(missing)}"
            
            result = ValidationCheck(
                check_name="MO Call Setup and Release",
                status=status,
                details=details,
                packet_numbers=packet_numbers
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            logging.error(f"Error validating MO call: {e}")
            result = ValidationCheck(
                check_name="MO Call Setup and Release",
                status=ValidationResult.FAIL,
                details=f"✗ Error during validation: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_mt_call_setup_release(self) -> ValidationCheck:
        """
        Validate Mobile Terminated (MT) Call Setup and Release
        
        Checks for:
        - MAP: SendRoutingInfo (to locate subscriber)
        - BSSAP: PAGING request
        - BSSAP: SETUP (to MT party)
        - BSSAP: CONNECT (MT answered)
        - BSSAP: Proper release sequence
        
        Returns:
            ValidationCheck with result
        """
        logging.info("Validating MT Call Setup and Release...")
        
        try:
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='gsm_map || bssap',
                keep_packets=False
            )
            
            found_messages = {
                'send_routing_info': False,
                'paging': False,
                'setup': False,
                'connect': False,
                'release': False
            }
            packet_numbers = []
            
            for pkt in cap:
                pkt_num = int(pkt.number)
                
                # Check for MAP SendRoutingInfo
                if hasattr(pkt, 'gsm_map'):
                    if hasattr(pkt.gsm_map, 'sendRoutingInfo_element'):
                        found_messages['send_routing_info'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found MAP SendRoutingInfo in packet {pkt_num}")
                
                # Check for BSSAP messages
                if hasattr(pkt, 'bssap'):
                    if hasattr(pkt.bssap, 'msgtype'):
                        msg_type = pkt.bssap.msgtype
                        
                        # PAGING (0x52)
                        if msg_type == '0x52':
                            found_messages['paging'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found PAGING in packet {pkt_num}")
                        
                        # SETUP (0x05)
                        elif msg_type == '0x05':
                            found_messages['setup'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found MT SETUP in packet {pkt_num}")
                        
                        # CONNECT (0x07)
                        elif msg_type == '0x07':
                            found_messages['connect'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found MT CONNECT in packet {pkt_num}")
                        
                        # DISCONNECT or RELEASE
                        elif msg_type in ['0x25', '0x2d']:
                            found_messages['release'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found MT RELEASE/DISCONNECT in packet {pkt_num}")
            
            cap.close()
            
            # Determine result
            all_found = all(found_messages.values())
            
            if all_found:
                status = ValidationResult.PASS
                details = "✓ MT Call properly setup and released"
            else:
                missing = [k for k, v in found_messages.items() if not v]
                status = ValidationResult.FAIL
                details = f"✗ Missing messages in MT call flow: {', '.join(missing)}"
            
            result = ValidationCheck(
                check_name="MT Call Setup and Release",
                status=status,
                details=details,
                packet_numbers=packet_numbers
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            logging.error(f"Error validating MT call: {e}")
            result = ValidationCheck(
                check_name="MT Call Setup and Release",
                status=ValidationResult.FAIL,
                details=f"✗ Error during validation: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_volte_registration(self) -> ValidationCheck:
        """
        Validate VoLTE/IMS Registration

        Checks for:
        - SIP REGISTER (IMS registration)
        - 200 OK response

        Returns:
            ValidationCheck with result
        """
        logging.info("Validating VoLTE Registration...")

        try:
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='sip.Method == "REGISTER" || sip.Status-Code == 200',
                keep_packets=False
            )

            found_messages = {
                'register': False,
                'register_ok': False
            }
            packet_numbers = []

            for pkt in cap:
                pkt_num = int(pkt.number)

                if hasattr(pkt, 'sip'):
                    # Check for REGISTER
                    if hasattr(pkt.sip, 'method') and 'REGISTER' in str(pkt.sip.method):
                        found_messages['register'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found SIP REGISTER in packet {pkt_num}")

                    # Check for 200 OK (registration success)
                    if hasattr(pkt.sip, 'status_code') and pkt.sip.status_code == '200':
                        if hasattr(pkt.sip, 'cseq_method') and 'REGISTER' in str(pkt.sip.cseq_method):
                            found_messages['register_ok'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found REGISTER 200 OK in packet {pkt_num}")

            cap.close()

            all_found = all(found_messages.values())

            if all_found:
                status = ValidationResult.PASS
                details = "✓ VoLTE/IMS Registration completed successfully"
            else:
                missing = [k for k, v in found_messages.items() if not v]
                status = ValidationResult.FAIL
                details = f"✗ Missing VoLTE registration: {', '.join(missing)}"

            result = ValidationCheck(
                check_name="VoLTE/IMS Registration",
                status=status,
                details=details,
                packet_numbers=packet_numbers
            )

            self.validation_results.append(result)
            return result

        except Exception as e:
            logging.error(f"Error validating VoLTE registration: {e}")
            result = ValidationCheck(
                check_name="VoLTE/IMS Registration",
                status=ValidationResult.FAIL,
                details=f"✗ Error during validation: {str(e)}"
            )
            self.validation_results.append(result)
            return result

    def validate_volte_call_setup_release(self) -> ValidationCheck:
        """
        Validate VoLTE Call Setup and Release

        Checks for:
        - SIP INVITE (call origination)
        - SIP 200 OK (call answered)
        - SIP ACK (call connected)
        - SIP BYE (call release)
        - 200 OK for BYE

        Returns:
            ValidationCheck with result
        """
        logging.info("Validating VoLTE Call Setup and Release...")

        try:
            cap = pyshark.FileCapture(
                self.pcap_path,
                display_filter='sip.Method == "INVITE" || sip.Method == "ACK" || sip.Method == "BYE" || sip.Status-Code == 200',
                keep_packets=False
            )

            found_messages = {
                'invite': False,
                'invite_ok': False,
                'ack': False,
                'bye': False,
                'bye_ok': False
            }
            packet_numbers = []
            caller = None
            callee = None

            for pkt in cap:
                pkt_num = int(pkt.number)

                if hasattr(pkt, 'sip'):
                    # Check for INVITE
                    if hasattr(pkt.sip, 'method') and pkt.sip.method == 'INVITE':
                        found_messages['invite'] = True
                        packet_numbers.append(pkt_num)

                        # Extract caller/callee
                        if hasattr(pkt.sip, 'from_user'):
                            caller = pkt.sip.from_user
                        if hasattr(pkt.sip, 'to_user'):
                            callee = pkt.sip.to_user

                        logging.info(f"Found SIP INVITE in packet {pkt_num} (From: {caller}, To: {callee})")

                    # Check for 200 OK to INVITE
                    if hasattr(pkt.sip, 'status_code') and pkt.sip.status_code == '200':
                        if hasattr(pkt.sip, 'cseq_method') and pkt.sip.cseq_method == 'INVITE':
                            found_messages['invite_ok'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found INVITE 200 OK in packet {pkt_num}")
                        elif hasattr(pkt.sip, 'cseq_method') and pkt.sip.cseq_method == 'BYE':
                            found_messages['bye_ok'] = True
                            packet_numbers.append(pkt_num)
                            logging.info(f"Found BYE 200 OK in packet {pkt_num}")

                    # Check for ACK
                    if hasattr(pkt.sip, 'method') and pkt.sip.method == 'ACK':
                        found_messages['ack'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found SIP ACK in packet {pkt_num}")

                    # Check for BYE
                    if hasattr(pkt.sip, 'method') and pkt.sip.method == 'BYE':
                        found_messages['bye'] = True
                        packet_numbers.append(pkt_num)
                        logging.info(f"Found SIP BYE in packet {pkt_num}")

            cap.close()

            # Check results
            essential_found = found_messages['invite'] and found_messages['invite_ok'] and found_messages['bye']

            if essential_found:
                status = ValidationResult.PASS
                details = f"✓ VoLTE call properly setup and released (Caller: {caller}, Callee: {callee})"
            else:
                missing = [k for k, v in found_messages.items() if not v and k in ['invite', 'invite_ok', 'bye']]
                status = ValidationResult.FAIL
                details = f"✗ Missing VoLTE call messages: {', '.join(missing)}"

            result = ValidationCheck(
                check_name="VoLTE Call Setup and Release",
                status=status,
                details=details,
                packet_numbers=packet_numbers
            )

            self.validation_results.append(result)
            return result

        except Exception as e:
            logging.error(f"Error validating VoLTE call: {e}")
            result = ValidationCheck(
                check_name="VoLTE Call Setup and Release",
                status=ValidationResult.FAIL,
                details=f"✗ Error during validation: {str(e)}"
            )
            self.validation_results.append(result)
            return result

    def validate_all(self) -> Dict[str, ValidationCheck]:
        """
        Run all validations and return results
        Runs BOTH 2G/BSSAP and VoLTE validations to show complete picture

        Returns:
            Dictionary of validation results keyed by check name
        """
        logging.info("=" * 60)
        logging.info("Starting Complete PCAP Validation")
        logging.info("=" * 60)
        
        # Detect call type for informational purposes
        call_type = self.detect_call_type()
        logging.info(f"Detected primary call type: {call_type}")

        results = {}

        # Always run 2G/BSSAP validations
        logging.info("\n" + "=" * 60)
        logging.info("Running 2G/BSSAP validations...")
        logging.info("=" * 60)
        lup_result = self.validate_location_update_procedure()
        mo_result = self.validate_mo_call_setup_release()
        mt_result = self.validate_mt_call_setup_release()

        results['2g_location_update'] = lup_result
        results['2g_mo_call'] = mo_result
        results['2g_mt_call'] = mt_result

        # Always run VoLTE/IMS validations
        logging.info("\n" + "=" * 60)
        logging.info("Running VoLTE/IMS validations...")
        logging.info("=" * 60)
        reg_result = self.validate_volte_registration()
        call_result = self.validate_volte_call_setup_release()

        results['volte_registration'] = reg_result
        results['volte_call'] = call_result

        logging.info("\n" + "=" * 60)
        logging.info("Validation Complete")
        logging.info("=" * 60)
        
        return results
    
    def generate_report(self) -> str:
        """
        Generate a formatted validation report
        
        Returns:
            Formatted string report
        """
        report = []
        report.append("\n" + "=" * 80)
        report.append("PCAP VALIDATION REPORT".center(80))
        report.append("=" * 80)
        report.append(f"PCAP File: {self.pcap_path}")

        # Separate 2G and VoLTE results
        bssap_results = [r for r in self.validation_results if '2G' in r.check_name or 'BSSAP' in r.check_name or 'Location' in r.check_name or 'MO Call' in r.check_name or 'MT Call' in r.check_name]
        volte_results = [r for r in self.validation_results if 'VoLTE' in r.check_name or 'IMS' in r.check_name]

        # 2G/BSSAP Section
        if bssap_results:
            report.append("\n" + "-" * 80)
            report.append("2G / BSSAP / GSM-MAP VALIDATIONS".center(80))
            report.append("-" * 80)

            for result in bssap_results:
                report.append(f"\n[{result.status.value}] {result.check_name}")
                report.append(f"  {result.details}")
                if result.packet_numbers:
                    # Show first 10 packet numbers to keep report readable
                    pkt_list = result.packet_numbers[:10]
                    pkt_str = ', '.join(map(str, pkt_list))
                    if len(result.packet_numbers) > 10:
                        pkt_str += f", ... (+{len(result.packet_numbers) - 10} more)"
                    report.append(f"  Packets: {pkt_str}")

        # VoLTE/IMS Section
        if volte_results:
            report.append("\n" + "-" * 80)
            report.append("VoLTE / IMS / SIP VALIDATIONS".center(80))
            report.append("-" * 80)

            for result in volte_results:
                report.append(f"\n[{result.status.value}] {result.check_name}")
                report.append(f"  {result.details}")
                if result.packet_numbers:
                    # Show first 10 packet numbers to keep report readable
                    pkt_list = result.packet_numbers[:10]
                    pkt_str = ', '.join(map(str, pkt_list))
                    if len(result.packet_numbers) > 10:
                        pkt_str += f", ... (+{len(result.packet_numbers) - 10} more)"
                    report.append(f"  Packets: {pkt_str}")

        report.append("\n" + "=" * 80)
        
        # Summary
        passed = sum(1 for r in self.validation_results if r.status == ValidationResult.PASS)
        failed = sum(1 for r in self.validation_results if r.status == ValidationResult.FAIL)
        warnings = sum(1 for r in self.validation_results if r.status == ValidationResult.WARNING)
        
        # Separate summaries
        bssap_passed = sum(1 for r in bssap_results if r.status == ValidationResult.PASS)
        bssap_failed = sum(1 for r in bssap_results if r.status == ValidationResult.FAIL)
        volte_passed = sum(1 for r in volte_results if r.status == ValidationResult.PASS)
        volte_failed = sum(1 for r in volte_results if r.status == ValidationResult.FAIL)

        report.append("SUMMARY:")
        report.append(f"  2G/BSSAP:   {bssap_passed} Passed, {bssap_failed} Failed")
        report.append(f"  VoLTE/IMS:  {volte_passed} Passed, {volte_failed} Failed")
        report.append(f"  TOTAL:      {passed} Passed, {failed} Failed, {warnings} Warnings")
        report.append("=" * 80 + "\n")
        
        return "\n".join(report)


def validate_pcap(pcap_path: str) -> Tuple[bool, str]:
    """
    Convenience function to validate a PCAP file
    
    Args:
        pcap_path: Path to PCAP file
    
    Returns:
        Tuple of (all_passed: bool, report: str)
    """
    validator = BSSAPMAPValidator(pcap_path)
    results = validator.validate_all()
    report = validator.generate_report()
    
    all_passed = all(
        r.status == ValidationResult.PASS 
        for r in validator.validation_results
    )
    
    return all_passed, report


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test with a PCAP file
    import sys
    if len(sys.argv) > 1:
        pcap_file = sys.argv[1]
        all_passed, report = validate_pcap(pcap_file)
        print(report)
        sys.exit(0 if all_passed else 1)
    else:
        print("Usage: python pcap_validator.py <pcap_file>")
        sys.exit(1)

