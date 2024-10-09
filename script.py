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

# Path to the ChromeDriver executable in the same folder as this script
chrome_driver_path = "chromedriver.exe"

# Set up Chrome options for headless mode if you don't want a visible browser window
chrome_options = Options()
chrome_options.add_argument("--headless")  # Runs Chrome in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

# Initialize Flask app
app = Flask(__name__)

@app.route('/extract-careers', methods=['POST'])
def extract_careers():
    print("[INFO] Received request to extract careers pages.")
    emails = request.json.get('emails', [])
    if not emails:
        print("[ERROR] No emails provided in the request.")
        return jsonify({"error": "No emails provided"}), 400

    # Extract domains from emails
    domains = [re.search(r"@([\w.-]+)", email).group(1) for email in emails if re.search(r"@([\w.-]+)", email)]
    print(f"[INFO] Extracted domains: {domains}")

    results = {}
    for domain in domains:
        print(f"[INFO] Processing domain: {domain}")
        # Initialize the WebDriver
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
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

            # Store the cleaned content in the results
            results[domain] = cleaned_content
            print(f"[INFO] Stored cleaned content for domain: {domain}")

        except Exception as e:
            results[domain] = f"An error occurred: {e}"
            print(f"[ERROR] An error occurred while processing domain {domain}: {e}")

        finally:
            # Close the WebDriver
            driver.quit()
            print(f"[INFO] Closed WebDriver for domain: {domain}")

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)