# MSS Automation Tool

A comprehensive Python-based automation toolkit for MSS (Mobile Switching System) operations, including MSISDN lookup on MML systems and automated phone call testing via ADB.

## Features

### Subscriber Management
- 🔍 **Automated MSISDN lookup** across multiple MML servers via SSH
- 📊 **Summary reports** for each search
- 🧹 **Backspace processing** for clean MML output

### Phone Call Automation
- 📞 **Automated phone calls** between mobile devices using ADB
- 🔌 **Remote device connection** via ADB over network
- ⏱️ **Call duration control** with automatic hangup
- 🔄 **ADB server management** with restart capability
- ✈️ **Flight mode control** - Enable/disable airplane mode remotely
- 📡 **Network type switching** - Switch between 2G/3G/4G/5G networks
- 📶 **Network information** - Get detailed network status and signal info

### Common Features
- 🎨 **Colored terminal output** for better readability
- 📝 **Detailed logging** with DEBUG level visible in terminal
- ⚙️ **YAML-based configuration** for easy management
- 📦 **Modular architecture** for easy extension

## Project Structure

```
MSS-AUTOMATION/
├── configs/                    # Configuration files
│   ├── __init__.py
│   ├── config.py               # Main configuration loader
│   ├── logging_config.py       # Logging system configuration
│   ├── SERVERS.yaml            # MML server configuration
│   └── PHONES.yaml             # Phone device configuration
│
├── subscriber_management/      # MSISDN search module
│   ├── __init__.py
│   ├── mml_client.py           # SSH/MML client implementation
│   └── subscriber_checker.py   # Subscriber lookup logic
│
├── phone_automation/           # Phone call automation module
│   ├── __init__.py
│   └── phone_call_automation.py # ADB-based call automation
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── colors.py               # ANSI color codes
│   └── text_processing.py     # Text processing utilities
│
├── logs/                       # Generated log files
├── tests/                      # Robot Framework test suites
│   └── CustomCall.robot        # Automated call test scenarios
├── resources/                  # Robot Framework resources
│   └── PhoneAutomation.resource # Reusable keywords for automation
├── run_subscriber_search.py    # Entry point for MSISDN search
├── run_phone_automation.py     # Entry point for phone automation
├── run_robot_tests.py          # Entry point for Robot Framework tests
├── custom_call.py              # Custom call scenario automation
├── report_generator.py         # Report generation
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── ROBOT_FRAMEWORK_GUIDE.md    # Robot Framework usage guide
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure MML servers in `configs/SERVERS.yaml`:
```yaml
SERVERS:
  MSSTB4:
    ip: 172.29.108.42
    user: AUTOMA
    password: AUTOMA-1

  MSSTB5:
    ip: 172.29.108.106
    user: AUTOMA
    password: AUTOMA-1
```

3. Configure phones in `configs/PHONES.yaml`:
```yaml
PHONES:
  phoneA:
    name: Phone A
    msisdn: "4915900103141"
    ip_port: 172.29.42.44:7437

  phoneB:
    name: Phone B
    msisdn: "4915781993213"
    ip_port: 172.29.42.44:7445
```

## Usage

### Subscriber Search (MSISDN Lookup)

Search for a MSISDN across all configured MML servers:

```bash
python run_subscriber_search.py --msisdn 4915781993214
```

Short form:
```bash
python run_subscriber_search.py -m 4915781993214
```

**Features:**
- Searches across multiple servers sequentially
- Stops on first match
- Generates detailed reports
- Color-coded output with DEBUG messages

### Phone Call Automation

Launch the interactive phone call automation tool:

```bash
python run_phone_automation.py
```

**Interactive Menu:**
1. Call from Phone A to Phone B
2. Call from Phone B to Phone A
3. Check call state (both phones)
4. Answer call on Phone A
5. Answer call on Phone B
6. End call on Phone A
7. End call on Phone B
8. List connected devices
9. Connect to both phones
10. Disconnect all devices
11. Restart ADB server
12. **Toggle flight mode on Phone A**
13. **Toggle flight mode on Phone B**
14. **Check flight mode status (both phones)**
15. **Set network type on Phone A (2G/3G/4G/AUTO)**
16. **Set network type on Phone B (2G/3G/4G/AUTO)**
17. **Get network info (both phones)**
0. Exit

**Features:**
- Make calls between configured phones
- Set call duration with automatic hangup
- Manage ADB connections
- Restart ADB server when needed
- Flight mode control for testing connectivity scenarios
- Network type switching for different generation testing (2G/3G/4G/5G)
- Comprehensive network information retrieval

### Flight Mode Control

Control airplane mode remotely via ADB:

```python
from phone_automation.phone_call_automation import PhoneCallAutomation

automation = PhoneCallAutomation()

# Enable flight mode
automation.toggle_flight_mode("172.29.42.44:7437", enable=True)

# Disable flight mode
automation.toggle_flight_mode("172.29.42.44:7437", enable=False)

# Check status
status = automation.get_flight_mode_status("172.29.42.44:7437")
print(f"Flight mode enabled: {status}")
```

**Use Cases:**
- Test call behavior during network disconnection
- Simulate connectivity issues
- Automated network switching tests
- Emergency mode testing

### Network Type Switching

Switch between different mobile network generations:

```python
from phone_automation.phone_call_automation import PhoneCallAutomation

automation = PhoneCallAutomation()

# Switch to 2G only
automation.set_network_type("172.29.42.44:7437", "2G")

# Switch to 3G
automation.set_network_type("172.29.42.44:7437", "3G")

# Switch to 4G/LTE
automation.set_network_type("172.29.42.44:7437", "4G")

# Switch to AUTO (LTE/WCDMA/GSM)
automation.set_network_type("172.29.42.44:7437", "AUTO")

# Get current network type
current = automation.get_network_type("172.29.42.44:7437")
print(f"Current network: {current}")

# Get detailed network info
info = automation.get_network_info("172.29.42.44:7437")
```

**Supported Network Types:**
- `2G` - GSM only (slowest, maximum coverage)
- `3G` - WCDMA/HSPA (moderate speed)
- `4G` or `LTE` - 4G LTE (high speed)
- `5G` - 5G NR (newest, if device supports)
- `AUTO` - Automatic selection (LTE/WCDMA/GSM)

**Use Cases:**
- Test call quality on different network types
- VoLTE vs circuit-switched voice testing
- Network handover simulation
- Coverage area testing
- Voice quality comparison across generations

**Note:** Network type switching may require special permissions or root access on some devices.

### Custom Call Automation (Python)

Execute a predefined call scenario using STF devices:

```bash
python custom_call.py
```

**Scenario Steps:**
1. Auto-select two available STF devices
2. Connect both via STF (serial → IP:PORT)
3. Switch Phone A to 2G
4. Phone A calls Phone B
5. Phone B answers after 5 seconds of ringing
6. Call lasts 30 seconds and ends

**Features:**
- Automatic STF device selection
- MSISDN auto-detection from device metadata
- Interactive prompts for missing information
- Automatic cleanup on exit

### Robot Framework Tests

Execute automated tests using Robot Framework:

```bash
# Install Robot Framework
pip install robotframework

# Run all tests
python run_robot_tests.py

# Run specific test
python run_robot_tests.py --test "Custom Call Scenario - Two STF Devices"

# Run with custom parameters
python run_robot_tests.py --call-duration 60 --ring-wait 10 --network 4G

# Run with tags
python run_robot_tests.py --include 2G

# Alternative: Use robot command directly
robot tests/CustomCall.robot
```

**Available Robot Tests:**
1. **Custom Call Scenario - Two STF Devices** - Basic automated call test
2. **Custom Call Scenario - Specific Network Types** - Template test for 2G/3G/4G

**Robot Framework Features:**
- ✅ Keyword-driven test automation
- 📊 Detailed HTML reports (log.html, report.html)
- 🏷️ Tag-based test selection
- 🔄 Template-based testing for multiple scenarios
- 📝 Readable test syntax for non-programmers
- 🔌 Easy CI/CD integration

**Output Files:**
- `robot_results/output.xml` - Machine-readable results
- `robot_results/log.html` - Detailed execution log
- `robot_results/report.html` - High-level test report

For detailed Robot Framework usage, see [ROBOT_FRAMEWORK_GUIDE.md](ROBOT_FRAMEWORK_GUIDE.md)

## Output

### Terminal Output
- **Colored logs** with different colors for each level:
  - DEBUG: Gray
  - INFO: Cyan
  - WARNING: Yellow
  - ERROR: Red
- Real-time command execution feedback
- Commands in green, output in yellow

### Log Files
- `logs/<server_ip>.log` - Detailed logs for each MML server
- `logs/phone_call_automation.log` - Phone automation logs
- `logs/summary.txt` - Summary report of MSISDN searches

## Configuration

### YAML Configuration Files

All configurations are now in YAML format for easy editing:

#### SERVERS.yaml
```yaml
SERVERS:
  ServerName:
    ip: xxx.xxx.xxx.xxx
    user: username
    password: password
```

#### PHONES.yaml
```yaml
PHONES:
  phoneID:
    name: Display Name
    msisdn: "phone_number"
    ip_port: xxx.xxx.xxx.xxx:port
```

### Python Configuration (configs/config.py)

#### Timeouts
- `READ_TIMEOUT` - Time to wait for command output (default: 6s)
- `CONNECT_TIMEOUT` - SSH connection timeout (default: 10s)
- `SHELL_TIMEOUT` - Shell channel timeout (default: 2s)

#### MML Commands
```python
MML_COMMANDS = {
    "CHECK_SUBSCRIBER": [
        "ZMVO:MSISDN={msisdn}::;"
    ]
}
```

#### Detection Patterns
```python
SUBSCRIBER_NOT_FOUND_PATTERNS = ["UNKNOWN SUBSCRIBER", "DX ERROR", "COMMAND EXECUTION FAILED"]
SUBSCRIBER_FOUND_PATTERNS = ["SUBSCRIBER INFORMATION", "MOBILE COUNTRY CODE"]
```

## Architecture

### Modular Design

The project follows a clean, modular architecture:

1. **configs/** - Centralized configuration
   - YAML-based server and phone configs
   - Unified logging system
   - All settings in one place

2. **subscriber_management/** - MSISDN search module
   - SSH/MML client for server communication
   - Subscriber checking logic
   - Pattern matching and analysis

3. **phone_automation/** - Phone call module
   - ADB-based phone control
   - Call automation and management
   - Device connection handling

4. **utils/** - Shared utilities
   - ANSI color codes
   - Text processing functions
   - Reusable helpers

### Key Benefits

✅ **Separation of Concerns** - Each module handles one responsibility
✅ **Easy Configuration** - YAML files for non-developers
✅ **Reusable Components** - Modules can be used independently
✅ **Scalable** - Easy to add new servers, phones, or features
✅ **Maintainable** - Clear structure, easy to navigate

## Extending the Tool

### Add New MML Server
Simply edit `configs/SERVERS.yaml`:
```yaml
SERVERS:
  NewServer:
    ip: 172.29.108.200
    user: USERNAME
    password: PASSWORD
```

### Add New Phone
Edit `configs/PHONES.yaml`:
```yaml
PHONES:
  phoneC:
    name: Phone C
    msisdn: "4915999999999"
    ip_port: 172.29.42.44:7450
```

### Add New MML Commands
1. Define command in `configs/config.py` → `MML_COMMANDS`
2. Create method in `SubscriberChecker` class
3. Call from main flow

### Custom Phone Actions
1. Extend `PhoneCallAutomation` class
2. Add new methods for your actions
3. Add menu options in `interactive_menu()`

## Requirements

- Python 3.6+
- paramiko >= 2.11 (for SSH connections)
- pyyaml >= 5.1 (for YAML configuration)
- ADB (Android Debug Bridge) for phone automation

Install ADB on Ubuntu/Debian:
```bash
sudo apt-get install adb
```

## Troubleshooting

### Subscriber Management

**Connection Issues:**
- Verify server configuration in `configs/SERVERS.yaml`
- Check network connectivity
- Verify SSH credentials

**Output Not Captured:**
- Increase `READ_TIMEOUT` in `configs/config.py`
- Check MML command syntax
- Review server logs in `logs/` directory

### Phone Automation

**ADB Not Found:**
```bash
sudo apt-get install adb
```

**Device Connection Failed:**
- Verify IP:PORT in `configs/PHONES.yaml`
- Check device is connected to STF
- Use "Restart ADB server" menu option
- Check for authorization dialogs on device

**Call Not Initiated:**
- Ensure device has CALL permission
- Verify MSISDN format (no spaces)
- Check ADB connection status

### General

**YAML Configuration Errors:**
- Validate YAML syntax (indentation matters!)
- Ensure required fields are present
- Check file exists in `configs/` directory

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.6+)

## Development

### Import Examples

```python
# Import configurations
from configs.config import SERVERS, PHONES
from configs.logging_config import build_logger

# Import subscriber management
from subscriber_management import SubscriberChecker, MMLClient

# Import phone automation
from phone_automation import PhoneCallAutomation

# Use the modules
logger = build_logger("my_app")
automation = PhoneCallAutomation(logger)
checker = SubscriberChecker(SERVERS[0])
```

### Testing

Test configuration loading:
```bash
python -c "from configs.config import SERVERS, PHONES; print(f'Servers: {len(SERVERS)}, Phones: {len(PHONES)}')"
```

### Logging Levels

The logging system supports multiple levels:
- **DEBUG**: Detailed information (visible in terminal and files)
- **INFO**: General information (cyan in terminal)
- **WARNING**: Warning messages (yellow in terminal)
- **ERROR**: Error messages (red in terminal)

## License

Internal tool - All rights reserved

## Version History

- **v2.0** (Nov 2025) - Reorganized structure, YAML configs, phone automation
- **v1.0** (Oct 2025) - Initial release with MSISDN search

---

**Last Updated:** November 5, 2025
