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
    """
    
    def __init__(self, pcap_path: str):
        """
        Initialize validator with PCAP file path
        
        Args:
            pcap_path: Path to the PCAP file to validate
        """
        self.pcap_path = pcap_path
        self.validation_results: List[ValidationCheck] = []
        logging.info(f"Initialized BSSAPMAPValidator with PCAP: {pcap_path}")
    
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
    
    def validate_all(self) -> Dict[str, ValidationCheck]:
        """
        Run all validations and return results
        
        Returns:
            Dictionary of validation results keyed by check name
        """
        logging.info("=" * 60)
        logging.info("Starting Complete PCAP Validation")
        logging.info("=" * 60)
        
        # Run all validations
        lup_result = self.validate_location_update_procedure()
        mo_result = self.validate_mo_call_setup_release()
        mt_result = self.validate_mt_call_setup_release()
        
        results = {
            'location_update': lup_result,
            'mo_call': mo_result,
            'mt_call': mt_result
        }
        
        logging.info("=" * 60)
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
        report.append("")
        
        for result in self.validation_results:
            report.append(f"\n[{result.status.value}] {result.check_name}")
            report.append(f"  {result.details}")
            if result.packet_numbers:
                report.append(f"  Packets: {', '.join(map(str, result.packet_numbers))}")
        
        report.append("\n" + "=" * 80)
        
        # Summary
        passed = sum(1 for r in self.validation_results if r.status == ValidationResult.PASS)
        failed = sum(1 for r in self.validation_results if r.status == ValidationResult.FAIL)
        warnings = sum(1 for r in self.validation_results if r.status == ValidationResult.WARNING)
        
        report.append(f"SUMMARY: {passed} Passed, {failed} Failed, {warnings} Warnings")
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

