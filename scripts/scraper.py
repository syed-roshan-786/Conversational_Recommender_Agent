import requests
from bs4 import BeautifulSoup
import json
import os

CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_FILE = "data/catalog.json"

def scrape_catalog():
    print(f"Scraping {CATALOG_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    try:
        response = requests.get(CATALOG_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a naive heuristic based on standard HTML structures.
        # Since SHL page structure may vary or be JS rendered, this serves as a fallback.
        items = []
        
        # Assuming product cards are in some identifiable container, e.g., an article or div class
        # In a real dynamic environment, we might need Playwright. 
        # But for this assignment constraint, we do a basic parse and default to the mock data if empty.
        product_cards = soup.find_all('div', class_=lambda x: x and 'product' in x.lower())
        
        if not product_cards:
            print("Warning: Could not find product cards. The page might be client-side rendered or structure changed.")
            print("Using existing mock data if available.")
            return

        for card in product_cards:
            title_el = card.find(['h2', 'h3'])
            link_el = card.find('a')
            desc_el = card.find('p')
            
            if title_el and link_el:
                name = title_el.get_text(strip=True)
                url = link_el.get('href')
                if not url.startswith('http'):
                    url = "https://www.shl.com" + url
                    
                desc = desc_el.get_text(strip=True) if desc_el else "SHL Assessment"
                
                items.append({
                    "name": name,
                    "url": url,
                    "description": desc,
                    "category": "Assessment",
                    "skills_measured": ["General"],
                    "duration": "Untimed",
                    "test_type": "K",
                    "keywords": [name.lower()]
                })
        
        if items:
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(items, f, indent=2)
            print(f"Successfully scraped {len(items)} items to {OUTPUT_FILE}.")

    except Exception as e:
        print(f"Error scraping catalog: {e}")

if __name__ == "__main__":
    scrape_catalog()
