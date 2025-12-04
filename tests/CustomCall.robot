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
Library             DateTime
Library             BuiltIn


*** Variables ***
${START_TIME}       ${EMPTY}
${END_TIME}         ${EMPTY}
${DURATION}         ${EMPTY}


*** Test Cases ***
Custom Call Scenario - Two STF Devices
    [Documentation]    Execute automated call scenario with two auto-selected STF devices
    ...                Directly calls the Python run_custom_scenario() function.
    [Tags]    phone-automation    stf    call-test    2G

    # Capture start time
    ${START_TIME}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S.%f
    Log To Console    \n${\n}Test Start Time: ${START_TIME}
    Log    Test Start Time: ${START_TIME}
    Set Suite Variable    ${START_TIME}

    # Run the entire custom scenario from the Python module
    ${success}=    Run Custom Scenario

    # Capture end time
    ${END_TIME}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S.%f
    Log To Console    Test End Time: ${END_TIME}
    Log    Test End Time: ${END_TIME}
    Set Suite Variable    ${END_TIME}

    # Calculate duration
    ${DURATION}=    Subtract Date From Date    ${END_TIME}    ${START_TIME}
    Log To Console    Test Duration: ${DURATION} seconds
    Log    Test Duration: ${DURATION} seconds
    Set Suite Variable    ${DURATION}

    # Determine status
    ${STATUS}=    Set Variable If    ${success}    PASS    FAIL

    # Log summary
    Log To Console    \n${\n}========== TEST SUMMARY ==========
    Log To Console    Start Time: ${START_TIME}
    Log To Console    End Time: ${END_TIME}
    Log To Console    Duration: ${DURATION} seconds
    Log To Console    Status: ${STATUS}
    Log To Console    ==================================

    # Check result
    Should Be True    ${success}    Custom call scenario failed

