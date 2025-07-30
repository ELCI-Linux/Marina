#!/usr/bin/env python3
"""
Real Estate Listings Scraper

This modular scraper extracts property listings from real estate websites. Features include:
- Property details extraction (price, location, bedrooms, bathrooms, size)
- Property categorization (house, apartment, condo)
- Support for major real estate sites (Zillow, Realtor.com, Trulia)
- Geographic data extraction
- Rate limiting and ethical scraping practices
"""

import os
import sys
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from urllib.parse import urljoin
from dataclasses import dataclass
from datetime import datetime

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class PropertyListing:
    """Represents a real estate property listing with extracted details"""
    url: str
    title: str
    address: str
    price: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    property_type: Optional[str]
    listing_date: Optional[str]
    agent_name: Optional[str]
    agency: Optional[str]
    description: str
    features: List[str]
    neighborhood: Optional[str]
    scraped_at: str

class RealEstateScraper:
    """
    Modular real estate listing scraper supporting various property websites
    """
    
    def __init__(self, platform: str = 'zillow', delay_between_requests: float = 2.0):
        self.platform = platform.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-RealEstateScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Platform-specific configurations
        self.platform_configs = {
            'zillow': {
                'listing_selector': '.list-card',
                'title_selector': '.list-card-heading',
                'price_selector': '.list-card-price',
                'address_selector': '.list-card-addr',
                'beds_selector': '.list-card-details li:nth-child(1)',
                'baths_selector': '.list-card-details li:nth-child(2)',
                'sqft_selector': '.list-card-details li:nth-child(3)',
                'agent_selector': '.list-card-agent'
            },
            'realtor': {
                'listing_selector': '.component_property-card',
                'title_selector': '.listing-price',
                'price_selector': '.data-price',
                'address_selector': '.listing-address',
                'beds_selector': '.property-beds',
                'baths_selector': '.property-baths',
                'sqft_selector': '.property-sqft',
                'agent_selector': '.listing-agent'
            },
            'trulia': {
                'listing_selector': '.Grid__CellBox',
                'title_selector': '.MediaBlock__Title',
                'price_selector': '.Text__TextBase',
                'address_selector': '.Text__TextBase',
                'beds_selector': '.BedBathSqftText',
                'baths_selector': '.BedBathSqftText',
                'sqft_selector': '.BedBathSqftText',
                'agent_selector': '.ContactInfoText'
            }
        }
    
    def extract_numeric_value(self, text: str, pattern: str) -> Optional[float]:
        """Extract numeric values from text using regex patterns"""
        if not text:
            return None
            
        match = re.search(pattern, text.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        return None
    
    def extract_property_type(self, title: str, description: str) -> str:
        """Classify property type based on title and description"""
        text = f"{title} {description}".lower()
        
        type_patterns = {
            'House': [r'\bhouse\b', r'\bhome\b', r'\bsingle.family\b'],
            'Apartment': [r'\bapartment\b', r'\bapt\b', r'\bunit\b'],
            'Condo': [r'\bcondo\b', r'\bcondominium\b'],
            'Townhouse': [r'\btownhouse\b', r'\btownhome\b'],
            'Duplex': [r'\bduplex\b'],
            'Mobile Home': [r'\bmobile\b', r'\btrailer\b'],
            'Land': [r'\bland\b', r'\blot\b']
        }
        
        for prop_type, patterns in type_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                return prop_type
        
        return 'Unknown'
    
    def extract_features(self, description: str) -> List[str]:
        """Extract property features from description"""
        features = []
        
        feature_patterns = [
            r'\bpool\b', r'\bgarage\b', r'\bfireplace\b', r'\bbalcony\b',
            r'\bpatio\b', r'\bgarden\b', r'\blaundry\b', r'\bbasement\b',
            r'\battic\b', r'\bwalk.in.closet\b', r'\bcentral.air\b',
            r'\bhardwood.floors\b', r'\bcarpet\b', r'\btile\b',
            r'\bupdated.kitchen\b', r'\bmaster.suite\b'
        ]
        
        description_lower = description.lower()
        for pattern in feature_patterns:
            if re.search(pattern, description_lower):
                feature = pattern.replace(r'\b', '').replace('.', ' ')
                features.append(feature)
        
        return features
    
    def scrape_property(self, property_element) -> Optional[PropertyListing]:
        """Extract data from a single property listing element"""
        try:
            config = self.platform_configs.get(self.platform, {})
            
            # Extract title/heading
            title_elem = property_element.select_one(config.get('title_selector', ''))
            title = title_elem.get_text(strip=True) if title_elem else 'Property Listing'
            
            # Extract price
            price_elem = property_element.select_one(config.get('price_selector', ''))
            price = price_elem.get_text(strip=True) if price_elem else None
            
            # Extract address
            address_elem = property_element.select_one(config.get('address_selector', ''))
            address = address_elem.get_text(strip=True) if address_elem else 'Address not available'
            
            # Extract property details
            beds_elem = property_element.select_one(config.get('beds_selector', ''))
            bedrooms = None
            if beds_elem:
                beds_text = beds_elem.get_text()
                bedrooms = self.extract_numeric_value(beds_text, r'(\d+)\s*bed')
                if bedrooms:
                    bedrooms = int(bedrooms)
            
            baths_elem = property_element.select_one(config.get('baths_selector', ''))
            bathrooms = None
            if baths_elem:
                baths_text = baths_elem.get_text()
                bathrooms = self.extract_numeric_value(baths_text, r'(\d+(?:\.\d+)?)\s*bath')
            
            sqft_elem = property_element.select_one(config.get('sqft_selector', ''))
            square_feet = None
            if sqft_elem:
                sqft_text = sqft_elem.get_text()
                square_feet = self.extract_numeric_value(sqft_text, r'(\d+(?:,\d+)?)\s*sq')
                if square_feet:
                    square_feet = int(square_feet)
            
            # Extract agent information
            agent_elem = property_element.select_one(config.get('agent_selector', ''))
            agent_name = agent_elem.get_text(strip=True) if agent_elem else None
            
            # Generate property URL
            link_elem = property_element.find('a', href=True)
            property_url = urljoin('https://example-realestate.com', link_elem['href']) if link_elem else 'Unknown'
            
            # Extract description (simplified - would normally be on detail page)
            description = f"Property listing for {address}"
            
            # Derive additional metadata
            property_type = self.extract_property_type(title, description)
            features = self.extract_features(description)
            
            # Extract neighborhood from address
            neighborhood = None
            if ',' in address:
                parts = address.split(',')
                if len(parts) > 1:
                    neighborhood = parts[-2].strip()
            
            return PropertyListing(
                url=property_url,
                title=title,
                address=address,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                property_type=property_type,
                listing_date=None,  # Would need to extract from detail page
                agent_name=agent_name,
                agency=None,  # Would need to extract from detail page
                description=description,
                features=features,
                neighborhood=neighborhood,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error extracting property listing: {e}")
            return None
    
    def discover_properties(self, search_url: str, max_properties: int = 20) -> List[PropertyListing]:
        """Discover and scrape property listings from a real estate platform"""
        properties = []
        
        try:
            print(f"🏠 Starting real estate scraping from: {search_url}")
            time.sleep(self.delay)
            
            response = self.session.get(search_url, timeout=20)
            if response.status_code != 200:
                print(f"❌ Failed to fetch property listings: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.platform_configs.get(self.platform, {})
            
            # Find property elements
            property_elements = soup.select(config.get('listing_selector', '.property'))
            
            for property_element in property_elements[:max_properties]:
                property_listing = self.scrape_property(property_element)
                if property_listing:
                    properties.append(property_listing)
            
            print(f"✅ Scraped {len(properties)} properties from {self.platform}")
            
        except Exception as e:
            print(f"❌ Error discovering properties: {e}")
        
        return properties
    
    def analyze_market_data(self, properties: List[PropertyListing]) -> Dict:
        """Analyze market data from scraped properties"""
        if not properties:
            return {}
        
        # Extract numeric prices for analysis
        prices = []
        for prop in properties:
            if prop.price:
                price_match = re.search(r'\$?([\d,]+)', prop.price.replace(',', ''))
                if price_match:
                    try:
                        prices.append(int(price_match.group(1)))
                    except ValueError:
                        continue
        
        analysis = {
            'total_properties': len(properties),
            'property_types': {},
            'neighborhoods': {},
            'avg_bedrooms': 0,
            'avg_bathrooms': 0,
            'avg_sqft': 0
        }
        
        # Property type distribution
        for prop in properties:
            prop_type = prop.property_type or 'Unknown'
            analysis['property_types'][prop_type] = analysis['property_types'].get(prop_type, 0) + 1
        
        # Neighborhood distribution
        for prop in properties:
            neighborhood = prop.neighborhood or 'Unknown'
            analysis['neighborhoods'][neighborhood] = analysis['neighborhoods'].get(neighborhood, 0) + 1
        
        # Calculate averages
        valid_bedrooms = [p.bedrooms for p in properties if p.bedrooms is not None]
        valid_bathrooms = [p.bathrooms for p in properties if p.bathrooms is not None]
        valid_sqft = [p.square_feet for p in properties if p.square_feet is not None]
        
        if valid_bedrooms:
            analysis['avg_bedrooms'] = sum(valid_bedrooms) / len(valid_bedrooms)
        if valid_bathrooms:
            analysis['avg_bathrooms'] = sum(valid_bathrooms) / len(valid_bathrooms)
        if valid_sqft:
            analysis['avg_sqft'] = sum(valid_sqft) / len(valid_sqft)
        
        # Price analysis
        if prices:
            analysis['price_stats'] = {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'median_price': sorted(prices)[len(prices) // 2]
            }
        
        return analysis
    
    def save_results(self, properties: List[PropertyListing], filename: str = None):
        """Save scraped property listings to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"real_estate_scrape_{self.platform}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        properties_data = [prop.__dict__ for prop in properties]
        
        # Generate market analysis
        market_analysis = self.analyze_market_data(properties)
        
        with open(filepath, 'w') as f:
            json.dump({
                'platform': self.platform,
                'total_properties': len(properties),
                'market_analysis': market_analysis,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'properties': properties_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples
if __name__ == '__main__':
    # Example: Scrape Zillow for properties
    zillow_scraper = RealEstateScraper('zillow', delay_between_requests=3.0)
    
    # Discover properties
    properties = zillow_scraper.discover_properties('https://www.zillow.com/homes/', max_properties=15)
    
    if properties:
        print(f"Found {len(properties)} property listings:")
        for prop in properties[:3]:  # Show first 3
            print(f"- {prop.title}")
            print(f"  Address: {prop.address}")
            print(f"  Price: {prop.price}")
            print(f"  Type: {prop.property_type}")
            print()
        
        # Analyze market data
        analysis = zillow_scraper.analyze_market_data(properties)
        if analysis:
            print("Market Analysis:")
            print(f"  Property Types: {analysis.get('property_types', {})}")
            print(f"  Average Bedrooms: {analysis.get('avg_bedrooms', 0):.1f}")
            print(f"  Average Square Feet: {analysis.get('avg_sqft', 0):.0f}")
        
        zillow_scraper.save_results(properties)
    
    print("Real Estate Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = RealEstateScraper('zillow')")
    print("  properties = scraper.discover_properties('https://www.zillow.com/search/')")
    print("  scraper.save_results(properties)")
