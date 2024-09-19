from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_total_pages(driver):
    try:
        next_page_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='rightBtn']/a/img"))
        )
        driver.execute_script("arguments[0].click();", next_page_button)
        
        WebDriverWait(driver, 10).until(EC.staleness_of(next_page_button))
        
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        max_page = query_params.get('maxPage', [1])[0]
        return int(max_page)
    except (NoSuchElementException, TimeoutException):
        print("Could not find or click 'next page' button. Assuming only one page.")
        return 1
    except Exception as e:
        print(f"Error getting total pages: {e}")
        return 1

def clean_price(price):
    if isinstance(price, (int, float)):
        return price
    elif isinstance(price, str):
        cleaned = re.sub(r'[^\d.]', '', price)
        return float(cleaned) if cleaned else float('inf')
    else:
        return float('inf')

def scrape_momo(search_term):
    driver = setup_driver()
    all_products = []

    try:
        base_url = f'https://m.momoshop.com.tw/search.momo?searchKeyword={search_term}&searchType=1&cateLevel=-1&ent=k&_isFuzzy=0'
        driver.get(base_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.goodsItemLi"))
        )
        
        total_pages = get_total_pages(driver)
        print(f"Total pages to scrape: {total_pages}")

        for page in range(1, total_pages + 1):
            url = f'https://m.momoshop.com.tw/search.momo?searchKeyword={search_term}&searchType=1&cateLevel=-1&curPage={page}&maxPage={total_pages}&minPage=1&_isFuzzy=0'
            print(f"Scraping page {page}/{total_pages}: {url}")
            
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.goodsItemLi"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            items = soup.select('li.goodsItemLi')
            
            for item in items:
                title = item.select_one('h3.prdName').text.strip() if item.select_one('h3.prdName') else 'N/A'
                price = item.select_one('b.price').text.strip() if item.select_one('b.price') else 'N/A'
                price = clean_price(price)
                all_products.append({'Title': title, 'Price': price})
            
            time.sleep(0.5)  # Be respectful to the server
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    return all_products

def sort_products_by_price(products):
    return sorted(products, key=lambda x: x['Price'], reverse=True)

def format_data_for_csv(products):
    return [[product['Title'], product['Price']] for product in products]

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Price'])
        writer.writerows(data)

def main():
    search_term = input("Enter the search term: ")
    results = scrape_momo(search_term)
    
    if results:
        sorted_results = sort_products_by_price(results)
        formatted_data = format_data_for_csv(sorted_results)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'{search_term.replace(' ', '_')}_products_{timestamp}.csv'

        save_to_csv(formatted_data, filename)
        print(f"\nScraped and sorted {len(sorted_results)} results and saved to {filename}")
    else:
        print("No product data collected. CSV file not created.")

if __name__ == "__main__":
    main()