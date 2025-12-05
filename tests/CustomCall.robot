*** Settings ***
Documentation       Custom Call Automation Test Suite
...                 Automated phone call scenario using STF devices:
...                 1. Auto-select two available STF devices
...                 2. Connect both via STF (serial → IP:PORT)
...                 3. Switch Phone A to 2G
...                 4. Phone A calls Phone B
...                 5. Phone B answers after 5 seconds of ringing
...                 6. Call lasts 30 seconds and ends
...                 7. Collect Anritsu trace (PCAP)
...
...                 This test simply calls the Python function from custom_call.py
...                 which contains all the scenario logic.

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
${TC_OUTPUT_DIR}    ${CURDIR}/../tc_output_dir/CustomCall_${START_TIME}
${TRACE_ENABLED}    ${TRUE}    # Set to ${FALSE} to disable Anritsu trace collection


*** Keywords ***
Collect Anritsu Trace
    [Documentation]    Initialize Anritsu driver and collect PCAP trace for the call session
    [Arguments]    ${start_time}    ${end_time}    ${phone_a_msisdn}    ${phone_b_msisdn}    ${phone_a_imsi}    ${phone_b_imsi}

    Log To Console    \n${\n}========== ANRITSU TRACE COLLECTION ==========
    Log To Console    Template: ${ANRITSU_TEMPLATE}
    Log To Console    Time Range: ${start_time} to ${end_time}
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

    # Save input data to JSON file BEFORE starting Anritsu trace
    ${json_file}=    Set Variable    ${TC_OUTPUT_DIR}/anritsu_input_data.json
    ${current_time}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    ${json_content}=    Catenate    SEPARATOR=\n
    ...    {
    ...    ${SPACE*2}"metadata": {
    ...    ${SPACE*4}"test_case": "CustomCall",
    ...    ${SPACE*4}"timestamp": "${current_time}",
    ...    ${SPACE*4}"template": "${ANRITSU_TEMPLATE}",
    ...    ${SPACE*4}"output_directory": "${TC_OUTPUT_DIR}"
    ...    ${SPACE*2}},
    ...    ${SPACE*2}"trace_parameters": {
    ...    ${SPACE*4}"start_time": "${start_time}",
    ...    ${SPACE*4}"end_time": "${end_time}",
    ...    ${SPACE*4}"template": "${ANRITSU_TEMPLATE}",
    ...    ${SPACE*4}"is_fixed_call": false
    ...    ${SPACE*2}},
    ...    ${SPACE*2}"device_information": {
    ...    ${SPACE*4}"phone_a": {
    ...    ${SPACE*6}"msisdn": "${phone_a_msisdn}",
    ...    ${SPACE*6}"imsi": "${phone_a_imsi}"
    ...    ${SPACE*4}},
    ...    ${SPACE*4}"phone_b": {
    ...    ${SPACE*6}"msisdn": "${phone_b_msisdn}",
    ...    ${SPACE*6}"imsi": "${phone_b_imsi}"
    ...    ${SPACE*4}}
    ...    ${SPACE*2}},
    ...    ${SPACE*2}"devices_info_structure": {
    ...    ${SPACE*4}"device_1": {
    ...    ${SPACE*6}"sims": {
    ...    ${SPACE*8}"sim_slot_1": {
    ...    ${SPACE*10}"sim_MSISDN": "${phone_a_msisdn}",
    ...    ${SPACE*10}"sim_IMSI": "${phone_a_imsi}",
    ...    ${SPACE*10}"sim_Calling_Number": "${phone_a_msisdn}",
    ...    ${SPACE*10}"sim_Calling_Number_0": "${phone_a_msisdn}"
    ...    ${SPACE*8}}
    ...    ${SPACE*6}}
    ...    ${SPACE*4}},
    ...    ${SPACE*4}"device_2": {
    ...    ${SPACE*6}"sims": {
    ...    ${SPACE*8}"sim_slot_1": {
    ...    ${SPACE*10}"sim_MSISDN": "${phone_b_msisdn}",
    ...    ${SPACE*10}"sim_IMSI": "${phone_b_imsi}",
    ...    ${SPACE*10}"sim_Calling_Number": "${phone_b_msisdn}",
    ...    ${SPACE*10}"sim_Calling_Number_0": "${phone_b_msisdn}"
    ...    ${SPACE*8}}
    ...    ${SPACE*6}}
    ...    ${SPACE*4}}
    ...    ${SPACE*2}},
    ...    ${SPACE*2}"anritsu_server_config": {
    ...    ${SPACE*4}"server_ip": "${ANRITSU}[ANRITSU_SERVER_IP]",
    ...    ${SPACE*4}"username": "${ANRITSU}[ANRITSU_SERVER_USERNAME]"
    ...    ${SPACE*2}}
    ...    }

    Create File    ${json_file}    ${json_content}
    Log To Console    \n📄 Anritsu input data saved to: ${json_file}
    Log    Anritsu input data saved to: ${json_file}

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
    [Documentation]    Convert Robot Framework timestamp to Anritsu format (MM/DD/YYYY hh:mm:ss)
    [Arguments]    ${rf_timestamp}

    # Parse the timestamp: "2024-12-04 14:30:45.123456"
    ${date_part}    ${time_part}=    Split String    ${rf_timestamp}    ${SPACE}    max_split=1
    ${year}    ${month}    ${day}=    Split String    ${date_part}    -
    ${time_only}=    Fetch From Left    ${time_part}    .

    # Format as MM/DD/YYYY HH:MM:SS
    ${anritsu_timestamp}=    Set Variable    ${month}/${day}/${year} ${time_only}

    RETURN    ${anritsu_timestamp}

Collect And Process Anritsu Trace
    [Documentation]    Extract device info and collect Anritsu trace
    [Arguments]    ${result}    ${start_time}    ${end_time}

    Log To Console    \n${\n}Starting Anritsu trace collection...

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

    # Log device information
    Log To Console    Phone A: ${phone_a_msisdn} (Serial: ${phone_a_serial}, IMSI: ${phone_a_imsi})
    Log To Console    Phone B: ${phone_b_msisdn} (Serial: ${phone_b_serial}, IMSI: ${phone_b_imsi})

    # Collect Anritsu trace
    ${pcap_path}=    Collect Anritsu Trace    ${anritsu_start}    ${anritsu_end}    ${phone_a_msisdn}    ${phone_b_msisdn}    ${phone_a_imsi}    ${phone_b_imsi}

    Log To Console    Anritsu trace collection completed
    Log    PCAP file saved to: ${pcap_path}

    RETURN    ${pcap_path}


*** Test Cases ***
Custom Call Scenario - Two STF Devices
    [Documentation]    Execute automated call scenario with two auto-selected STF devices
    ...                Directly calls the Python run_custom_scenario() function.
    [Tags]    phone-automation    stf    call-test    2G

    # Capture start time
    ${START_TIME_RAW}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S.%f
    ${START_TIME_ORIGINAL}=    Set Variable    ${START_TIME_RAW[:23]}
    # Round down to previous minute (set seconds to 00)
    ${START_TIME}=    Set Variable    ${START_TIME_ORIGINAL[:17]}00
    Log To Console    \n${\n}Test Start Time (Original): ${START_TIME_ORIGINAL}
    Log To Console    Test Start Time (Adjusted): ${START_TIME}
    Log    Test Start Time (Original): ${START_TIME_ORIGINAL}
    Log    Test Start Time (Adjusted): ${START_TIME}
    Set Suite Variable    ${START_TIME}
    
    # Update TC_OUTPUT_DIR with actual timestamp
    ${TC_OUTPUT_DIR}=    Set Variable    ${CURDIR}/../tc_output_dir/CustomCall_${START_TIME_ORIGINAL}
    Set Suite Variable    ${TC_OUTPUT_DIR}

    # Run the entire custom scenario from the Python module
    ${result}=    Run Custom Scenario

    # Capture end time
    ${END_TIME_RAW}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S.%f
    ${END_TIME_ORIGINAL}=    Set Variable    ${END_TIME_RAW[:23]}
    # Round up to next minute (set seconds to 00 and add 1 minute)
    ${END_TIME_ROUNDED}=    Add Time To Date    ${END_TIME_ORIGINAL}    1 minute    result_format=%Y-%m-%d %H:%M:%S
    ${END_TIME}=    Set Variable    ${END_TIME_ROUNDED[:17]}00
    Log To Console    Test End Time (Original): ${END_TIME_ORIGINAL}
    Log To Console    Test End Time (Adjusted): ${END_TIME}
    Log    Test End Time (Original): ${END_TIME_ORIGINAL}
    Log    Test End Time (Adjusted): ${END_TIME}
    Set Suite Variable    ${END_TIME}

    # Calculate duration
    ${DURATION}=    Subtract Date From Date    ${END_TIME}    ${START_TIME}
    Log To Console    Test Duration: ${DURATION} seconds
    Log    Test Duration: ${DURATION} seconds
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

