import csv
import hashlib
import requests
import os
import json
import random
import logging
import pytz
import sys
from datetime import datetime
from time import sleep
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

load_dotenv()

##### GLOBAL VARIABLES
global TOKEN
global HEADERS

#### IMPORTS FOR ENVIROMENT = FROM .env FILE
USERNAME = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
TOKEN = os.getenv('TOKEN')

MLX_BASE = os.getenv('MLX_BASE')
MLX_LAUNCHER = os.getenv('MLX_LAUNCHER')
LOCALHOST = os.getenv('LOCALHOST')

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


#### IMPORTS FROM CONFIG.JSON
with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

COUNTRY = config["PROXY"]["COUNTRY"]
REGION = config["PROXY"]["REGION"]
CITY = config["PROXY"]["CITY"]
PROTOCOL = config["PROXY"]["PROTOCOL"]
SESSION_TYPE = config["PROXY"]["SESSION_TYPE"]

BROWSER_TYPE = config["BROWSER_TYPE"]
OS_TYPE = config["OPERATIONAL_SYSTEM"]



# * ____________________ STRUCTURE FOR LOGS ____________________ * #
class TimezoneFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super().__init__(fmt, datefmt)

        # Defining Timezone - Pattern UTC
        self.tz = pytz.timezone(tz) if tz else pytz.UTC

    def formatTime(self, record, datefmt=None):
        # Convert logs timestamp to the defined timezone
        dt = datetime.fromtimestamp(record.created, self.tz)
        return dt.strftime(datefmt) if datefmt else dt.isoformat()


# Configuring the logger and timestamp format
tz_formatter = TimezoneFormatter(
    fmt="%(asctime)s\t%(levelname)s\t%(filename)s:%(lineno)d\t%(message)s",
    datefmt="%d-%m-%Y %H:%M:%S.%f %Z",
    tz="America/Sao_Paulo"
)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True) # Creates 'logs' folder if it doesn't exist.

log_file = os.path.join(log_dir, "google_scrapping.log") # It creates the log file "google_scrapping.log"
logger = logging.getLogger()

logger.setLevel(logging.INFO) # Define INFO or above as information to show. If we need to check some payload that are under debug, we can change it to "DEBUG" and check all debugging info.

if not logger.hasHandlers():
        
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(tz_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(tz_formatter)
    logger.addHandler(console_handler)



# * ____________________ FUNCTIONS ____________________ * #

def signin() -> str:
    """
    Proceed with a Sign In request and returns a token for authentication.

    Returns:
        token: string
    """

    payload = {
        "email": USERNAME,
        "password": hashlib.md5(PASSWORD.encode()).hexdigest()
    }

    r = requests.post(f"{MLX_BASE}/user/signin", json=payload)

    if(r.status_code != 200):
        logging.error(f"Error during login: {r.text}")

    response = r.json().get('data', {})

    logging.info("Token is succesfully retrieved.")

    token = response.get('token', '')
    sleep(2)

    return token

def update_headers(token):
    """
    Updates the headers to include the token.

    Args:
        token: string

    Returns:
        HEADERS: dictonary
    """

    HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
    }

    logging.info("Headers were updated.")

    return HEADERS


def get_proxy():
    """
    Request a new proxy to the API and retrive it as a proxy string,
    in the format "host:port:username:password", or None in error case.

    Returns:
        proxy_payload: dictonary
    """

    payload = {
        "country": COUNTRY,
        "protocol": PROTOCOL,
        "sessionType": SESSION_TYPE,
        "region": REGION,
        "city": CITY
    }

    logging.debug(f"Payload in 'get_proxy()': {payload}.")
    logging.info("Generating a proxy string. Wait...")
    sleep(2)

    try:
        r = requests.post(f"https://profile-proxy.multilogin.com/v1/proxy/connection_url", headers=HEADERS, json=payload, timeout=30)
        
        if r.status_code == 201:
            logging.info(f"The proxy was sucessufuly generated.")
            sleep(1)

            response_data = r.json()
            proxy_item = response_data.get("data", None)

            if proxy_item:
                logging.debug("The proxy_item has been retrieved.")
                logging.debug(f"Proxy: {proxy_item}.")
                sleep(1)
            return proxy_item
        
        else:
            logging.error(f"Error: {r.status_code}, {r.text}")
            return None

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return None
    
def build_proxy_payload(proxy_item):
    """
    It builds the proxy validation payload from a string 'proxy_item'
    in the format "host:port:username:password". Retrieves a dictionary or None ir fails.

    Args:
        proxy_item: dictionary

    Returns:
        proxy_payload: dictonary
    """

    if not proxy_item or not PROTOCOL:
        logging.error("No proxy data received.")
        return None
    
    try: 
        sleep(1)
        logging.info("Building the proxy payload.")
        
        parts = proxy_item.split(":")
        logging.debug(f"Parts: {parts}")
        if len(parts) < 4:
            logging.error("Invalid proxy format.")
            return None

        proxy_payload = {
            "type": PROTOCOL,
            "host": parts[0],
            "port": int(parts[1]),
            "username": parts[2],
            "password": parts[3]
        }

        logging.debug(f"Proxy_payload: {proxy_payload}.")
        return proxy_payload
    
    except Exception as e:
        logging.error(f"Error processing proxy_item: {e}")
        return None



def check_proxy(proxy_payload):
    """
    Validate the proxy using Validate Proxy API Endpoint. Returns a validated payload
    if the status is 200, or None if it fails.

    Args:
        proxy_payload: dictonary
    
    Returns:
        proxy_payload (updated): dictonary
    """

    if proxy_payload is None:
        return None
    
    try:
        logging.info("Checking the proxy...")

        r = requests.post(f'{MLX_LAUNCHER}v1/proxy/validate', headers=HEADERS, json=proxy_payload, timeout=15)
    
    except requests.RequestException as e:
        logging.error(f"Error validating proxy - exception: {e}")
        check_proxy(proxy_payload)
    
    if r.status_code == 200:
        logging.debug(f"{proxy_payload}")
        logging.info(f"Proxy checked successfully.")
        sleep(1)
        return proxy_payload
    
    #Emergency 19/03 - Workaround

    if r.status_code == 401:
        logging.info(f"Status code: {r.status_code} Skipping proxy checking: The payload is {proxy_payload}.")
        return proxy_payload
    
    else:
        try:
            error_message = r.json().get("status", {}).get("message", "Unknown error")

        except Exception:
            error_message = "Unknown error"
        logging.error(f"Proxy validation failed with status code: {r.status_code}. Message: {error_message}.")
        sleep(2)

        logging.info("A new proxy will be generated. Please, wait...")
        sleep(2)
        get_proxy()
        return None
    

def buid_qbp_payload(proxy_payload):
    """
    Defines a payload for quick profiles. Receives proxy_payload to define it.

    Args:
        proxy_payload: dictionary

    Returns:
        payload: dictionary
    """
    logging.info("Building the profile payload...")

    payload = {
        "browser_type": BROWSER_TYPE,
        "os_type": OS_TYPE,
        "is_headless": False,
        "automation": "selenium",
        "parameters": { 
            "proxy": {
                "type": PROTOCOL,
                "host": proxy_payload["host"],
                "port": proxy_payload["port"],
                "username": proxy_payload["username"],
                "password": proxy_payload["password"]
            },
            "custom_start_urls": [
                            "https://www.multilogin.com", #it works only for Stealthfox, that's why it's imporant to use driver.get('url') to navigate to websites.

                ],
            "fingerprint": {},
            "flags": {
                "audio_masking": "natural",
                "canvas_noise": "natural",
                "fonts_masking": "mask",
                "geolocation_masking": "mask",
                "geolocation_popup": "prompt",
                "graphics_masking": "mask",
                "graphics_noise": "mask",
                "localization_masking": "mask",
                "media_devices_masking": "natural",
                "navigator_masking": "mask",
                "ports_masking": "mask",
                "proxy_masking": "custom",
                "quic_mode": "natural",
                "screen_masking": "natural",
                "startup_behavior": "custom",
                "timezone_masking": "mask",
                "webrtc_masking": "mask"
            }
        }
    }

    sleep(1)
    logging.debug(f"Profile payload: {payload}")
    logging.info("Profile payload is ready.")
    return payload


def start_qbp(payload):
    """
        Starts a quick profile using the payload defined in qbp_payload()

    Args:
        payload: string

    Returns:
        driver: selenium webdriver
        qbp_id: string
    """
    logging.info("Starting quick profile. Please, wait...")
    sleep(2)

    try:
        r = requests.post(f"{MLX_LAUNCHER}v3/profile/quick", headers=HEADERS, json=payload, timeout=15)

        r_json = r.json()
        code_resp = r_json["status"]["http_code"]
        qbp_id = r_json["data"]["id"]
        port = r_json["data"]["port"]

        sleep(1)
        if code_resp == 200:
            logging.info(f"Profile {qbp_id} is successfully started.")

    except requests.RequestException as e:
        logging.error(f"Unexpected error happened during the quick profile start request: {e}.")

    try:
        if BROWSER_TYPE == "mimic":
            options = ChromiumOptions()
            options.page_load_strategy = "eager"

        else:
            options = Options()
    
    except Exception as e:
        logging.error(f"Error while defining Options in driver start. Check varaible browser_type: {e}")

    
    driver = webdriver.Remote(command_executor=f"{LOCALHOST}:{port}", options=options)

    return driver, qbp_id



def stop_profile(qbp_id) -> None:
    """
    Stops a specific profile.
    
    Args: 
        profile_id: string
    """

    r = requests.get(f"{MLX_LAUNCHER}v1/profile/stop/p/{qbp_id}", headers=HEADERS)

    if(r.status_code != 200):
        logging.error(f"Error while stopping profile: {r.text}")

    else:
        logging.info(f"Profile {qbp_id} was stopped.")


def browser_to_google(driver):
    """
    It browsers to google.com, and wait the Google's logo or Doodle to fully load and be clickable.

    Args:
        driver: selenium web driver

    Returns:
        search_box: selenium element
    """

    logging.info("Browsing to Google...")
    sleep(1)

    driver.get('https://google.com')

    wait = WebDriverWait(driver, 20)

    #ensuring Google is loaded completely before interact with the search
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "img.lnXdpd")))
    logging.info("Google homepage has loaded.")
    sleep(1)


def find_google_search(driver):
    """
    It looks for Search Box element in Google home page.

    Args:
        driver: selenium web driver

    Returns:
        search_box: selenium element
    """
    
    wait = WebDriverWait(driver, 20)

    search_box = wait.until(EC.element_to_be_clickable((By.ID, "APjFqb"))) #Google Searchbox
    logging.info("Search box has been found.")
    sleep(1)

    return search_box


def check_recaptcha(driver):
    """
    Check if Google is requesting a captcha to be solved. It tries to identify captcha elements, to ensure it's detected before continue or stop the script.

    Args:
        driver: selenium webdriver.
        qbp_id: string
        
    """

    logging.info("Checking captcha. Please, wait...")
    sleep(1)
    wait = WebDriverWait(driver, 20) #Provides up to 20 seconds to allow the automation to identify captcha elements.

    try:
        captcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]")))

        driver.switch_to.frame(captcha_iframe)
        logging.debug("Inside reCAPTCHA Iframe")

        recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
        logging.warning("Captcha detected. Manual action might be required. 30 second to complete the captcha, after that, the page will be refreshed.")

        sleep(30) #Providing time to allow the captcha be solved.

        try:
            recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
            logging.warning("Captcha is still present. Refreshing the page and checking.")
            driver.refresh()
            sleep(15)
            return True

        except TimeoutException:
            logging.info("The reCAPTCHA element could not be find. Continuing the script...")
            return False
    
    except TimeoutException:
            logging.info("The reCAPTCHA element could not be find. Continuing the script.")
            return False
    
    except Exception as e: 
        logging.error(f"Unexpected error while locating captcha element: {e}")
        return False
    
    finally:
        driver.switch_to.default_content()


def find_elements(driver):
    """
    It locates elements from the query made on Google. Retriving "search titles" and "urls"

    Args:
        driver: selenium webdriver

    Returns:
        titles: list
        urls: list
    """

    logging.info("Starting to search for the elements in the page.")

    titles = []
    urls = []

    wait = WebDriverWait(driver, 10)

    try:
        search_results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[jsname="UWckNb"]'))) 

        for result in search_results:
            try:
                title_element = result.find_element(By.TAG_NAME, 'h3')
                title = title_element.text if title_element else None
                url = result.get_attribute("href")

                if title and url:
                    titles.append(title)
                    urls.append(url)
                sleep(1)

            except Exception as e:
                logging.error(f"An error has occured while processing a result: {e}")

    except Exception as e:
        logging.error(f"An error happened while locating elements: {e}")

    return titles, urls


def human_typing(element, query):
    """
    It emulates a human typing, with random delays for each characters, also using differnt delays after punctuation symbols, and after spaces.

    Args:
        args: string
    """

    logging.info(f"Starting to type: {query}...")
    sleep(1) #just to ensure it will a delay of 1 sec before start the typing
    
    for i, char in enumerate(query):
        if random.random() < 0.05 and char.isalnum():
            logging.debug("Typing an error.")
            error = random.choice("abcdefghijklmnopqrstuvwxyz") #choosing a random error
            element.send_keys(error) #write the error
            logging.debug(f"The error: {error}")
            sleep(random.uniform(0.07, 0.2)) # small pause before correct
            element.send_keys(Keys.BACKSPACE)

        element.send_keys(char)

        #introducting long pauses between words
        if char in ".,?!;":
            sleep(random.uniform(0.3,0.6)) #after 

        elif char == " ":
            sleep(random.uniform(0.15, 0.4)) #bigger pause between words
        
        else:
            sleep(random.uniform(0.05, 0.2)) #normal time between characters

        if i % random.randint(7,15) == 0: #emulate acceleration and slow down random
            sleep(random.uniform(0.1, 0.3))
            
    return


def save_to_csv(query, titles, urls):
    """
    Record all titles and urls in a CSV file.

    Args:
        query: string
        titles: list
        urls: list
    """
    
    file_path = "google_search.csv"
    write_header = not os.path.exists(file_path)

    try: 
        with open(file_path, "a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            
            if write_header:
                writer.writerow(["Date", "Time", "Query", "Title", "URL"])

            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M:%S")

            for title, url in zip(titles, urls):
                writer.writerow([date, time, query, title, url])
    
        logging.info(f"The data has been saved in {file_path}.")

    except Exception as e:
        logging.error(f"Unexpected error occured during the process to record information on CSV file: {e}")
    
    return


def handling_args():
    """
    This function is responsible to handle with all args provided by the user via command line argument. 

    Returns:
        args_list: list
    """

    args_list = []
    num_args = len(sys.argv) - 1
    sleep(1)

    logging.info(f"Number of queries: {num_args}")

    if len(sys.argv) - 1 == 0:
        sleep(1)
        logging.error("No query has been passed. It's not possible to proceed. Please, start the script again.")
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        args_list.append(arg)
     
    logging.info(f"Queries requested: {args_list}")
    sleep(1)

    return args_list


# * ____________________ MAIN FUNCTION ____________________ *

def main(args_list, start_index=0):

    for i in range(start_index, len(args_list)):
        query = args_list[i]

        # Generating and checking proxy
        proxy_item = get_proxy()
        proxy_payload = build_proxy_payload(proxy_item)
        proxy_payload = check_proxy(proxy_payload)

        payload = buid_qbp_payload(proxy_payload)

        #S tarting profile
        driver, qbp_id = start_qbp(payload)

        #Selenium automation will start from here
        driver.maximize_window() # It can be else maximized via Selenium or added as a cmd_param.

        title = driver.title # Will return Multilogin's website title, as a default Start URL. It could be Google, but I prefered to do it using a function.
        logging.info(f"Title: {title}")

        browser_to_google(driver)

        search_box = find_google_search(driver)
        
        search_box.click()
        logging.info("Search box clicked.")
        sleep(1)

        human_typing(search_box, query)
        sleep(2)

        search_box.send_keys(Keys.ENTER)
        sleep(3)

        if check_recaptcha(driver):
            logging.warning("reCAPTCHA was still detected and it was not resolved, we need to restart the script. Retrying...")
            sleep(1)

            stop_profile(qbp_id)
            return main(args_list, i)
        
        else:
            logging.info("No captcha has been found. Continuing.")
            pass
        
        titles, urls = find_elements(driver)
        sleep(1)
        logging.info(f"Number of titles: {len(titles)}")
        logging.info(f"Number of urls: {len(urls)}")
        sleep(2)

        save_to_csv(query, titles, urls)
        sleep(1)
        stop_profile(qbp_id)

    sleep(1)
    query_word = "query" if len(args_list) == 1 else "queries"
    logging.info(f"The search on Google for {len(args_list)} {query_word} has been finished. Please, check the CSV file.")


# * ____________________ STARTS HERE ____________________ * #
if __name__ == "__main__":
    logging.info("Starting Google Search script.")

    logging.debug(f"Checking HEADERS: {HEADERS}")

    args_list = handling_args()

    if not TOKEN:
        token =  signin()
        logging.debug(f"Checking token: {token}.")
        HEADERS.update({'Authorization': f'Bearer {token}'})
        
    else:
        HEADERS.update({'Authorization': f'Bearer {TOKEN}'})

    logging.debug(f"Checking HEADERS: {HEADERS}")

    main(args_list)