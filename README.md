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
├── run_subscriber_search.py    # Entry point for MSISDN search
├── run_phone_automation.py     # Entry point for phone automation
├── report_generator.py         # Report generation
├── requirements.txt            # Python dependencies
└── README.md                   # This file
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
3. End call on Phone A
4. End call on Phone B
5. List connected devices
6. Connect to both phones
7. Disconnect all devices
8. Restart ADB server
0. Exit

**Features:**
- Make calls between configured phones
- Set call duration with automatic hangup
- Manage ADB connections
- Restart ADB server when needed

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
