# MSS Automation Tool

A Python-based automation tool for checking MSISDN presence on MML (Man-Machine Language) telecom systems via SSH.

## Features

- 🔍 **Automated MSISDN lookup** across multiple servers
- 🎨 **Colored terminal output** for better readability
- 📝 **Detailed logging** with per-server log files
- 🧹 **Backspace processing** for clean MML output
- 📊 **Summary reports** for each search
- ⚡ **Real-time command output** in terminal

## Project Structure

```
MSS-AUTOMATION/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── mml_client.py          # SSH/MML client implementation
├── subscriber_checker.py  # Business logic for checking subscribers
├── report_generator.py    # Report generation
├── logging_config.py      # Logging configuration
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── colors.py          # ANSI color codes
│   └── text_processing.py # Text processing utilities
├── logs/                  # Generated log files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure servers in `config.py`:
```python
SERVERS = [
    {"name": "MSSTB4", "ip": "172.29.108.42", "user": "AUTOMA", "password": "AUTOMA-1"},
    {"name": "MSSTB5", "ip": "172.29.108.106", "user": "AUTOMA", "password": "AUTOMA-1"},
]
```

## Usage

Search for a MSISDN:
```bash
python3 main.py --msisdn 4915781993214
```

Short form:
```bash
python3 main.py -m 4915781993214
```

## Output

### Terminal Output
- Real-time colored output showing command execution and results
- Commands in green, output in yellow, errors in red

### Log Files
- `logs/<server_ip>.log` - Detailed logs for each server
- `logs/summary.txt` - Summary report of the search

## Configuration

### Timeouts
Adjust in `config.py`:
- `READ_TIMEOUT` - Time to wait for command output (default: 6s)
- `CONNECT_TIMEOUT` - SSH connection timeout (default: 10s)
- `SHELL_TIMEOUT` - Shell channel timeout (default: 2s)

### MML Commands
Customize MML command sequences in `config.py`:
```python
MML_COMMANDS = {
    "CHECK_SUBSCRIBER": [
        "ZMVO",
        "MSISDN={msisdn}",
        ";"
    ]
}
```

### Detection Patterns
Configure success/failure patterns in `config.py`:
```python
SUBSCRIBER_NOT_FOUND_PATTERNS = ["UNKNOWN SUBSCRIBER", "DX ERROR"]
SUBSCRIBER_FOUND_PATTERNS = ["SUBSCRIBER INFORMATION", "MOBILE COUNTRY CODE"]
```

## Architecture

### Separation of Concerns

1. **Configuration** (`config.py`)
   - All settings in one place
   - Easy to modify without touching code

2. **MML Client** (`mml_client.py`)
   - Handles SSH connections and MML communication
   - Reusable for any MML commands
   - Context manager support

3. **Subscriber Checker** (`subscriber_checker.py`)
   - Business logic for subscriber lookup
   - Pattern matching and result analysis
   - Independent of transport layer

4. **Report Generator** (`report_generator.py`)
   - Creates summary reports
   - Can be extended for different formats

5. **Logging** (`logging_config.py`)
   - Centralized logging configuration
   - Colored terminal output
   - Plain text file output

6. **Utilities** (`utils/`)
   - Reusable helper functions
   - Text processing, colors, etc.

## Extending the Tool

### Add New MML Commands
1. Define command sequence in `config.py`
2. Create method in `SubscriberChecker` or new checker class
3. Call from main flow

### Add New Server Types
1. Subclass `MMLClient` for specific behavior
2. Override connection or command execution methods

### Custom Reports
1. Extend `ReportGenerator` class
2. Add methods for different report formats (JSON, CSV, etc.)

## Troubleshooting

### Connection Issues
- Check server IP and credentials in `config.py`
- Verify network connectivity
- Check SSH key policies

### Output Not Captured
- Increase `READ_TIMEOUT` in `config.py`
- Check MML command syntax
- Review server logs for errors

### Backspace Characters in Logs
- The tool automatically processes backspace characters
- If still seeing issues, check `process_backspaces()` in `text_processing.py`

## License

Internal tool - All rights reserved
#!/usr/bin/env python3
"""
config.py
Configuration settings for the MSS automation tool.
"""

import os

# ---- Server Configuration ----
SERVERS = [
    {"name": "MSSTB4", "ip": "172.29.108.42", "user": "AUTOMA", "password": "AUTOMA-1"},
    {"name": "MSSTB5", "ip": "172.29.108.106", "user": "AUTOMA", "password": "AUTOMA-1"},
]

# ---- Timeout Settings ----
READ_TIMEOUT = 6.0  # Seconds to wait for command output
CONNECT_TIMEOUT = 10  # Seconds to wait for SSH connection
SHELL_TIMEOUT = 2.0  # Seconds for shell channel timeout

# ---- Logging Configuration ----
LOG_DIR = "logs"
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"
LOG_FORMAT_CONSOLE = "%(asctime)s %(levelname)s %(message)s"
LOG_FORMAT_FILE = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---- MML Command Configuration ----
MML_COMMANDS = {
    "CHECK_SUBSCRIBER": [
        "ZMVO",
        "MSISDN={msisdn}",
        ";"
    ]
}

# ---- Detection Patterns ----
SUBSCRIBER_NOT_FOUND_PATTERNS = ["UNKNOWN SUBSCRIBER", "DX ERROR", "COMMAND EXECUTION FAILED"]
SUBSCRIBER_FOUND_PATTERNS = ["SUBSCRIBER INFORMATION", "MOBILE COUNTRY CODE"]

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

