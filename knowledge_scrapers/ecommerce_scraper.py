#!/usr/bin/env python3
"""
E-commerce Product Scraper

This scraper intelligently extracts product information from e-commerce websites. Features include:
- Automatic discovery of product links via typical structures.
- Extraction of product details such as price, description, and availability.
- Modular architecture to extend for different e-commerce platforms.
- Respectful rate limiting and error management.
"""

import os
import sys
import requests
import json
import time
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class ProductInfo:
    url: str
    title: str
    price: Optional[str]
    description: Optional[str]
    availability: Optional[str]
    scraped_at: str

class EcommerceScraper:
    def __init__(self, root_url: str, delay_between_requests: float = 1.0):
        self.root_url = root_url
        self.delay = delay_between_requests
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-EcommerceScraper/1.0 (Educational Purpose)'
        })

    def scrape_product_page(self, url: str) -> Optional[ProductInfo]:
        if url in self.visited_urls:
            return None
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch {url}: HTTP {response.status_code}")
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
            title_elem = soup.find('h1', class_='product-title') or soup.find('title')
            price_elem = soup.find('span', class_='price')
            description_elem = soup.find('div', class_='product-description')
            availability_elem = soup.find('div', class_='availability-status')

            return ProductInfo(
                url=url,
                title=title_elem.get_text(strip=True) if title_elem else 'N/A',
                price=price_elem.get_text(strip=True) if price_elem else 'N/A',
                description=description_elem.get_text(strip=True) if description_elem else 'N/A',
                availability=availability_elem.get_text(strip=True) if availability_elem else 'N/A',
                scraped_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None

    def start_scraping(self, max_pages: int = 10) -> List[ProductInfo]:
        # Placeholder for actual product page discovery logic
        product_urls = self.discover_product_links()[:max_pages]
        products = []
        for url in product_urls:
            product_info = self.scrape_product_page(url)
            if product_info:
                products.append(product_info)
        return products

    def discover_product_links(self) -> List[str]:
        # Placeholder method to discover product URLs from the main page or sitemap
        return [
            urljoin(self.root_url, f'/product/{i}') for i in range(1, 21)  # Example product URLs
        ]

if __name__ == '__main__':
    scraper = EcommerceScraper(root_url='https://example.com')
    products = scraper.start_scraping(max_pages=5)
    print(json.dumps([product.__dict__ for product in products], indent=2))

