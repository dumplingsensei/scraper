import requests
import csv
import time
import json
import re
from datetime import datetime

def clean_price(price):
    if isinstance(price, (int, float)):
        return float(price)
    elif isinstance(price, str):
        return float(re.sub(r'[^\d.]', '', price))
    else:
        return float('inf')  # Use infinity for 'N/A' to put these at the end when sorting

def scrape_pchome(search_term):
    base_url = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
    params = {
        "q": search_term,
        "page": 1,
        "sort": "sale/dc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    results = []
    metadata = {}

    while True:
        response = requests.get(base_url, params=params, headers=headers)
        
        try:
            data = response.json()
            
            if 'prods' in data:
                if not data['prods']:
                    break

                for product in data['prods']:
                    title = product.get('name', 'N/A')
                    price = clean_price(product.get('price', 'N/A'))
                    product_id = product.get('Id', 'N/A')
                    link = f"https://24h.pchome.com.tw/prod/{product_id}" if product_id != 'N/A' else 'N/A'
                    results.append([title, price, link])

                params['page'] += 1
            else:
                # We've reached the end of the results, store metadata
                metadata = {
                    'total_rows': data.get('totalRows', 'N/A'),
                    'total_pages': data.get('totalPage', 'N/A'),
                    'category': data.get('cateName', 'N/A'),
                    'query': data.get('q', 'N/A')
                }
                break

            time.sleep(0.5)  # Be respectful to the server
        except json.JSONDecodeError:
            print("Failed to decode JSON. Response content:")
            print(response.text)
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            break

    return results, metadata

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Price', 'Link'])
        writer.writerows(data)

def main():
    search_term = input("Enter the search term: ")
    results, metadata = scrape_pchome(search_term)
    
    # Sort results by price (lowest to highest)
    sorted_results = sorted(results, key=lambda x: x[1])
    
    # Replace 'inf' values (which were used for sorting) with 'N/A'
    for result in sorted_results:
        if result[1] == float('inf'):
            result[1] = 'N/A'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create filename by replacing spaces with underscores and adding .csv extension
    filename = f"pchome_{search_term.replace(' ', '_')}_{timestamp}.csv"
    
    save_to_csv(sorted_results, filename)
    print(f"Scraped and sorted {len(sorted_results)} results and saved to {filename}")
    print("Metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")



if __name__ == "__main__":
    main()