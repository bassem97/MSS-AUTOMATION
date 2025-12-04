*** Settings ***
Documentation       Custom Call Automation Test Suite
...                 Automated phone call scenario using STF devices:
...                 1. Auto-select two available STF devices
...                 2. Connect both via STF (serial → IP:PORT)
...                 3. Switch Phone A to 2G
...                 4. Phone A calls Phone B
...                 5. Phone B answers after 5 seconds of ringing
...                 6. Call lasts 30 seconds and ends
...
...                 This test simply calls the Python function from custom_call.py
...                 which contains all the scenario logic.

Library             ../custom_call.py


*** Test Cases ***
Custom Call Scenario - Two STF Devices
    [Documentation]    Execute automated call scenario with two auto-selected STF devices
    ...                Directly calls the Python run_custom_scenario() function.
    [Tags]    phone-automation    stf    call-test    2G

    # Run the entire custom scenario from the Python module
    ${success}=    Run Custom Scenario

    # Check result
    Should Be True    ${success}    Custom call scenario failed

