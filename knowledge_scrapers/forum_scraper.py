#!/usr/bin/env python3
"""
Forum Discussion Scraper

This modular scraper extracts discussion content from forums and Q&A sites. Features include:
- Thread and post extraction
- User interaction analysis
- Topic categorization
- Support for popular forum platforms (phpBB, vBulletin, Discourse, etc.)
- Ethical scraping with rate limiting
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
class ForumPost:
    """Represents a forum post with extracted content"""
    url: str
    thread_title: str
    author: str
    content: str
    post_number: int
    timestamp: Optional[str]
    likes_count: Optional[int]
    replies_count: Optional[int]
    forum_category: Optional[str]
    scraped_at: str

@dataclass
class ForumThread:
    """Represents a complete forum thread"""
    url: str
    title: str
    category: str
    author: str
    posts: List[ForumPost]
    views_count: Optional[int]
    replies_count: Optional[int]
    created_at: Optional[str]
    last_post_at: Optional[str]
    scraped_at: str

class ForumScraper:
    """
    Modular forum scraper supporting various forum platforms
    """
    
    def __init__(self, forum_type: str = 'generic', delay_between_requests: float = 1.5):
        self.forum_type = forum_type.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-ForumScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Forum platform-specific configurations
        self.forum_configs = {
            'phpbb': {
                'thread_selector': '.topictitle',
                'post_selector': '.post',
                'content_selector': '.content',
                'author_selector': '.username',
                'timestamp_selector': '.author .responsive-hide'
            },
            'vbulletin': {
                'thread_selector': '.threadtitle',
                'post_selector': '[id^="post_"]',
                'content_selector': '.postcontent',
                'author_selector': '.username_container',
                'timestamp_selector': '.postdate'
            },
            'discourse': {
                'thread_selector': '.topic-title',
                'post_selector': '.topic-post',
                'content_selector': '.cooked',
                'author_selector': '.username',
                'timestamp_selector': '.relative-date'
            },
            'reddit': {
                'thread_selector': '[data-testid="post-content"]',
                'post_selector': '.Comment',
                'content_selector': '[data-testid="comment"]',
                'author_selector': '[data-testid="comment_author_link"]',
                'timestamp_selector': '[data-testid="comment_timestamp"]'
            },
            'generic': {
                'thread_selector': 'h1, .thread-title, .topic-title',
                'post_selector': '.post, .message, .comment',
                'content_selector': '.content, .message-content, .post-content',
                'author_selector': '.author, .username, .user',
                'timestamp_selector': '.timestamp, .date, .time'
            }
        }
    
    def extract_thread_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract thread-level metadata"""
        metadata = {}
        
        # Extract thread title
        title_selectors = ['.thread-title', '.topic-title', 'h1', '.topictitle']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                metadata['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract category/forum name
        category_selectors = ['.breadcrumb a', '.forum-name', '.category-name']
        for selector in category_selectors:
            category_elem = soup.select_one(selector)
            if category_elem:
                metadata['category'] = category_elem.get_text(strip=True)
                break
        
        # Extract view count
        views_patterns = [r'Views?:?\s*(\d+)', r'(\d+)\s*views?']
        page_text = soup.get_text()
        for pattern in views_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    metadata['views_count'] = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        return metadata
    
    def scrape_post(self, post_element, thread_title: str, thread_url: str, post_number: int) -> Optional[ForumPost]:
        """Extract data from a single forum post element"""
        try:
            config = self.forum_configs.get(self.forum_type, self.forum_configs['generic'])
            
            # Extract post content
            content_elem = post_element.select_one(config['content_selector'])
            content = content_elem.get_text(strip=True) if content_elem else 'N/A'
            
            # Skip very short posts (likely not meaningful)
            if len(content) < 10:
                return None
            
            # Extract author
            author_elem = post_element.select_one(config['author_selector'])
            author = author_elem.get_text(strip=True) if author_elem else 'Anonymous'
            
            # Extract timestamp
            timestamp_elem = post_element.select_one(config['timestamp_selector'])
            timestamp = None
            if timestamp_elem:
                timestamp = timestamp_elem.get('datetime') or timestamp_elem.get_text(strip=True)
            
            # Extract engagement metrics
            likes_count = self._extract_number_from_element(post_element, ['like', 'upvote', 'thumbs'])
            replies_count = self._extract_number_from_element(post_element, ['reply', 'response'])
            
            # Extract forum category if available
            category_elem = post_element.select_one('.category, .forum')
            forum_category = category_elem.get_text(strip=True) if category_elem else None
            
            return ForumPost(
                url=thread_url + f"#post{post_number}",
                thread_title=thread_title,
                author=author,
                content=content,
                post_number=post_number,
                timestamp=timestamp,
                likes_count=likes_count,
                replies_count=replies_count,
                forum_category=forum_category,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error extracting post {post_number}: {e}")
            return None
    
    def _extract_number_from_element(self, element: BeautifulSoup, keywords: List[str]) -> Optional[int]:
        """Extract numerical values associated with keywords from an element"""
        element_text = element.get_text().lower()
        
        for keyword in keywords:
            # Look for patterns like "5 likes", "likes: 10", etc.
            patterns = [
                rf'(\d+)\s*{keyword}',
                rf'{keyword}:?\s*(\d+)',
                rf'{keyword}\s*\((\d+)\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, element_text)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def scrape_thread(self, thread_url: str, max_posts: int = 50) -> Optional[ForumThread]:
        """Scrape a complete forum thread"""
        if thread_url in self.visited_urls:
            return None
            
        self.visited_urls.add(thread_url)
        
        try:
            print(f"🔍 Scraping forum thread: {thread_url}")
            time.sleep(self.delay)
            
            response = self.session.get(thread_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch {thread_url}: HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.forum_configs.get(self.forum_type, self.forum_configs['generic'])
            
            # Extract thread metadata
            metadata = self.extract_thread_metadata(soup, thread_url)
            thread_title = metadata.get('title', 'Unknown Thread')
            
            # Find all posts in the thread
            post_elements = soup.select(config['post_selector'])
            posts = []
            
            for i, post_element in enumerate(post_elements[:max_posts], 1):
                post = self.scrape_post(post_element, thread_title, thread_url, i)
                if post:
                    posts.append(post)
            
            if not posts:
                print(f"⚠️  No posts found in thread: {thread_url}")
                return None
            
            # Extract thread-level information
            first_post = posts[0] if posts else None
            
            return ForumThread(
                url=thread_url,
                title=thread_title,
                category=metadata.get('category', 'Unknown'),
                author=first_post.author if first_post else 'Unknown',
                posts=posts,
                views_count=metadata.get('views_count'),
                replies_count=len(posts) - 1,  # Replies = total posts - original post
                created_at=first_post.timestamp if first_post else None,
                last_post_at=posts[-1].timestamp if posts else None,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error scraping thread {thread_url}: {e}")
            return None
    
    def discover_threads(self, forum_url: str, max_threads: int = 20) -> List[str]:
        """Discover thread URLs from a forum index or category page"""
        thread_urls = []
        
        try:
            response = self.session.get(forum_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch forum: {forum_url}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.forum_configs.get(self.forum_type, self.forum_configs['generic'])
            
            # Look for thread links
            thread_selectors = [
                'a[href*="/thread/"]',
                'a[href*="/topic/"]',
                'a[href*="/t/"]',
                'a[href*="/viewtopic.php"]',
                '.threadtitle a',
                '.topictitle'
            ]
            
            for selector in thread_selectors:
                thread_links = soup.select(selector)
                for link in thread_links[:max_threads]:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(forum_url, href)
                        thread_urls.append(full_url)
                        
                if thread_urls:
                    break  # Found threads with this selector
                    
        except Exception as e:
            print(f"❌ Error discovering threads from {forum_url}: {e}")
        
        return list(set(thread_urls))[:max_threads]  # Remove duplicates
    
    def scrape_forum(self, forum_url: str, max_threads: int = 10, max_posts_per_thread: int = 25) -> List[ForumThread]:
        """Scrape multiple threads from a forum"""
        print(f"🚀 Starting forum scraping from: {forum_url}")
        
        thread_urls = self.discover_threads(forum_url, max_threads)
        scraped_threads = []
        
        for url in thread_urls:
            thread = self.scrape_thread(url, max_posts_per_thread)
            if thread:
                scraped_threads.append(thread)
                
        print(f"✅ Scraped {len(scraped_threads)} threads from forum")
        return scraped_threads
    
    def save_results(self, threads: List[ForumThread], filename: str = None):
        """Save scraped forum threads to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"forum_scrape_{self.forum_type}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        threads_data = []
        for thread in threads:
            thread_dict = thread.__dict__.copy()
            thread_dict['posts'] = [post.__dict__ for post in thread.posts]
            threads_data.append(thread_dict)
        
        with open(filepath, 'w') as f:
            json.dump({
                'forum_type': self.forum_type,
                'total_threads': len(threads),
                'total_posts': sum(len(thread.posts) for thread in threads),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'threads': threads_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples
if __name__ == '__main__':
    # Example: Scrape a phpBB forum
    phpbb_scraper = ForumScraper('phpbb', delay_between_requests=2.0)
    
    # Example: Scrape a Discourse forum
    discourse_scraper = ForumScraper('discourse', delay_between_requests=1.5)
    
    # Example: Generic forum scraper
    generic_scraper = ForumScraper('generic', delay_between_requests=1.0)
    
    print("Forum Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = ForumScraper('phpbb')")
    print("  threads = scraper.scrape_forum('https://forum.example.com')")
    print("  scraper.save_results(threads)")
