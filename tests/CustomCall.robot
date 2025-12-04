*** Settings ***
Documentation       Custom Call Automation Test Suite
...                 Automated phone call scenario using STF devices:
...                 1. Auto-select two available STF devices
...                 2. Connect both via STF (serial → IP:PORT)
...                 3. Switch Phone A to 2G
...                 4. Phone A calls Phone B
...                 5. Phone B answers after 5 seconds of ringing
...                 6. Call lasts 30 seconds and ends

# Config files
Variables           ../configs/config.py

# Resource files
Resource            ../resources/PhoneAutomation.resource

# Python libraries
Library             Collections
Library             BuiltIn


*** Variables ***
${RING_WAIT_SECONDS}        5
${CALL_DURATION}            30
${NETWORK_TYPE}             2G


*** Test Cases ***
Custom Call Scenario - Two STF Devices
    [Documentation]    Execute automated call scenario with two auto-selected STF devices
    [Tags]    phone-automation    stf    call-test    2G

    # Print scenario header
    Print Scenario Header


    # Variables for cleanup
    Set Test Variable    ${PHONE_A_SERIAL}    ${None}
    Set Test Variable    ${PHONE_B_SERIAL}    ${None}
    Set Test Variable    ${STF_MANAGER}       ${None}

    TRY
        # Initialize STF
        ${stf_base_url}=    Get Variable Value    ${STF_CONFIG['base_url']}
        ${stf_user_auth}=   Get Variable Value    ${STF_CONFIG['user_auth']}
        ${STF_MANAGER}=     Initialize STF Manager    ${stf_base_url}    ${stf_user_auth}
        Set Test Variable    ${STF_MANAGER}

        # Select two available devices
        ${device_a}    ${device_b}=    Get Two Available STF Devices    ${STF_MANAGER}
        ${PHONE_A_SERIAL}=    Set Variable    ${device_a['serial']}
        ${PHONE_B_SERIAL}=    Set Variable    ${device_b['serial']}
        Set Test Variable    ${PHONE_A_SERIAL}
        Set Test Variable    ${PHONE_B_SERIAL}

        # Determine MSISDNs
        Log To Console    \n============================================================
        Log To Console    STEP 0: Determining MSISDNs for the devices...
        Log To Console    ============================================================
        ${phone_a_msisdn}=    Get Or Prompt For MSISDN    Phone A    ${device_a}
        ${phone_b_msisdn}=    Get Or Prompt For MSISDN    Phone B    ${device_b}

        # Use fallback MSISDNs if extraction failed
        ${phone_a_msisdn}=    Set Variable If    '${phone_a_msisdn}' == 'None'    +4915900103141    ${phone_a_msisdn}
        ${phone_b_msisdn}=    Set Variable If    '${phone_b_msisdn}' == 'None'    +4915781993213    ${phone_b_msisdn}

        Log To Console    Using MSISDN for Phone A: ${phone_a_msisdn}
        Log To Console    Using MSISDN for Phone B: ${phone_b_msisdn}

        # Connect devices via STF
        Log To Console    \n============================================================
        Log To Console    STEP 0: Connecting selected STF devices via serial...
        Log To Console    ============================================================
        ${phone_a_ip_port}=    Connect Device Via STF    ${STF_MANAGER}    ${PHONE_A_SERIAL}
        ${phone_b_ip_port}=    Connect Device Via STF    ${STF_MANAGER}    ${PHONE_B_SERIAL}

        # Build phones dictionary
        ${phone_a_dict}=    Create Dictionary
        ...    name=STF-${PHONE_A_SERIAL}
        ...    msisdn=${phone_a_msisdn}
        ...    ip_port=${phone_a_ip_port}
        ...    serial=${PHONE_A_SERIAL}

        ${phone_b_dict}=    Create Dictionary
        ...    name=STF-${PHONE_B_SERIAL}
        ...    msisdn=${phone_b_msisdn}
        ...    ip_port=${phone_b_ip_port}
        ...    serial=${PHONE_B_SERIAL}

        ${phones_dict}=    Create Dictionary
        ...    phoneA=${phone_a_dict}
        ...    phoneB=${phone_b_dict}

        # Initialize automation
        ${automation}=    Initialize Phone Automation    ${phones_dict}    ${STF_CONFIG}

        Log To Console    Phone A: ${phone_a_msisdn} @ ${phone_a_ip_port} (serial ${PHONE_A_SERIAL})
        Log To Console    Phone B: ${phone_b_msisdn} @ ${phone_b_ip_port} (serial ${PHONE_B_SERIAL})

        # Step 1: Connect to both phones
        Log To Console    \n============================================================
        Log To Console    STEP 1: Connecting to both phones (via ADB)...
        Log To Console    ============================================================
        Connect Phone Via ADB    ${automation}    ${phone_a_ip_port}    Phone A (${phone_a_msisdn})
        Connect Phone Via ADB    ${automation}    ${phone_b_ip_port}    Phone B (${phone_b_msisdn})
        Log To Console    ✓ Both phones connected successfully

        # Step 2: Switch Phone A to 2G
        Log To Console    \n============================================================
        Log To Console    STEP 2: Switching Phone A (${phone_a_msisdn}) to ${NETWORK_TYPE}...
        Log To Console    ============================================================
        Switch Phone To Network    ${automation}    ${phone_a_ip_port}    ${NETWORK_TYPE}    ${phone_a_msisdn}

        # Step 3: Phone A calls Phone B
        Log To Console    \n============================================================
        Log To Console    STEP 3: Phone A (${phone_a_msisdn}) calling Phone B (${phone_b_msisdn})...
        Log To Console    ============================================================
        Initiate Call    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}    ${phone_b_msisdn}

        # Step 4: Wait for Phone B to ring, then answer after 5 seconds
        Log To Console    \n============================================================
        Log To Console    STEP 4: Waiting for Phone B to ring...
        Log To Console    ============================================================
        Wait For Ring And Answer    ${automation}    ${phone_b_ip_port}    ${phone_b_msisdn}    ${RING_WAIT_SECONDS}

        # Wait for call connection
        Wait For Call Connection    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}    ${phone_b_ip_port}    ${phone_b_msisdn}

        # Step 5: Call lasts 30 seconds then ends
        Log To Console    \n============================================================
        Log To Console    STEP 5: Call in progress...
        Log To Console    ============================================================
        Maintain Call Duration    ${CALL_DURATION}

        End Call    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}

        # Print success summary
        Print Scenario Summary

    EXCEPT    AS    ${error}
        Log To Console    \n✗ Error during scenario execution: ${error}
        Fail    Scenario failed: ${error}

    FINALLY
        # Cleanup: Disconnect STF devices
        Run Keyword If    '${STF_MANAGER}' != 'None' and '${PHONE_A_SERIAL}' != 'None'
        ...    Disconnect Device From STF    ${STF_MANAGER}    ${PHONE_A_SERIAL}
        Run Keyword If    '${STF_MANAGER}' != 'None' and '${PHONE_B_SERIAL}' != 'None'
        ...    Disconnect Device From STF    ${STF_MANAGER}    ${PHONE_B_SERIAL}
    END


Custom Call Scenario - Specific Network Types
    [Documentation]    Execute call scenario with configurable network type
    [Tags]    phone-automation    stf    call-test    network-switch
    [Template]    Execute Call Scenario With Network Type

    2G
    3G
    4G


*** Keywords ***
Execute Call Scenario With Network Type
    [Documentation]    Template keyword to run scenario with different network types
    [Arguments]    ${network_type}

    Print Scenario Header


    Set Test Variable    ${PHONE_A_SERIAL}    ${None}
    Set Test Variable    ${PHONE_B_SERIAL}    ${None}
    Set Test Variable    ${STF_MANAGER}       ${None}

    TRY
        # Initialize and setup
        ${stf_base_url}=    Get Variable Value    ${STF_CONFIG['base_url']}
        ${stf_user_auth}=   Get Variable Value    ${STF_CONFIG['user_auth']}
        ${STF_MANAGER}=     Initialize STF Manager    ${stf_base_url}    ${stf_user_auth}
        Set Test Variable    ${STF_MANAGER}

        ${device_a}    ${device_b}=    Get Two Available STF Devices    ${STF_MANAGER}
        ${PHONE_A_SERIAL}=    Set Variable    ${device_a['serial']}
        ${PHONE_B_SERIAL}=    Set Variable    ${device_b['serial']}
        Set Test Variable    ${PHONE_A_SERIAL}
        Set Test Variable    ${PHONE_B_SERIAL}

        ${phone_a_msisdn}=    Get Or Prompt For MSISDN    Phone A    ${device_a}
        ${phone_b_msisdn}=    Get Or Prompt For MSISDN    Phone B    ${device_b}

        # Use fallback MSISDNs if extraction failed
        ${phone_a_msisdn}=    Set Variable If    '${phone_a_msisdn}' == 'None'    +4915900103141    ${phone_a_msisdn}
        ${phone_b_msisdn}=    Set Variable If    '${phone_b_msisdn}' == 'None'    +4915781993213    ${phone_b_msisdn}

        ${phone_a_ip_port}=    Connect Device Via STF    ${STF_MANAGER}    ${PHONE_A_SERIAL}
        ${phone_b_ip_port}=    Connect Device Via STF    ${STF_MANAGER}    ${PHONE_B_SERIAL}

        ${phone_a_dict}=    Create Dictionary    name=STF-${PHONE_A_SERIAL}    msisdn=${phone_a_msisdn}    ip_port=${phone_a_ip_port}    serial=${PHONE_A_SERIAL}
        ${phone_b_dict}=    Create Dictionary    name=STF-${PHONE_B_SERIAL}    msisdn=${phone_b_msisdn}    ip_port=${phone_b_ip_port}    serial=${PHONE_B_SERIAL}
        ${phones_dict}=     Create Dictionary    phoneA=${phone_a_dict}    phoneB=${phone_b_dict}

        ${automation}=    Initialize Phone Automation    ${phones_dict}    ${STF_CONFIG}

        # Execute scenario with specified network type
        Connect Phone Via ADB    ${automation}    ${phone_a_ip_port}    Phone A (${phone_a_msisdn})
        Connect Phone Via ADB    ${automation}    ${phone_b_ip_port}    Phone B (${phone_b_msisdn})

        Switch Phone To Network    ${automation}    ${phone_a_ip_port}    ${network_type}    ${phone_a_msisdn}

        Initiate Call    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}    ${phone_b_msisdn}
        Wait For Ring And Answer    ${automation}    ${phone_b_ip_port}    ${phone_b_msisdn}    ${RING_WAIT_SECONDS}
        Wait For Call Connection    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}    ${phone_b_ip_port}    ${phone_b_msisdn}

        Maintain Call Duration    ${CALL_DURATION}
        End Call    ${automation}    ${phone_a_ip_port}    ${phone_a_msisdn}

        Print Scenario Summary

    FINALLY
        Run Keyword If    '${STF_MANAGER}' != 'None' and '${PHONE_A_SERIAL}' != 'None'
        ...    Disconnect Device From STF    ${STF_MANAGER}    ${PHONE_A_SERIAL}
        Run Keyword If    '${STF_MANAGER}' != 'None' and '${PHONE_B_SERIAL}' != 'None'
        ...    Disconnect Device From STF    ${STF_MANAGER}    ${PHONE_B_SERIAL}
    END

