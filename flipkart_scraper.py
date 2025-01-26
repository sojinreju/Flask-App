from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

def scrape_reviews(url, timeout=20):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    reviews = []

    try:
        # Set page load timeout and open the URL
        driver.set_page_load_timeout(timeout)
        driver.get(url)

        # Scroll to the bottom of the page to load all elements
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Identify and scrape reviews from Flipkart
        if "flipkart.com" in url.lower():
            # Scrape review text elements
            review_text_elements = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ZmyHeo"))
            )

            # Click on all "read more" buttons if they exist
            while True:
                # Find all the "read more" buttons
                read_more_buttons = driver.find_elements(By.CLASS_NAME, "b4x-fr")
                if not read_more_buttons:
                    break  # No more "Read More" buttons, stop clicking

                # Click each "Read More" button and wait for the page to load more reviews
                for button in read_more_buttons:
                    try:
                        ActionChains(driver).move_to_element(button).click().perform()  # Move to button and click it
                        time.sleep(2)  # Wait for new reviews to load
                    except Exception as e:
                        print(f"Error clicking 'Read More' button: {e}")

                # Re-fetch review text after clicking the "Read More" buttons
                review_text_elements = driver.find_elements(By.CSS_SELECTOR, ".ZmyHeo")
                
                # If reviews have been added, break out of the loop and proceed
                if len(review_text_elements) > len(reviews):
                    break

            # Collect all reviews
            reviews = [text.text.strip() for text in review_text_elements if text.text.strip()]

        # Check if reviews are empty and notify
        if not reviews:
            print(f"No reviews found for URL: {url}")

    except Exception as e:
        print(f"Scraping error for {url}: {e}")
    finally:
        driver.quit()

    return reviews


