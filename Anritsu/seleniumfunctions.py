from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException,ElementNotInteractableException,NoSuchElementException
import logging
import time
from selenium.webdriver.common.keys import Keys
import re


def eleclick(driver, xpath, element_name) -> bool:
    try:
        # Reduced wait time for headless - no visual rendering delays
        ele = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        
        # Skip scrollIntoView in headless - not needed for visual positioning
        # Only scroll if element is not in viewport (rare in headless)
        if not driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            return rect.top >= 0 && rect.bottom <= window.innerHeight;
        """, ele):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ele)
        
        # Use JavaScript click for better reliability in headless
        driver.execute_script("arguments[0].click();", ele)
        
        # Minimal delay - headless processes faster
        time.sleep(1)
        return True
        
    except TimeoutException:
        # Fallback: try to find and click with JS even if not "clickable"
        try:
            ele = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", ele)
            time.sleep(0.1)
            return True
        except:
            #logging.warning(f"Failed to click '{element_name}' - element not found")
            return False
            
    except Exception as e:
        # Try direct JavaScript execution as last resort
        try:
            driver.execute_script(f"""
                var element = document.evaluate('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) element.click();
            """)
            time.sleep(0.1)
            return True
        except:
            #logging.error(f"All click attempts failed for '{element_name}': {str(e)}")
            return False

    except TimeoutException:
        logging.error(f"Timeout: Could not find clickable element '{element_name}'")
        return False
        
    except ElementClickInterceptedException:
        logging.error(f"Click intercepted for '{element_name}', trying JavaScript click")
        try:
            # Fallback to JavaScript click
            driver.execute_script("arguments[0].click();", ele)
            logging.info(f"Successfully clicked '{element_name}' using JavaScript")
            return True
        except Exception as e:
            logging.error(f"JavaScript click also failed for '{element_name}': {e}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error clicking '{element_name}': {e}")
        return False
    
def sendkeys(driver, xpath, send_value, element_name, clear_first=False) -> bool:
    try:
        # Wait for element to be present and interactable
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        
        # Small delay to ensure element is ready
        time.sleep(1)
        
        # Clear field if requested
        if clear_first:
            # Click to ensure focus
            ele.click()
            time.sleep(0.2)
            
            # Try multiple clearing methods
            try:
                # Method 1: JavaScript clear
                driver.execute_script("arguments[0].value = '';", ele)
                
                # Method 2: Select all and delete
                ele.send_keys(Keys.CONTROL + "a")
                ele.send_keys(Keys.DELETE)
                
                # Method 3: Selenium clear as backup
                ele.clear()
                
                # Trigger events for JS frameworks
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, ele)
                
                time.sleep(0.2)
            except Exception as clear_error:
                logging.warning(f"Clear operation had issues: {clear_error}")
            
        # Send keys
        ele.send_keys(send_value)
        logging.info(f"Successfully sent keys to '{element_name}'")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send keys to '{element_name}': {str(e)}")
        return False
        
    except TimeoutException:
        logging.error(f"Timeout: Could not find element '{element_name}'")
        return False
        
    except ElementNotInteractableException:
        logging.error(f"Element not interactable '{element_name}', trying JavaScript")
        try:
            # Fallback to JavaScript
            if clear_first:
                driver.execute_script("arguments[0].value = '';", ele)
            driver.execute_script("arguments[0].value = arguments[1];", ele, send_value)
            logging.info(f"Successfully sent keys to '{element_name}' using JavaScript")
            return True
        except Exception as e:
            logging.error(f"JavaScript fallback failed for '{element_name}': {e}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error sending keys to '{element_name}': {e}")
        return False

def senddirc(driver, xpath, send_value, element_name, clear_first=False) -> bool:
    try:
        # Wait for element to be present and interactable
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        
        # Small delay to ensure element is ready
        time.sleep(0.5)
        
        # Clear field if requested
        if clear_first:
            # Click to ensure focus
            ele.click()
            time.sleep(0.2)
            
            # Try multiple clearing methods
            try:
                # Method 1: JavaScript clear
                driver.execute_script("arguments[0].value = '';", ele)
                
                # Method 2: Select all and delete
                ele.send_keys(Keys.CONTROL + "a")
                ele.send_keys(Keys.DELETE)
                
                # Method 3: Selenium clear as backup
                ele.clear()
                
                # Trigger events for JS frameworks
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, ele)
                
                time.sleep(0.2)
            except Exception as clear_error:
                logging.warning(f"Clear operation had issues: {clear_error}")
            
        # Send keys
        ele.send_keys(send_value)
        logging.info(f"Successfully sent keys to '{element_name}'")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send keys to '{element_name}': {str(e)}")
        return False
        
    except TimeoutException:
        logging.error(f"Timeout: Could not find element '{element_name}'")
        return False
        
    except ElementNotInteractableException:
        logging.error(f"Element not interactable '{element_name}', trying JavaScript")
        try:
            # Fallback to JavaScript
            if clear_first:
                driver.execute_script("arguments[0].value = '';", ele)
            driver.execute_script("arguments[0].value = arguments[1];", ele, send_value)
            logging.info(f"Successfully sent keys to '{element_name}' using JavaScript")
            return True
        except Exception as e:
            logging.error(f"JavaScript fallback failed for '{element_name}': {e}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error sending keys to '{element_name}': {e}")
        return False
      
def eclear(driver, xpath, element_name) -> bool:
    try:
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ele)
        time.sleep(0.5)
        
        # Try standard clear first
        ele.clear()
        
        # Check if clear worked
        if ele.get_attribute('value'):
            logging.warning(f"Standard clear failed for '{element_name}', trying alternatives")
            # Try select all + delete
            ele.send_keys(Keys.CONTROL + "a")
            ele.send_keys(Keys.DELETE)
            
            # If still not cleared, try JavaScript
            if ele.get_attribute('value'):
                driver.execute_script("arguments[0].value = '';", ele)
                
        logging.info(f"Successfully cleared '{element_name}'")
        return True
        
    except TimeoutException:
        logging.error(f"Timeout: Could not find element '{element_name}'")
        return False
        
    except ElementNotInteractableException:
        logging.error(f"Element '{element_name}' not interactable, trying JavaScript clear")
        try:
            driver.execute_script("arguments[0].value = '';", ele)
            logging.info(f"Successfully cleared '{element_name}' using JavaScript")
            return True
        except Exception as e:
            logging.error(f"JavaScript clear failed for '{element_name}': {e}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error clearing '{element_name}': {e}")
        return False
    
def getele(driver, xpath, element_name="element"):
    try:
        ele = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        logging.debug(f"Successfully found '{element_name}'")
        return ele
        
    except TimeoutException:
        logging.error(f"Timeout: Could not find element '{element_name}'")
        return None
        
    except Exception as e:
        logging.error(f"Error finding element '{element_name}': {e}")
        return None

# def text_in_child_element(driver, parent_ele_xpath, child_xpath, new_text):
#     try:
#         imsi_ele = driver.find_element(By.XPATH, parent_ele_xpath)
#         parent_ele = imsi_ele.find_element(By.XPATH, "./ancestor::tr")
#         child_ele = parent_ele.find_element(By.XPATH, child_xpath)
#         logging.info(f"start title is {child_ele.get_attribute('title')}")
#         logging.info(f"start text is {child_ele.text}")
#         return new_text == child_ele.text
#     except:
#         return False

# def addpictodoc(driver, doc):
#     time = datetime.datetime.now()
#     filename = "picture" + str(time) + ".png"

#     driver.save_screenshot(filename)
#     doc.add_picture(filename, width=Cm(15), height=Cm(8))
#     os.remove(filename) 


def ele_presence(driver, xpath, ele_name, timeout=10):
    """
    Checks for the presence of a graph element on the page.
    Args:
        driver: Selenium WebDriver instance
        xpath: XPath to locate the graph element
        ele_name: Name of the graph for logging purposes
        timeout: Maximum time to wait for element (default: 10 seconds)
    Returns:
        bool: True if graph is present, False otherwise
    """
    logging.debug(f"Checking presence of element: {ele_name} with timeout: {timeout}s")
    
    try:
        # Wait for element to be present in DOM
        logging.debug(f"Waiting for element presence: {ele_name}")
        ele = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        logging.info(f"Element successfully located: {ele_name}")
        
        # Verify element visibility
        try:
            logging.debug(f"Verifying display status for: {ele_name}")
            is_displayed = ele.is_displayed()
            
            if is_displayed:
                logging.info(f"Element is visible and ready: {ele_name}")
            else:
                logging.warning(f"Element found but not visible: {ele_name}")
                
            return True
            
        except Exception as display_err:
            logging.warning(f"Could not verify display status for {ele_name}: {str(display_err)}")
            logging.debug(f"Element exists but display validation failed for: {ele_name}")
            return True
            
    except TimeoutException:
        logging.error(f"Element not found within {timeout} seconds: {ele_name}")
        logging.debug(f"XPath used: {xpath}")
        return False
        
    except NoSuchElementException:
        logging.error(f"Element does not exist in DOM: {ele_name}")
        logging.debug(f"XPath used: {xpath}")
        return False
        
    except Exception as e:
        logging.error(f"Unexpected error while locating {ele_name}: {type(e).__name__} - {str(e)}")
        logging.debug(f"XPath used: {xpath}")
        return False
 
# def addhighlightedtext(doc, text):
#     paraobj = doc.add_paragraph()
#     runobj = paraobj.add_run(text)
#     runobj.bold = True
#     font1 = runobj.font
#     font1.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN






# ───── Elements in Shadow DOM  ────────────────────────────────

# === Utility Functions ===

def create_shadow_xpath(xpath):
    # First replace all // with /shadow/
    shadow_xpath = xpath.replace("//", "/shadow/")

    # Then replace all instances of [n] with :nth-of-type(n) using regular expressions
    import re

    shadow_xpath = re.sub(r"\[(\d+)\]", r":nth-of-type(\1)", shadow_xpath)

    return shadow_xpath

def process_shadow_xpath(xpath):
    logging.info(f"process_shadow_xpath: Input xpath = {xpath}")
    
    # Replace /shadow/ with //
    xpath = xpath.replace('//', '/shadow/')
    logging.info(f"process_shadow_xpath: After replacing // with /shadow/ = {xpath}")

    # Replace div[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'div\[(\d+)\]', r'div:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        logging.info(f"process_shadow_xpath: After div[n] replacement = {xpath}")
    
    # Replace button[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'button\[(\d+)\]', r'button:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        logging.info(f"process_shadow_xpath: After button[n] replacement = {xpath}")
    
    # Replace eui-button[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'eui-button\[(\d+)\]', r'eui-button:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        logging.info(f"process_shadow_xpath: After eui-button[n] replacement = {xpath}")
    
    # Replace item[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'item\[(\d+)\]', r'item:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        logging.info(f"process_shadow_xpath: After item[n] replacement = {xpath}")
    
    logging.info(f"process_shadow_xpath: Final processed xpath = {xpath}")
    return xpath

def split_xpath(xpath):
    xpath = process_shadow_xpath(xpath)
    normalized_xpath = xpath.replace("//", "/")
    return [segment for segment in normalized_xpath.split("/") if segment]

def traverse_shadow_dom(driver, shadow_host, path_segments):
    current_element = shadow_host

    for segment in path_segments:
        try:
            if segment == "shadow":
                shadow_root = driver.execute_script(
                    "return arguments[0].shadowRoot", current_element
                )
                if shadow_root:
                    current_element = shadow_root
            else:
                current_element = WebDriverWait(driver, 10).until(
                    lambda d: current_element.find_element(By.CSS_SELECTOR, segment)
                )
                #logging.info(f"current element is {current_element.tag_name}")

        except Exception as e:
            print(f"Failed to find segment {segment}:{e}")
            return None
    return current_element

def find_element_with_shadow_xpath(driver, xpath):
    """
    Find an element using a shadow DOM XPath starting from the initial host.
    """
    path_segments = split_xpath(xpath)
    if not path_segments:
        logging.error("No valid segments in XPath")
        return None

    # The first segment is the starting point outside shadow DOM
    shadow_host_selector = path_segments.pop(0)
    try:
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, shadow_host_selector))
        )
        #logging.info( f"Found shadow host with selector '{shadow_host_selector}': {shadow_host.tag_name}")
    except Exception as e:
        logging.error(
            f"Failed to find shadow host with selector '{shadow_host_selector}': {str(e)}"
        )
        return None

    return traverse_shadow_dom(driver, shadow_host, path_segments)

def find_element_with_shadow_xpath_and_send_key(driver, xpath, key):
    """
    Find an element using a shadow DOM XPath starting from the initial host.
    send key
    """
    path_segments = split_xpath(xpath)
    if not path_segments:
        logging.error("No valid segments in XPath")
        return None
    # The first segment is the starting point outside shadow DOM
    shadow_host_selector = path_segments.pop(0)
    try:
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, shadow_host_selector))
        )
        logging.info(
            f"Found shadow host with selector '{shadow_host_selector}': {shadow_host.tag_name}"
        )
        # Find the element by traversing the shadow DOM
        element = traverse_shadow_dom(driver, shadow_host, path_segments)

        if element:
            logging.info(f"Found element, sending key: {key}")
            # Use JavaScript to set the value and dispatch appropriate events
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
                element,
                key,
            )
            return element
        else:
            logging.error("Element not found in shadow DOM")
            return None
    except Exception as e:
        logging.error(
            f"Failed to find shadow host with selector '{shadow_host_selector}': {str(e)}"
        )
        return None

def find_element_in_shadow_dom(driver, xpath):
    """
    Find an element in shadow DOM using an XPath-like syntax.

    Args:
        driver: Selenium WebDriver instance
        xpath: XPath-like string to locate element in shadow DOM

    Returns:
        WebElement: The found element or None if not found
    """
    # Step 1: Convert XPath to shadow DOM compatible format
    shadow_xpath = create_shadow_xpath(xpath)

    # Step 2: Find the element using the converted XPath
    return find_element_with_shadow_xpath(driver, shadow_xpath)

# ======================== 

def eleclick_with_shadow(driver, xpath):
    """
    click on element in shadow DOM(s)
    
    Args:
        driver: WebDriver instance
        xpath: Shadow DOM XPath string
        
    Returns:
        bool: True if click was successful, False otherwise
    """
    try:
        # Find the element using your existing function
        element = find_element_with_shadow_xpath(driver, xpath)
        
        if element:
            # Use JavaScript click - exactly like your working code
            driver.execute_script("arguments[0].click();", element)
            time.sleep(2)  # Same delay as your working code
            #logging.info(f"Successfully clicked element: {element.tag_name}")
            return True
        else:
            logging.error("Element not found")
            return False
            
    except Exception as e:
        logging.error(f"Failed to click element: {str(e)}")
        return False

def sendkeys_with_shadow(driver, xpath, keys):
    """
    Send keys to element in shadow DOM(s)
    
    Args:
        driver: WebDriver instance
        xpath: Shadow DOM XPath string
        keys: String or keys to send to the element
        
    Returns:
        bool: True if sending keys was successful, False otherwise
    """
    try:
        # Find the element using your existing function
        element = find_element_with_shadow_xpath(driver, xpath)
        
        if element:
            # Clear the element first (optional - remove if not needed)
            element.clear()
            
            # Send keys to the element
            element.send_keys(keys)
            time.sleep(2)  # Same delay as your working code
            #logging.info(f"Successfully sent keys to element: {element.tag_name}")
            return True
        else:
            logging.error("Element not found")
            return False
            
    except Exception as e:
        logging.error(f"Failed to send keys to element: {str(e)}")
        return False


# ───── Special Elements  ────────────────────────────────

def wait_until_class_not_contains_and_click(driver, xpath=None, class_text="view_SideButton_disabled", timeout=45, debug=True):
    """
    Enhanced function to find and click Export buttons with comprehensive detection.
    
    Args:
        driver: Selenium WebDriver instance
        xpath: Optional specific xpath to try first (for backward compatibility)
        class_text: Class text that should NOT be present (indicates disabled state)
        timeout: Maximum time to wait in seconds
        debug: Enable detailed logging
    
    Returns:
        WebElement if successful, None if failed
    
    Usage:
        # Simple usage - will automatically find Export button
        element = wait_until_class_not_contains_and_click(driver)
        
        # With specific xpath (backward compatibility)
        element = wait_until_class_not_contains_and_click(
            driver, 
            xpath="//li[@id='ExportButton']//a[@title='Export']",
            class_text="view_SideButton_disabled"
        )
    """
    try:
        logging.info("Starting enhanced export button detection and click...")
        
        # Detect headless mode
        is_headless = _detect_headless_mode(driver)
        if is_headless:
            timeout = max(timeout, 45)
            logging.info("Headless mode detected - using extended timeout")
        
        # Wait for page to be ready
        _wait_for_page_ready(driver, timeout)
        
        # Run comprehensive debug if requested
        if debug:
            _comprehensive_page_debug(driver)
        
        # Strategy 1: Try original xpath if provided
        if xpath:
            logging.info(f"Trying original xpath: {xpath}")
            element = _try_original_xpath(driver, xpath, class_text, timeout)
            if element:
                return _attempt_click(driver, element, is_headless)
        
        # Strategy 2: Use comprehensive detection
        logging.info("Using comprehensive export button detection...")
        element = _comprehensive_export_detection(driver, class_text, timeout)
        if element:
            return _attempt_click(driver, element, is_headless)
        
        # Strategy 3: Last resort - try any clickable with "Export"
        logging.info("Last resort: trying any clickable with 'Export'...")
        element = _find_any_export_element(driver)
        if element:
            return _attempt_click(driver, element, is_headless)
        
        logging.error("No Export button found with any strategy")
        return None
        
    except Exception as e:
        logging.error(f"Error in wait_until_class_not_contains_and_click: {e}")
        return None

def _detect_headless_mode(driver):
    """Detect if browser is running in headless mode"""
    try:
        return driver.execute_script("return navigator.webdriver") or \
               any('headless' in str(arg).lower() for arg in driver.capabilities.get('chrome', {}).get('args', []))
    except:
        return False

def _wait_for_page_ready(driver, timeout):
    """Wait for page to be fully loaded"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Wait for navbar container
        navbar_selectors = [
            (By.ID, "gwt-debug-leftSideBar_Container"),
            (By.CLASS_NAME, "navbar-nav"),
            (By.XPATH, "//ul[contains(@class, 'navbar-nav')]"),
            (By.XPATH, "//nav"),
            (By.XPATH, "//div[contains(@class, 'navbar')]")
        ]
        
        navbar_found = False
        for selector_type, selector_value in navbar_selectors:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                logging.info(f"Navbar found: {selector_type}={selector_value}")
                navbar_found = True
                break
            except TimeoutException:
                continue
        
        if not navbar_found:
            logging.warning("No navbar found, continuing anyway...")
        
        # Wait for dynamic content
        time.sleep(2)
        
    except Exception as e:
        logging.warning(f"Error waiting for page ready: {e}")

def _try_original_xpath(driver, xpath, class_text, timeout):
    """Try the original xpath approach"""
    try:
        element = WebDriverWait(driver, min(timeout // 3, 15)).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        # Check parent element class if it's a link inside a list item
        if element.tag_name == 'a':
            parent = element.find_element(By.XPATH, "./..")
            if parent.tag_name == 'li':
                parent_class = parent.get_attribute('class') or ''
                if class_text in parent_class:
                    logging.info(f"Original xpath element is disabled: {parent_class}")
                    return None
        
        # Check element's own class
        element_class = element.get_attribute('class') or ''
        if class_text in element_class:
            logging.info(f"Original xpath element is disabled: {element_class}")
            return None
        
        if element.is_displayed() and element.is_enabled():
            logging.info("Original xpath found suitable element")
            return element
        
    except TimeoutException:
        logging.info("Original xpath timed out")
    except Exception as e:
        logging.warning(f"Original xpath failed: {e}")
    
    return None

def _comprehensive_export_detection(driver, class_text, timeout):
    """Comprehensive export button detection with scoring"""
    try:
        # All possible ways to find Export buttons
        search_strategies = [
            # High priority - specific patterns
            ("ExportButton ID", "//li[@id='ExportButton']//a[@title='Export']"),
            ("ExportButton ID any link", "//li[@id='ExportButton']//a"),
            ("Export title link", "//a[@title='Export']"),
            ("Export title button", "//button[@title='Export']"),
            
            # Medium priority - text-based
            ("Link text Export", "//a[contains(text(), 'Export')]"),
            ("Button text Export", "//button[contains(text(), 'Export')]"),
            ("Input value Export", "//input[@value='Export']"),
            ("Span text Export", "//span[contains(text(), 'Export')]//ancestor::*[self::a or self::button][1]"),
            
            # Class and ID patterns
            ("ID contains export", "//*[contains(@id, 'export') or contains(@id, 'Export')]"),
            ("Class contains export", "//*[contains(@class, 'export') or contains(@class, 'Export')]"),
            
            # Icon-based
            ("Export icons", "//*[contains(@class, 'fa-file-export') or contains(@class, 'fa-export') or contains(@class, 'fa-download')]"),
            ("Export glyphicons", "//*[contains(@class, 'glyphicon-export') or contains(@class, 'glyphicon-download')]"),
            
            # Data attributes
            ("Data action export", "//*[contains(@data-action, 'export')]"),
            ("Data toggle export", "//*[contains(@data-toggle, 'export')]"),
            
            # Dropdown patterns
            ("Dropdown Export", "//div[contains(@class, 'dropdown')]//a[contains(text(), 'Export')]"),
            ("Menu Export", "//ul[contains(@class, 'menu')]//a[contains(text(), 'Export')]"),
            
            # Broader searches
            ("Any clickable Export", "//*[self::a or self::button or self::input[@type='button']][contains(text(), 'Export') or contains(@title, 'Export') or contains(@value, 'Export')]"),
            ("Case insensitive Export", "//*[contains(translate(text(), 'EXPORT', 'export'), 'export')]"),
        ]
        
        all_candidates = []
        
        for strategy_name, xpath in search_strategies:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    logging.info(f" {strategy_name}: Found {len(elements)} elements")
                    for elem in elements:
                        candidate = _analyze_element(elem, strategy_name, class_text)
                        if candidate:
                            all_candidates.append(candidate)
                else:
                    logging.debug(f" {strategy_name}: 0 elements")
            except Exception as e:
                logging.debug(f" {strategy_name}: Error - {e}")
        
        if not all_candidates:
            logging.warning("No export candidates found")
            return None
        
        # Score and rank candidates
        scored_candidates = []
        for candidate in all_candidates:
            score = _score_element(candidate, class_text)
            scored_candidates.append((score, candidate))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Log top candidates
        logging.info("\n=== TOP EXPORT CANDIDATES ===")
        for i, (score, candidate) in enumerate(scored_candidates[:5]):
            logging.info(f"Rank {i+1} (Score: {score}): {candidate['strategy']}")
            logging.info(f"  Element: {candidate['tag']} id='{candidate['id']}' class='{candidate['class'][:50]}...'")
            logging.info(f"  Text: '{candidate['text']}' Title: '{candidate['title']}'")
            logging.info(f"  Displayed: {candidate['displayed']} Enabled: {candidate['enabled']}")
        
        # Return the best candidate
        if scored_candidates:
            best_score, best_candidate = scored_candidates[0]
            logging.info(f"Selected best candidate with score {best_score}")
            return best_candidate['element']
        
        return None
        
    except Exception as e:
        logging.error(f"Error in comprehensive detection: {e}")
        return None

def _analyze_element(element, strategy_name, class_text):
    """Analyze an element and return candidate info"""
    try:
        candidate = {
            'element': element,
            'strategy': strategy_name,
            'tag': element.tag_name,
            'id': element.get_attribute('id') or '',
            'class': element.get_attribute('class') or '',
            'text': element.text[:50] if element.text else '',
            'title': element.get_attribute('title') or '',
            'href': element.get_attribute('href') or '',
            'onclick': element.get_attribute('onclick') or '',
            'displayed': element.is_displayed(),
            'enabled': element.is_enabled(),
            'location': element.location,
            'size': element.size
        }
        
        # Skip if element is clearly disabled
        if class_text and class_text in candidate['class']:
            return None
        
        # Check parent for disabled state (for nested elements)
        try:
            parent = element.find_element(By.XPATH, "./..")
            parent_class = parent.get_attribute('class') or ''
            if class_text and class_text in parent_class:
                return None
        except:
            pass
        
        return candidate
        
    except Exception as e:
        logging.debug(f"Error analyzing element: {e}")
        return None

def _score_element(candidate, class_text):
    """Score an element based on various criteria"""
    score = 0
    
    # Base score for clickable elements
    if candidate['tag'] in ['a', 'button']:
        score += 20
    elif candidate['tag'] == 'input':
        score += 15
    
    # Visibility and state
    if candidate['displayed']:
        score += 10
    if candidate['enabled']:
        score += 10
    
    # Size check
    if candidate['size']['width'] > 0 and candidate['size']['height'] > 0:
        score += 5
    
    # Text and title content
    if 'Export' in candidate['title']:
        score += 15
    if 'Export' in candidate['text']:
        score += 12
    
    # Specific IDs
    if candidate['id'] == 'ExportButton':
        score += 25
    elif 'export' in candidate['id'].lower():
        score += 8
    
    # Functional attributes
    if candidate['href'] and candidate['href'] != '#' and candidate['href'] != 'javascript:;':
        score += 8
    if candidate['onclick']:
        score += 8
    
    # Strategy bonus
    if 'ExportButton ID' in candidate['strategy']:
        score += 20
    elif 'Export title' in candidate['strategy']:
        score += 15
    elif 'text Export' in candidate['strategy']:
        score += 10
    
    # Penalties
    if 'disabled' in candidate['class'].lower():
        score -= 20
    if not candidate['displayed']:
        score -= 15
    if not candidate['enabled']:
        score -= 15
    
    return score

def _find_any_export_element(driver):
    """Last resort: find any element with Export"""
    try:
        # Very broad search
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Export') or contains(@title, 'Export') or contains(@value, 'Export')]")
        
        for elem in elements:
            try:
                if elem.is_displayed() and elem.is_enabled():
                    # Try to find a clickable parent
                    current = elem
                    for _ in range(3):  # Go up 3 levels max
                        if current.tag_name in ['a', 'button'] or current.get_attribute('onclick'):
                            logging.info(f"Found clickable parent: {current.tag_name}")
                            return current
                        try:
                            current = current.find_element(By.XPATH, "./..")
                        except:
                            break
                    
                    # If element itself is clickable
                    if elem.tag_name in ['a', 'button'] or elem.get_attribute('onclick'):
                        logging.info(f"Found clickable element: {elem.tag_name}")
                        return elem
            except:
                continue
        
        return None
        
    except Exception as e:
        logging.error(f"Error in last resort search: {e}")
        return None

def _attempt_click(driver, element, is_headless=False):
    """Attempt to click element with multiple strategies"""
    try:
        # Scroll to element
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
        time.sleep(1 if is_headless else 0.5)
        
        # Try different click methods
        click_methods = [
            ('Regular click', lambda: element.click()),
            ('JavaScript click', lambda: driver.execute_script("arguments[0].click();", element)),
            ('Dispatch click event', lambda: driver.execute_script("""
                var evt = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                arguments[0].dispatchEvent(evt);
            """, element)),
            ('Focus and click', lambda: driver.execute_script("arguments[0].focus(); arguments[0].click();", element)),
            ('Force click', lambda: driver.execute_script("""
                if (arguments[0].click) {
                    arguments[0].click();
                } else if (arguments[0].onclick) {
                    arguments[0].onclick();
                }
            """, element))
        ]
        
        for method_name, click_func in click_methods:
            try:
                logging.info(f"Trying {method_name}...")
                click_func()
                logging.info(f" {method_name} succeeded")
                time.sleep(1.5 if is_headless else 0.5)
                return element
            except Exception as e:
                logging.debug(f" {method_name} failed: {e}")
                continue
        
        logging.error("All click methods failed")
        return None
        
    except Exception as e:
        logging.error(f"Error in click attempt: {e}")
        return None

def _comprehensive_page_debug(driver):
    """Debug page structure and content"""
    try:
        logging.info("\n=== PAGE DEBUG INFO ===")
        
        # Basic info
        logging.info(f"Title: {driver.title}")
        logging.info(f"URL: {driver.current_url}")
        logging.info(f"Ready state: {driver.execute_script('return document.readyState')}")
        
        # Framework detection
        frameworks = {
            'jQuery': 'typeof jQuery !== "undefined"',
            'Bootstrap': 'typeof Bootstrap !== "undefined"',
            'GWT': 'typeof com !== "undefined"'
        }
        
        for framework, check in frameworks.items():
            try:
                result = driver.execute_script(f'return {check}')
                logging.info(f"{framework}: {'' if result else ''}")
            except:
                logging.info(f"{framework}: ")
        
        # Count elements
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_inputs = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit']")
        
        logging.info(f"Total buttons: {len(all_buttons)}")
        logging.info(f"Total links: {len(all_links)}")
        logging.info(f"Total input buttons: {len(all_inputs)}")
        
        # Show first few clickable elements
        all_clickables = all_buttons + all_links + all_inputs
        logging.info(f"\nFirst 5 clickable elements:")
        for i, elem in enumerate(all_clickables[:5]):
            try:
                text = elem.text[:30] if elem.text else ''
                title = elem.get_attribute('title') or ''
                elem_id = elem.get_attribute('id') or ''
                logging.info(f"  {i+1}: {elem.tag_name} id='{elem_id}' text='{text}' title='{title}'")
            except:
                logging.info(f"  {i+1}: Could not get element info")
        
        # Check for loading indicators
        loading_selectors = [
            "//div[contains(@class, 'loading')]",
            "//div[contains(@class, 'spinner')]",
            "//*[contains(text(), 'Loading')]"
        ]
        
        for selector in loading_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                logging.info(f"Loading indicators found: {len(elements)}")
                break
        
        logging.info("=== END DEBUG INFO ===\n")
        
    except Exception as e:
        logging.error(f"Debug error: {e}")

def debug_page_state(driver):
    """Backward compatibility wrapper"""
    return _comprehensive_page_debug(driver)