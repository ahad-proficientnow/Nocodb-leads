import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import requests
from flask import Flask, request, jsonify
import re

# Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize Flask app
app = Flask(__name__)

def get_chrome_version():
    try:
        version = subprocess.check_output(["google-chrome", "--version"]).decode().strip().split()[-1]
        return version
    except Exception as e:
        print(f"Error getting Chrome version: {e}")
        return None

def get_chromedriver_version():
    try:
        version = subprocess.check_output(["chromedriver", "--version"]).decode().strip().split()[1]
        return version
    except Exception as e:
        print(f"Error getting ChromeDriver version: {e}")
        return None

def check_versions():
    chrome_version = get_chrome_version()
    chromedriver_version = get_chromedriver_version()
    print(f"Chrome version: {chrome_version}")
    print(f"ChromeDriver version: {chromedriver_version}")
    if chrome_version and chromedriver_version:
        chrome_major = chrome_version.split('.')[0]
        chromedriver_major = chromedriver_version.split('.')[0]
        if chrome_major != chromedriver_major:
            print(f"Warning: Chrome ({chrome_version}) and ChromeDriver ({chromedriver_version}) major versions do not match.")
            print("Please update ChromeDriver to match your Chrome version.")
            print("You can download the correct version from: https://storage.googleapis.com/chrome-for-testing-public/CHROME_VERSION/linux64/chromedriver-linux64.zip")
            print("Replace CHROME_VERSION with your Chrome version (e.g., 128.0.6613.86)")
            return False
    else:
        print("Warning: Unable to determine Chrome or ChromeDriver version.")
        return False
    return True

@app.route('/extract-careers', methods=['POST'])
def extract_careers():
    if not check_versions():
        return jsonify({"error": "Chrome and ChromeDriver versions are incompatible"}), 500

    print("[INFO] Received request to extract careers page.")
    email = request.json.get('email', '')
    if not email:
        print("[ERROR] No email provided in the request.")
        return jsonify({"error": "No email provided"}), 400

    # Extract domain from email
    domain_match = re.search(r"@([\w.-]+)", email)
    if not domain_match:
        print("[ERROR] Invalid email format.")
        return jsonify({"error": "Invalid email format"}), 400
    domain = domain_match.group(1)
    print(f"[INFO] Extracted domain: {domain}")

    # Extract name from domain
    name = domain.split('.')[0].capitalize()
    print(f"[INFO] Extracted name: {name}")

    try:
        # Initialize the WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        
        careers_url = f"https://{domain}/careers"
        print(f"[INFO] Checking if careers page exists at: {careers_url}")

        # Check if the {website}/careers page exists with a GET request instead of HEAD
        response = requests.get(careers_url, allow_redirects=True)
        if response.status_code == 200:
            print(f"[INFO] Careers page found at: {careers_url}")
            url = careers_url
        else:
            print(f"[INFO] Careers page not found. Performing Google search for jobs at {domain}...")
            # If the /careers page doesn't exist, perform a Google search
            driver.get("https://www.google.com")
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(f"jobs at {domain}")
            search_box.send_keys(Keys.RETURN)

            # Wait for search results to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))
            
            # Get the links from the first 10 search results
            search_results = driver.find_elements(By.CSS_SELECTOR, "h3")[:10]
            url = None
            for result in search_results:
                link_element = result.find_element(By.XPATH, "..")
                link = link_element.get_attribute("href")
                print(f"[INFO] Found search result link: {link}")
                # Check if the link matches the domain
                if domain in link:
                    url = link
                    print(f"[INFO] Matching link found: {url}")
                    break

            # If no matching link is found, use the first link as a fallback
            if not url:
                url = search_results[0].find_element(By.XPATH, "..").get_attribute("href")
                print(f"[INFO] No matching link found. Using first search result: {url}")

        # Load the appropriate URL
        print(f"[INFO] Loading URL: {url}")
        driver.get(url)

        # Wait for the page to load the dynamic content
        time.sleep(5)  # Adjust time as needed, or use WebDriverWait for better control

        # Get the rendered HTML content
        html_content = driver.page_source
        print("[INFO] Page content retrieved successfully.")

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the <main> content if it exists; otherwise, use the entire <body>
        main_content = soup.find('main')
        if main_content is None:
            main_content = soup.body
        print("[INFO] Extracted main content from the page.")

        # Remove all <nav> and <script> elements from the content
        for tag in main_content.find_all(['nav', 'script']):
            tag.decompose()
        print("[INFO] Removed <nav> and <script> elements from the content.")

        # Function to clean the element by removing class, id, and style attributes but preserving <a> with hrefs
        def clean_element(element):
            for tag in element.find_all(True):  # Finds all tags (elements)
                # Preserve <a> tags with href attributes
                if tag.name == 'a' and tag.has_attr('href'):
                    # Remove all attributes except 'href'
                    tag.attrs = {'href': tag['href']}
                else:
                    # For other tags, remove all attributes
                    tag.attrs = {}
        
        # Clean the main content
        clean_element(main_content)
        print("[INFO] Cleaned the main content by removing unnecessary attributes.")

        # Convert the cleaned content back to a string
        cleaned_content = str(main_content)

        # Prepare the response data
        response_data = {
            "name": name,
            "domain": domain,
            "careers_page": url,
            "raw_body": cleaned_content
        }
        print(f"[INFO] Prepared response data for domain: {domain}")

    except Exception as e:
        response_data = {
            "name": name,
            "domain": domain,
            "careers_page": None,
            "raw_body": f"An error occurred: {str(e)}"
        }
        print(f"[ERROR] An error occurred while processing domain {domain}: {str(e)}")

    finally:
        # Close the WebDriver
        if 'driver' in locals():
            driver.quit()
            print(f"[INFO] Closed WebDriver for domain: {domain}")

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)