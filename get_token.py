import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

YOUR_EMAIL = "vt985761@gmail.com"
YOUR_PASSWORD = "rONIN1122" # Double-check this for typos!
LOGIN_URL = "https://m.pocketoption.com/en/login/"

def get_pocketoption_token():
    token = None
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080") # Set a window size

    driver = None
    try:
        logging.info("Setting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        logging.info(f"Navigating to login page: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 10)

        logging.info("Finding email field...")
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(YOUR_EMAIL)

        logging.info("Finding password field...")
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(YOUR_PASSWORD)

        logging.info("Finding and clicking login button...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

        logging.info("Login submitted. Waiting for redirect...")
        time.sleep(5)

        current_url = driver.current_url
        if "login" in current_url.lower():
             logging.error("Login failed: Still on login page. Taking screenshot...")
             # --- THIS IS THE NEW LINE ---
             driver.save_screenshot("login_error.png")
             logging.info("Screenshot saved as login_error.png")
             # --------------------------
             return None

        logging.info("Login successful. Extracting cookies...")
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'ssid':
                token = cookie['value']
                logging.info(f"Found SSID cookie: {token}")
                break
        if not token: logging.warning("Could not find the 'ssid' cookie after login.")

    except Exception as e:
         logging.error(f"An error occurred: {e}")
         if driver:
              driver.save_screenshot("unexpected_error.png")
              logging.info("Screenshot of unexpected error saved.")
    finally:
        if driver:
            logging.info("Closing WebDriver.")
            driver.quit()
    return token

if __name__ == "__main__":
    print("Attempting to get Pocket Option token...")
    retrieved_token = get_pocketoption_token()
    if retrieved_token:
        print("\n--- SUCCESS! Retrieved Token ---")
        print(retrieved_token)
        print("---------------------------------")
    else:
        print("\n--- FAILED to retrieve token. Check logs and screenshot. ---")
