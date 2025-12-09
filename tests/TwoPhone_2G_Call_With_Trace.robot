*** Settings ***
Documentation       Two-Phone 2G Call with Anritsu Trace Collection
...
...                 SCENARIO:
...                 Automated 2G call test between two STF-managed Android devices
...                 with complete network trace capture including Location Update procedure.
...
...                 TEST STEPS:
...                 1. Auto-select two available STF devices
...                 2. Connect both via STF (serial → IP:PORT)
...                 3. Switch Phone A to 2G network (triggers Location Update)
...                 4. Phone A calls Phone B
...                 5. Phone B answers after 5 seconds of ringing
...                 6. Call lasts 30 seconds and ends
...                 7. Collect Anritsu PCAP trace (includes Location Update + Call)
...
...                 VALIDATION:
...                 - Location Update Procedure (BSSAP/MAP)
...                 - MO Call Setup and Release (BSSAP)
...                 - MT Call Setup and Release (BSSAP)
...
...                 PCAP ANALYSIS:
...                 Use: python utils/pcap_validator.py tc_output_dir/<pcap_file>
...
...                 This test orchestrates the Python function from custom_call.py
...                 and collects network traces via Anritsu for validation.

Library             ../custom_call.py
Library             DateTime
Library             BuiltIn
Library             Collections
Library             OperatingSystem
Library             String

Variables           ../configs/SERVERS.yaml
Variables           ../configs/locators.yaml

Library             ../Anritsu/AnritsuServer.py    ${ANRITSU}    WITH NAME    AnritsuLib


*** Variables ***
${START_TIME}       ${EMPTY}
${END_TIME}         ${EMPTY}
${DURATION}         ${EMPTY}
${ANRITSU_TEMPLATE}    Easy_Subscriber_Search    # Default Anritsu trace template
${TC_OUTPUT_DIR}    ${CURDIR}/../tc_output_dir
${TRACE_ENABLED}    ${TRUE}    # Set to ${FALSE} to disable Anritsu trace collection


*** Keywords ***
Collect Anritsu Trace
    [Documentation]    Initialize Anritsu driver and collect PCAP trace for the call session
    [Arguments]    ${start_time}    ${end_time}    ${phone_a_msisdn}    ${phone_b_msisdn}    ${phone_a_imsi}    ${phone_b_imsi}

    Log To Console    \n${\n}========== ANRITSU TRACE COLLECTION ==========
    Log To Console    Template: ${ANRITSU_TEMPLATE}
    Log To Console    Time Range (with milliseconds): ${start_time} to ${end_time}
    Log To Console    Start Time: [${start_time}] (Length: ${start_time.__len__()})
    Log To Console    End Time: [${end_time}] (Length: ${end_time.__len__()})
    Log To Console    Phone A MSISDN: ${phone_a_msisdn}
    Log To Console    Phone B MSISDN: ${phone_b_msisdn}
    Log To Console    Output Dir: ${TC_OUTPUT_DIR}

    # Create output directory
    Create Directory    ${TC_OUTPUT_DIR}


    # Prepare device info structure
    ${device_1_sim}=    Create Dictionary
    ...    sim_MSISDN=${phone_a_msisdn}
    ...    sim_IMSI=${phone_a_imsi}
    ...    sim_Calling_Number=${phone_a_msisdn}
    ...    sim_Calling_Number_0=${phone_a_msisdn}

    ${device_2_sim}=    Create Dictionary
    ...    sim_MSISDN=${phone_b_msisdn}
    ...    sim_IMSI=${phone_b_imsi}
    ...    sim_Calling_Number=${phone_b_msisdn}
    ...    sim_Calling_Number_0=${phone_b_msisdn}

    ${device_1_sims}=    Create Dictionary    sim_slot_1=${device_1_sim}
    ${device_2_sims}=    Create Dictionary    sim_slot_1=${device_2_sim}

    ${device_1}=    Create Dictionary    sims=${device_1_sims}
    ${device_2}=    Create Dictionary    sims=${device_2_sims}

    ${devices_info}=    Create Dictionary    device_1=${device_1}    device_2=${device_2}


    # Step 1: Initialize Anritsu driver
    Log To Console    \n[1/3] Initializing Anritsu driver...
    ${init_result}=    AnritsuLib.initialize_anritsu_driver    CustomCall    ${TC_OUTPUT_DIR}
    Should Be True    ${init_result}    Anritsu driver initialization failed
    Log To Console    ✓ Anritsu driver initialized successfully

    # Step 2: Start OESearch trace
    Log To Console    \n[2/3] Starting Anritsu OESearch trace...
    ${oesearch_result}=    AnritsuLib.start_oesearch_NewUi
    ...    ${Oesearch_NewUi}
    ...    ${start_time}
    ...    ${end_time}
    ...    ${devices_info}
    ...    ${ANRITSU_TEMPLATE}
    ...    ${FALSE}
    Should Be True    ${oesearch_result}    OESearch trace initiation failed
    Log To Console    ✓ Anritsu trace initiated successfully

    # Step 3: Wait and download PCAP
    Log To Console    \n[3/3] Waiting for trace to complete and downloading PCAP...
    Log To Console    This may take several minutes...
    ${download_result}=    AnritsuLib.download_oesearch_pcap_NewUi    ${Oesearch_pcap_download_NewUi}
    Should Be True    ${download_result}    PCAP download failed
    Log To Console    ✓ PCAP downloaded successfully

    # Get PCAP file path
    ${pcap_path}=    AnritsuLib.get_pcap_path    ${ANRITSU_TEMPLATE}
    Log To Console    PCAP file location: ${pcap_path}
    Log    PCAP file downloaded to: ${pcap_path}

    Log To Console    =============================================

    RETURN    ${pcap_path}

Format Anritsu Timestamp
    [Documentation]    Convert Robot Framework timestamp to Anritsu format (YYYY-MM-DD HH:MM:SS.MSS)
    [Arguments]    ${rf_timestamp}

    # Parse the timestamp: "2025-12-05 09:51:00.000"
    # Keep the format as-is with milliseconds: YYYY-MM-DD HH:MM:SS.MSS
    ${anritsu_timestamp}=    Set Variable    ${rf_timestamp}

    RETURN    ${anritsu_timestamp}

Collect And Process Anritsu Trace
    [Documentation]    Extract device info and collect Anritsu trace
    [Arguments]    ${result}    ${start_time}    ${end_time}

    Log To Console    \n${\n}Starting Anritsu trace collection...
    Log To Console    Using adjusted times for Anritsu trace:
    Log To Console    - Start Time (Adjusted): ${start_time}
    Log To Console    - End Time (Adjusted): ${end_time}

    # Extract device information from result dictionary
    ${phone_a_msisdn}=    Get From Dictionary    ${result}    phone_a_msisdn
    ${phone_b_msisdn}=    Get From Dictionary    ${result}    phone_b_msisdn
    ${phone_a_serial}=    Get From Dictionary    ${result}    phone_a_serial
    ${phone_b_serial}=    Get From Dictionary    ${result}    phone_b_serial
    ${phone_a_imsi}=    Get From Dictionary    ${result}    phone_a_imsi
    ${phone_b_imsi}=    Get From Dictionary    ${result}    phone_b_imsi

    # Convert timestamps to Anritsu format
    ${anritsu_start}=    Format Anritsu Timestamp    ${start_time}
    ${anritsu_end}=    Format Anritsu Timestamp    ${end_time}

    Log To Console    Converted to Anritsu format:
    Log To Console    - Anritsu Start: ${anritsu_start}
    Log To Console    - Anritsu End: ${anritsu_end}

    # Log device information
    Log To Console    Phone A: ${phone_a_msisdn} (Serial: ${phone_a_serial}, IMSI: ${phone_a_imsi})
    Log To Console    Phone B: ${phone_b_msisdn} (Serial: ${phone_b_serial}, IMSI: ${phone_b_imsi})

    # Collect Anritsu trace
    ${pcap_path}=    Collect Anritsu Trace    ${anritsu_start}    ${anritsu_end}    ${phone_a_msisdn}    ${phone_b_msisdn}    ${phone_a_imsi}    ${phone_b_imsi}

    Log To Console    Anritsu trace collection completed
    Log    PCAP file saved to: ${pcap_path}

    RETURN    ${pcap_path}


*** Test Cases ***
2G Call Between Two Phones With Location Update Trace
    [Documentation]    Execute automated 2G call scenario with complete network trace
    ...
    ...                This test captures the complete call flow including:
    ...                - Location Update procedure (when switching to 2G)
    ...                - Call setup (BSSAP SETUP)
    ...                - Call connection and duration (30 seconds)
    ...                - Call release (normal clearing from A-party)
    ...
    ...                Trace times are captured AFTER airplane mode toggle to ensure
    ...                the Location Update procedure is included in the PCAP.
    [Tags]    2G    BSSAP    call-test    location-update    anritsu-trace    stf

    Log To Console    \n${\n}========== STARTING CALL SCENARIO ==========
    Log To Console    Trace times will be captured AFTER 2G switch (airplane mode toggle)
    Log To Console    This ensures Location Update procedure is included in PCAP
    Log To Console    ============================================

    # Run the entire custom scenario from the Python module
    # Python function now returns trace_start_time and trace_end_time
    ${result}=    Run Custom Scenario

    # Extract trace times from Python result (captured after airplane mode toggle)
    ${START_TIME}=    Get From Dictionary    ${result}    trace_start_time
    ${END_TIME}=    Get From Dictionary    ${result}    trace_end_time

    Log To Console    \n${\n}========== TRACE TIME WINDOW ==========
    Log To Console    Trace Start Time: ${START_TIME}
    Log To Console    Trace End Time: ${END_TIME}
    Log To Console    (Captured after 2G switch - includes Location Update)
    Log To Console    ========================================

    Log    Trace Start Time: ${START_TIME}
    Log    Trace End Time: ${END_TIME}
    Set Suite Variable    ${START_TIME}
    Set Suite Variable    ${END_TIME}

    # Calculate duration
    ${DURATION}=    Subtract Date From Date    ${END_TIME}    ${START_TIME}
    Log To Console    Trace Duration: ${DURATION} seconds
    Log    Trace Duration: ${DURATION} seconds
    Set Suite Variable    ${DURATION}

    # Extract success status and device info from result
    ${success}=    Get From Dictionary    ${result}    success

    # Log call scenario summary
    ${STATUS}=    Set Variable If    ${success}    PASS    FAIL
    Log To Console    \n${\n}========== CALL SCENARIO SUMMARY ==========
    Log To Console    Start Time: ${START_TIME}
    Log To Console    End Time: ${END_TIME}
    Log To Console    Duration: ${DURATION} seconds
    Log To Console    Status: ${STATUS}
    Log To Console    ===========================================

    # Check if call scenario was successful
    Should Be True    ${success}    Custom call scenario failed

    # If trace is enabled and call was successful, collect Anritsu trace
    Run Keyword If    ${TRACE_ENABLED} and ${success}    Collect And Process Anritsu Trace    ${result}    ${START_TIME}    ${END_TIME}

    # Final summary
    ${TRACE_STATUS}=    Set Variable If    ${TRACE_ENABLED}    ENABLED    DISABLED

    Log To Console    \n${\n}========== FINAL TEST SUMMARY ==========
    Log To Console    Call Status: ${STATUS}
    Log To Console    Trace Collection: ${TRACE_STATUS}
    Log To Console    Total Duration: ${DURATION} seconds
    Log To Console    ========================================



