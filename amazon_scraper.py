from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import logging
import time
import json
import re
from random import randint

class AmazonReviewScraper:
    def __init__(self):
        self.logger = self._setup_logging()
        self.driver = self._setup_driver()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        fh = logging.FileHandler('amazon_scraper.log')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        return logger
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Add random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        chrome_options.add_argument(f'user-agent={user_agents[randint(0, len(user_agents)-1)]}')
        
        return webdriver.Chrome(options=chrome_options)
    
    def extract_asin(self, url):
        """Extract ASIN from Amazon URL"""
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'B[A-Z0-9]{9}',
        ]
        
        for pattern in asin_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def scrape_reviews(self, product_identifier, pages=1):
        """Scrape reviews using Selenium"""
        try:
            asin = self.extract_asin(product_identifier)
            if not asin:
                self.logger.error("Could not extract ASIN from URL")
                return []
                
            self.logger.info(f"Using ASIN: {asin}")
            reviews = []
            
            # Try different URL patterns
            url_patterns = [
                f"https://www.amazon.in/product-reviews/{asin}",
                f"https://www.amazon.in/dp/{asin}/ref=cm_cr_arp_d_product_top?ie=UTF8"
            ]
            
            for base_url in url_patterns:
                self.logger.info(f"Trying URL: {base_url}")
                
                try:
                    # Load the page
                    self.driver.get(base_url)
                    time.sleep(randint(5, 10))  # Random delay
                    
                    # Save page source for debugging
                    with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    
                    # Check if reviews exist
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        '[data-hook="review"], .review, .a-section.review')
                    
                    if review_elements:
                        self.logger.info(f"Found {len(review_elements)} reviews")
                        
                        for review in review_elements:
                            try:
                                review_data = {
                                    'product_id': asin,
                                    'rating': review.find_element(By.CSS_SELECTOR, 
                                        '[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]'
                                    ).text.split(' out of')[0] if review.find_elements(By.CSS_SELECTOR, 
                                        '[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]') else None,
                                    
                                    'title': review.find_element(By.CSS_SELECTOR,
                                        '[data-hook="review-title"]'
                                    ).text.strip() if review.find_elements(By.CSS_SELECTOR,
                                        '[data-hook="review-title"]') else None,
                                    
                                    'text': review.find_element(By.CSS_SELECTOR,
                                        '[data-hook="review-body"]'
                                    ).text.strip() if review.find_elements(By.CSS_SELECTOR,
                                        '[data-hook="review-body"]') else None,
                                    
                                    'date': review.find_element(By.CSS_SELECTOR,
                                        '[data-hook="review-date"]'
                                    ).text if review.find_elements(By.CSS_SELECTOR,
                                        '[data-hook="review-date"]') else None,
                                    
                                    'verified': bool(review.find_elements(By.CSS_SELECTOR,
                                        '[data-hook="avp-badge"]')),
                                    
                                    'reviewer': review.find_element(By.CSS_SELECTOR,
                                        '.a-profile-name'
                                    ).text if review.find_elements(By.CSS_SELECTOR,
                                        '.a-profile-name') else None
                                }
                                
                                if review_data['text']:
                                    reviews.append(review_data)
                                    
                            except Exception as e:
                                self.logger.error(f"Error extracting review data: {str(e)}")
                                continue
                        
                        break  # Successfully found reviews, exit URL pattern loop
                    
                except Exception as e:
                    self.logger.error(f"Error accessing URL {base_url}: {str(e)}")
                    continue
            
            return reviews
            
        finally:
            self.driver.quit()
    
    def save_reviews(self, reviews, filename):
        """Save scraped reviews to CSV and JSON files"""
        try:
            if not reviews:
                self.logger.warning("No reviews to save!")
                return
                
            # Save as CSV
            df = pd.DataFrame(reviews)
            csv_file = f"{filename}.csv"
            df.to_csv(csv_file, index=False)
            self.logger.info(f"Saved {len(reviews)} reviews to {csv_file}")
            
            # Save as JSON
            json_file = f"{filename}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(reviews)} reviews to {json_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving reviews: {str(e)}")