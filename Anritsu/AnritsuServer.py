"""
    This module logins to CNOM server and can start and stop the UE trace for a given subscriber.
"""
import tarfile
import pexpect
import os
import datetime
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from seleniumfunctions import eleclick, sendkeys, senddirc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import tempfile
import glob


class AnritsuServer:
    """
         This class has methods that logins to cnom server returns the web driver for further scrapping.
                Args:
                        cnom_ip (str): IP address of the CNOM server.
                        cnom_port (int): PORT of the CNOM server.
                        cnom_username (str): Username of the CNOM server.
                        cnom_password (str): Password of the CNOM server.

                Functions:
                        Initialize_driver - Initializes the webdriver and returns driver object to calling function.
                        Build_TC_dir - Builds the name of testcase using the current time stamp and the testcase name.

    """

    def __init__(self, anritsu_conn_params):
        """
            A constructor to build a connection with the cnom server.
            Args:
                cnom_ip (str): IP address of the cnom.
                cnom_port (int): PORT of the cnom.
                cnom_username (str): Username of the cnom.
                cnom_password (str): Password of the cnom.
        """

        self.base_url = f"https://{anritsu_conn_params['ANRITSU_SERVER_IP']}/"
        self.anritsu_username = anritsu_conn_params['ANRITSU_SERVER_USERNAME']
        self.anritsu_password = anritsu_conn_params['ANRITSU_SERVER_PASSWORD']

    def initialize_anritsu_driver(self, testcase_name, testcase_dir):
        """
        Initializes the Chrome WebDriver with specified options and logs into the Anritsu web interface.

        :param testcase_name: Used for naming/logging purposes (not used in current logic).
        :param testcase_dir: Directory path for saving downloaded PCAP files.
        :return: True if initialization and login are successful.
        """

        # Set up Chrome options
        temp_profile = tempfile.mkdtemp()
        self.options = webdriver.ChromeOptions()
        # self.options.add_argument('--headless')
        self.options.add_argument('--no-proxy-server')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920x1080")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument(f'--user-data-dir={temp_profile}')
        self.options.add_argument('--no-sandbox')

        # # Setting up Driver path
        # root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # driver_path = root_path + "/Resources/chromedriver-linux64/chromedriver"
        # logging.info(f"Chrom Driver Path : {driver_path} ")
        # self.service = Service(driver_path)

        driver_path = '/usr/local/bin/chromedriver'
        logging.info(f"Chrom Driver Path : {driver_path} ")
        self.service = Service(driver_path)

        # Set download directory for PCAP files
        self.pcap_download_dir = os.path.abspath(testcase_dir)
        prefs = {
            'download.default_directory': self.pcap_download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': False
        }
        self.options.add_experimental_option('prefs', prefs)
        logging.info(f"PCAP download directory set to: {self.pcap_download_dir}")

        # Initialize Chrome WebDriver with service and options
        self.driver = webdriver.Chrome(
            service=self.service, options=self.options)
        # self.driver = webdriver.Firefox(...)  # Optional: alternate Firefox setup
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Set implicit wait time
        self.driver.implicitly_wait(10)

        # Open the Anritsu EO Search application
        self.driver.get(self.base_url + 'eosearch/app')
        self.driver.maximize_window()

        # Perform login
        self.driver.find_element(By.ID, "username").send_keys(
            self.anritsu_username)
        self.driver.find_element(By.ID, "password").send_keys(
            self.anritsu_password)
        self.driver.find_element(By.ID, "loginBtn").click()

        return True

    # -------------------New GUI -------------------------------#

    def start_oesearch_NewUi(self, oesearch_path, start_time, end_time, devices, used_template, fixed_a=False):
        """
        Initiates an OE search for a subscriber using the new UI interface.

        Args:
            oesearch_path (dict): Dictionary containing XPath selectors for UI elements
            start_time (str): Start time for the search interval
            end_time (str): End time for the search interval
            devices (dict): Dictionary containing device_1 and device_2 configurations
            used_template (str): Template name to be used for the search
            fixed_a (bool): Flag to include additional calling numbers

        Returns:
            bool: True if search was initiated successfully, False otherwise
        """
        # Store device references
        self.device_1 = devices['device_1']
        self.device_2 = devices['device_2']

        logging.info("Starting OE search for subscriber")

        # Determine if the template requires network selection
        network_required_templates = {
            "GB Dialogue", "EOFINDER_OVERALL_summary"}
        requires_network = used_template in network_required_templates

        if requires_network:
            logging.info(f"Template '{used_template}' requires network access")

        try:
            # Step 1: Configure template selection
            logging.info(f"Configuring template: {used_template}")
            eleclick(
                self.driver, oesearch_path['Switch_to_new'], "Switch to new UI")
            sendkeys(
                self.driver, oesearch_path['Templete_input_field'], used_template, "Template input field")
            time.sleep(3)

            template = self.driver.find_element(
                By.CSS_SELECTOR, "li.p-listbox-item")
            template.click()
            eleclick(
                self.driver, oesearch_path['Templete_Done_button'], "Template confirmation button")
            time.sleep(3)

            # Wait for Time Interval accordion to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located(
                (By.XPATH, oesearch_path['Time_intrval_button'])))
            time.sleep(2)

            eleclick(
                self.driver, oesearch_path['Time_intrval_button'], "Time interval button")

            # Step 2: Configure time interval with enhanced method
            logging.info(
                f"Configuring time interval: {start_time} to {end_time}")
            logging.info(f"Start time type: {type(start_time)}, repr: {repr(start_time)}")
            logging.info(f"End time type: {type(end_time)}, repr: {repr(end_time)}")

            # Enhanced time input using JavaScript to ensure proper format (YYYY-MM-DD HH:MM:SS)
            for field_xpath, value in [(oesearch_path['Start_time_field'], start_time),
                                       (oesearch_path['End_time_field'], end_time)]:
                try:
                    # Wait for the field to be present
                    ele = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, field_xpath))
                    )

                    # Click to focus
                    ele.click()
                    time.sleep(0.3)

                    # Clear the field using multiple methods
                    try:
                        ele.send_keys(Keys.CONTROL + "a")
                        time.sleep(0.1)
                        ele.send_keys(Keys.DELETE)
                        time.sleep(0.1)
                        self.driver.execute_script("arguments[0].value = '';", ele)
                        time.sleep(0.1)
                    except Exception as clear_error:
                        logging.warning(f"Clear operation warning: {clear_error}")

                    # Set value using JavaScript for reliability
                    logging.info(f"Setting field value via JavaScript: '{value}' (length: {len(value)})")
                    self.driver.execute_script("arguments[0].value = arguments[1];", ele, value)

                    # Verify the value was set correctly
                    set_value = self.driver.execute_script("return arguments[0].value;", ele)
                    logging.info(f"Verification: Field value after JS set: '{set_value}'")

                    # Trigger events for JavaScript frameworks
                    self.driver.execute_script("""
                        arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                        arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                        arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));
                    """, ele)

                    time.sleep(0.5)
                    logging.info(f"Successfully set time field to: {value}")

                except Exception as e:
                    logging.error(f"Failed to set time field to {value}: {str(e)}")
                    # Fallback to original method
                    sendkeys(self.driver, field_xpath, value, "Time interval field", True)

            # Step 3: Configure filters based on template type
            if requires_network:
                # Network-based filtering (IMSI only)
                logging.info("Configuring IMSI filter for network template")
                eleclick(
                    self.driver, oesearch_path['Filter_Select_filed'], "Filter select field")
                sendkeys(
                    self.driver, oesearch_path['Search_box'], "IMSI", "Search box")
                eleclick(
                    self.driver, oesearch_path['Filter_IMSI'], "Filter IMSI")
                eleclick(
                    self.driver, oesearch_path['Dropdown_trigger'], "Filter condition dropdown")

                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                self.driver.refresh()
                logging.info("IMSI filter configured successfully")

            else:
                # Standard filtering (MSISDN, Calling/Called numbers, IMSI)
                logging.info(
                    "Configuring standard filters (MSISDN, Calling/Called numbers, IMSI)")
                eleclick(
                    self.driver, oesearch_path['Filter_Button'], "Filter button")

                # Set all filter conditions to 'contains'
                eleclick(
                    self.driver, oesearch_path['MSISDN_dropdown'], "MSISDN dropdown")
                eleclick(
                    self.driver, oesearch_path['MSISDN_contains'], "MSISDN contains condition")
                eleclick(
                    self.driver, oesearch_path['Calling_number_dropdown'], "Calling number dropdown")
                eleclick(
                    self.driver, oesearch_path['Calling_number_contains'], "Calling number contains condition")
                eleclick(
                    self.driver, oesearch_path['Called_number_dropdown'], "Called number dropdown")
                eleclick(
                    self.driver, oesearch_path['Called_number_contains'], "Called number contains condition")
                eleclick(
                    self.driver, oesearch_path['IMSI_dropdown'], "IMSI dropdown")
                eleclick(
                    self.driver, oesearch_path['IMSI_contains'], "IMSI contains condition")

                # Populate MSISDN fields
                logging.info("Populating MSISDN fields for both devices")
                sendkeys(self.driver, oesearch_path['MSISDN_field'],
                         self.device_1["sims"]["sim_slot_1"]["sim_MSISDN"] + Keys.RETURN, "MSISDN field")
                sendkeys(self.driver, oesearch_path['MSISDN_field'],
                         self.device_2["sims"]["sim_slot_1"]["sim_MSISDN"] + Keys.RETURN, "MSISDN field")

                # Populate additional fields if fixed_a is enabled
                if fixed_a:
                    logging.info(
                        "Populating additional calling numbers (fixed_a mode)")
                    sendkeys(self.driver, oesearch_path['MSISDN_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number"] + Keys.RETURN, "MSISDN field")
                    sendkeys(self.driver, oesearch_path['MSISDN_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number_0"] + Keys.RETURN, "MSISDN field")
                    sendkeys(self.driver, oesearch_path['Calling_number_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number"] + Keys.RETURN, "Calling number field")
                    sendkeys(self.driver, oesearch_path['Calling_number_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number_0"] + Keys.RETURN, "Calling number field")
                    sendkeys(self.driver, oesearch_path['Called_number_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number"] + Keys.RETURN, "Called number field")
                    sendkeys(self.driver, oesearch_path['Called_number_field'],
                             self.device_1["sims"]["sim_slot_1"]["sim_Calling_Number_0"] + Keys.RETURN, "Called number field")

                # Populate calling number fields
                logging.info("Populating calling number fields")
                sendkeys(self.driver, oesearch_path['Calling_number_field'],
                         self.device_2["sims"]["sim_slot_1"]["sim_MSISDN"] + Keys.RETURN, "Calling number field")
                sendkeys(self.driver, oesearch_path['Calling_number_field'],
                         self.device_1["sims"]["sim_slot_1"]["sim_MSISDN"] + Keys.RETURN, "Calling number field")

                # Populate called number fields
                logging.info("Populating called number fields")
                sendkeys(self.driver, oesearch_path['Called_number_field'],
                         self.device_1["sims"]["sim_slot_1"]["sim_MSISDN"] + Keys.RETURN, "Called number field")
                sendkeys(self.driver, oesearch_path['Called_number_field'],
                         self.device_2["sims"]["sim_slot_1"]["sim_MSISDN"], "Called number field")

                # Populate IMSI fields
                logging.info("Populating IMSI fields")
                sendkeys(self.driver, oesearch_path['IMSI_field'],
                         self.device_1["sims"]["sim_slot_1"]["sim_IMSI"] + Keys.RETURN, "IMSI field")
                sendkeys(self.driver, oesearch_path['IMSI_field'],
                         self.device_2["sims"]["sim_slot_1"]["sim_IMSI"] + ' ', "IMSI field")

            # Step 4: Execute search
            logging.info("Executing OE search")
            eleclick(
                self.driver, oesearch_path['Search_button'], "Search button")
            eleclick(
                self.driver, oesearch_path['Search_anyway'], "Search anyway button")

            logging.info("OE search initiated successfully")
            return True

        except Exception as e:
            logging.error(f"OE search failed. Error: {str(e)}")
            logging.error(
                f"Search parameters - Template: {used_template}, Time: {start_time} to {end_time}")
            return False

    def download_oesearch_pcap_NewUi(self, oesearch_download_path):
        """
        Downloads PCAP file from OESearch UI.
        Refreshes page periodically until trace is complete.
        """

        def check_export_button_exists(driver, timeout=5):
            """
            Checks if Export button exists with a short timeout.

            Args:
                driver: WebDriver instance
                timeout: Short timeout for checking (default: 5 seconds)

            Returns:
                WebElement if found, None otherwise
            """
            try:
                export_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//span[@style='position: relative; margin-right: 10px;' and @class='ng-star-inserted']//button[contains(@class, 'p-button')]"))
                )
                return export_button

            except TimeoutException:
                return None
            except Exception as e:
                logging.warning(f"Error checking for button: {str(e)}")
                return None

        try:
            logging.info("Waiting for Oesearch trace to complete...")

            max_attempts = 40
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                logging.info(
                    f"Checking for Export button - Attempt {attempt}/{max_attempts}")

                # Check if Export button is available
                export_button = check_export_button_exists(self.driver)

                if export_button:
                    # Button found - click it and break
                    export_button.click()
                    logging.info(
                        f"Oesearch trace completed after {attempt * 5} seconds")
                    break
                else:
                    # Button not found - refresh and wait
                    logging.info("Trace not complete yet, refreshing page...")
                    self.driver.refresh()
                    time.sleep(10)  # Wait 5 seconds before next attempt

            # Check if we exceeded max attempts
            if attempt >= max_attempts:
                logging.error(
                    f"Export button did not appear within {max_attempts * 5} seconds")
                return False

            # Continue with download process
            time.sleep(3)
            eleclick(
                self.driver, oesearch_download_path['PCAP_selection_button'], "PCAP_selection_button")
            eleclick(
                self.driver, oesearch_download_path['Confirm_Download_pcap'], "Confirm_Download_pcap")
            eleclick(
                self.driver, oesearch_download_path['File_mangment_button'], "File_mangment_button")
            eleclick(
                self.driver, oesearch_download_path['Confirm_file_mangment_button'], "Confirm_file_mangment_button")
            eleclick(
                self.driver, oesearch_download_path['Download_Pcap_button'], "Download_Pcap_button")
            time.sleep(15)
            eleclick(
                self.driver, oesearch_download_path['Delete_Pcap_button'], "Delete_Pcap_button")
            eleclick(
                self.driver, oesearch_download_path['Confirm_Pcap_delete'], "Confirm_Pcap_delete")

            logging.info(
                f".pcap file downloaded successfully to path: {self.pcap_download_dir}")
            time.sleep(10)
            self.driver.quit()

        except Exception as e:
            logging.error(f"Error while Downloading Pcap: {e}")
            return False

        return True

    def get_pcap_path(self, templet):
        os.chdir(self.pcap_download_dir)

        pcap_files = glob.glob(f"{templet}*")
        if pcap_files:
            tar_file = pcap_files[0]
            return os.path.join(self.pcap_download_dir, tar_file)

    # -------------------legacy app -------------------------------#

    def start_oesearch(self, oesearch_path, start_time, end_time, imsi, used_template):
        logging.info(
            f"Starting oeserach for subscriber with IMSI : {imsi} .....")

        # Check if the selected template requires network configuration
        network_required_templates = {
            "GB Dialogue",
            "EOFINDER_OVERALL_summary"
        }
        requires_network = used_template in network_required_templates

        if requires_network:
            logging.info(f"Template '{used_template}' requires network access")
            requires_network = True

        try:
            # Select and apply the desired template
            eleclick(
                self.driver, oesearch_path['Templete_menu_button'], "Templete_menu_button")
            sendkeys(
                self.driver, oesearch_path['Templete_input_field'], used_template, "Templete_input_field")
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

            # Set the search time interval
            eleclick(
                self.driver, oesearch_path['Time_intrval_button'], "Time_intrval_button")
            for field, value in [(oesearch_path['Start_time_field'], start_time), (oesearch_path['End_time_field'], end_time)]:
                sendkeys(self.driver, field, value, "time intervall", True)

            # Apply network filter if required
            if requires_network:
                eleclick(
                    self.driver, oesearch_path['Network_menu_button'], "Network_menu_button")
                eleclick(
                    self.driver, oesearch_path['checkbox_path'], "checkbox_path")

            if requires_network:
                # Set IMSI filter and perform search (network mode)
                eleclick(
                    self.driver, oesearch_path['Filter_button'], "Filter_button")
                eleclick(
                    self.driver, oesearch_path['Dropdown_trigger'], "Dropdown_trigger")
                sendkeys(
                    self.driver, oesearch_path['Filter_input'], "IMSI", "Filter_input")
                eleclick(
                    self.driver, oesearch_path['IMSI_filter'], "IMSI_filter")
                eleclick(
                    self.driver, oesearch_path['Filter_options'], "Filter_options")
                eleclick(self.driver, oesearch_path['Equal'], "Equal")
                sendkeys(
                    self.driver, oesearch_path['IMSI_box'], imsi, "IMSI_box")
                eleclick(
                    self.driver, oesearch_path['Search_button'], "Search_button")
            else:
                # Configure filters and search (non-network mode)
                eleclick(
                    self.driver, oesearch_path['Filter_button'], "Filter_button")
                time.sleep(3)
                eleclick(
                    self.driver, oesearch_path['Delete_summary_button'], "Delete_summary_button")
                eleclick(
                    self.driver, oesearch_path['Filter_by_filed'], "Filter_by_filed")
                time.sleep(2)

                # Navigate to IMSI filter and input value
                ActionChains(self.driver).send_keys(
                    Keys.DOWN).send_keys(Keys.ENTER).perform()
                time.sleep(3)

                self.driver.execute_script(
                    "document.querySelector(\"button[data-id='gwt-debug-paletteWidget_SelectOperator_1']\").click();")
                # eleclick(self.driver, oesearch_path['IMSI_equal'], "IMSI_equal")
                # sendkeys(self.driver, oesearch_path['IMSI_field'], imsi, "IMSI_field")
                eleclick(
                    self.driver, oesearch_path['Search_button'], "Search_button")

            logging.info("oeserach started ....")
            time.sleep(5)
            return True

        except Exception as e:
            logging.error(f"OE search failed for IMSI {imsi}: {str(e)}")
            return False

    def download_oesearch_pcap(self, oesearch_download_path):

        try:
            # wait_until_class_not_contains_and_click(self.driver, oesearch_download_path['Export_button'], "view_SideButton_disabled", 300)

            self.driver.refresh()
            logging.info("Switching to new UI interface")
            eleclick(
                self.driver, oesearch_download_path['Switch_to_new'], "Switch to new UI")
            eleclick(self.driver, oesearch_download_path['test'], "test")
            eleclick(
                self.driver, oesearch_download_path['Export_button'], "Export_button")
            time.sleep(10)

            # eleclick(self.driver, oesearch_download_path['Export_button'],"Export Button")
            # self.driver.execute_script('document.querySelector(\'.dropdown-toggle[title="Export"]\').click();')

            # click_seq = [
            #     "PCAP_selection_button",
            #     #"Confirm_Download_pcap",
            #     #"Download_list_button",
            #     #"Download_pcap",
            #     #"Download_list_button",
            #     #"Delete_all_download"
            # ]

            # for key in click_seq:
            #     eleclick(self.driver,oesearch_download_path[key],key)
            #     time.sleep(1)

            # logging.info("Pcap file downloaded successfully")
            self.driver.quit()

        except Exception as e:
            logging.error(f"Error while Downloading Pcap: {e}")
            return False

        return True
