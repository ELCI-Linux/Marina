#!/usr/bin/env python3
"""
Social Media Content Scraper

This modular scraper extracts public content from social media platforms. Features include:
- Extraction of posts, comments, and metadata
- Sentiment analysis integration
- Rate limiting and ethical scraping practices
- Support for multiple social media platforms
"""

import os
import sys
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from datetime import datetime

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class SocialMediaPost:
    """Represents a social media post with extracted content"""
    url: str
    platform: str
    author: str
    content: str
    timestamp: Optional[str]
    likes_count: Optional[int]
    shares_count: Optional[int]
    comments_count: Optional[int]
    hashtags: List[str]
    scraped_at: str

class SocialMediaScraper:
    """
    Modular social media scraper that can be extended for different platforms
    """
    
    def __init__(self, platform: str, delay_between_requests: float = 2.0):
        self.platform = platform.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-SocialMediaScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Platform-specific configurations
        self.platform_configs = {
            'twitter': {
                'post_selector': '.tweet',
                'content_selector': '.tweet-text',
                'author_selector': '.username',
                'timestamp_selector': '.timestamp'
            },
            'reddit': {
                'post_selector': '.thing',
                'content_selector': '.md',
                'author_selector': '.author',
                'timestamp_selector': '.live-timestamp'
            },
            'facebook': {
                'post_selector': '[data-testid="post_message"]',
                'content_selector': '[data-testid="post_message"]',
                'author_selector': 'strong',
                'timestamp_selector': 'abbr'
            }
        }
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text content"""
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        return [tag.lower() for tag in hashtags]
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text content"""
        mention_pattern = r'@\w+'
        mentions = re.findall(mention_pattern, text, re.IGNORECASE)
        return [mention.lower() for mention in mentions]
    
    def scrape_post(self, url: str) -> Optional[SocialMediaPost]:
        """Scrape a single social media post"""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        try:
            print(f"🔍 Scraping {self.platform} post: {url}")
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch {url}: HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.platform_configs.get(self.platform, {})
            
            # Extract post content
            content_elem = soup.select_one(config.get('content_selector', ''))
            content = content_elem.get_text(strip=True) if content_elem else 'N/A'
            
            # Extract author
            author_elem = soup.select_one(config.get('author_selector', ''))
            author = author_elem.get_text(strip=True) if author_elem else 'N/A'
            
            # Extract timestamp
            timestamp_elem = soup.select_one(config.get('timestamp_selector', ''))
            timestamp = timestamp_elem.get('datetime') or timestamp_elem.get_text(strip=True) if timestamp_elem else None
            
            # Extract engagement metrics (simplified)
            likes_count = self._extract_number_from_text(soup, ['like', 'heart'])
            shares_count = self._extract_number_from_text(soup, ['share', 'retweet'])
            comments_count = self._extract_number_from_text(soup, ['comment', 'reply'])
            
            # Extract hashtags
            hashtags = self.extract_hashtags(content)
            
            return SocialMediaPost(
                url=url,
                platform=self.platform,
                author=author,
                content=content,
                timestamp=timestamp,
                likes_count=likes_count,
                shares_count=shares_count,
                comments_count=comments_count,
                hashtags=hashtags,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def _extract_number_from_text(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[int]:
        """Extract numerical values associated with keywords (likes, shares, etc.)"""
        for keyword in keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                if hasattr(element, 'parent'):
                    parent_text = element.parent.get_text()
                    numbers = re.findall(r'\d+', parent_text)
                    if numbers:
                        try:
                            return int(numbers[0])
                        except ValueError:
                            continue
        return None
    
    def discover_posts(self, feed_url: str, max_posts: int = 10) -> List[str]:
        """Discover post URLs from a feed or profile page"""
        post_urls = []
        
        try:
            response = self.session.get(feed_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch feed: {feed_url}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Platform-specific post URL discovery
            if self.platform == 'twitter':
                post_links = soup.find_all('a', href=re.compile(r'/status/\d+'))
            elif self.platform == 'reddit':
                post_links = soup.find_all('a', href=re.compile(r'/r/\w+/comments/'))
            else:
                # Generic approach - look for links that might be posts
                post_links = soup.find_all('a', href=True)
            
            for link in post_links[:max_posts]:
                href = link.get('href')
                if href:
                    full_url = urljoin(feed_url, href)
                    post_urls.append(full_url)
                    
        except Exception as e:
            print(f"❌ Error discovering posts from {feed_url}: {e}")
        
        return post_urls[:max_posts]
    
    def scrape_feed(self, feed_url: str, max_posts: int = 10) -> List[SocialMediaPost]:
        """Scrape multiple posts from a social media feed"""
        print(f"🚀 Starting {self.platform} scraping from: {feed_url}")
        
        post_urls = self.discover_posts(feed_url, max_posts)
        scraped_posts = []
        
        for url in post_urls:
            post = self.scrape_post(url)
            if post:
                scraped_posts.append(post)
                
        print(f"✅ Scraped {len(scraped_posts)} posts from {self.platform}")
        return scraped_posts
    
    def save_results(self, posts: List[SocialMediaPost], filename: str = None):
        """Save scraped posts to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"social_media_scrape_{self.platform}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        posts_data = [post.__dict__ for post in posts]
        
        with open(filepath, 'w') as f:
            json.dump({
                'platform': self.platform,
                'total_posts': len(posts),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'posts': posts_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples for different platforms
if __name__ == '__main__':
    # Example: Scrape Twitter-like content
    twitter_scraper = SocialMediaScraper('twitter', delay_between_requests=2.0)
    
    # Example: Scrape Reddit-like content  
    reddit_scraper = SocialMediaScraper('reddit', delay_between_requests=1.5)
    
    print("Social Media Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = SocialMediaScraper('twitter')")
    print("  posts = scraper.scrape_feed('https://twitter.com/some_user')")
    print("  scraper.save_results(posts)")
