#!/usr/bin/env python3
"""
Marina Sitemap-Based Alphabetical Scraper

This module implements intelligent alphabetical scraping of websites using sitemaps
and robots.txt discovery. It systematically crawls sites in alphabetical order
for comprehensive knowledge acquisition.

Features:
- Automatic sitemap discovery from robots.txt
- Alphabetical URL sorting for systematic crawling
- Quality-based content filtering
- Marina corpus integration
- Respectful rate limiting
"""

import os
import sys
import requests
import json
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import datetime
from dataclasses import dataclass
import logging

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning.llm_builder.crawler.page_deconstructor import PageDeconstructor
from feedback.neocorpus_builder import NeocorpusBuilder

@dataclass
class ScrapedPage:
    """Represents a scraped page with metadata."""
    url: str
    title: str
    content: str
    topics: List[str]
    word_count: int
    quality_score: float
    scraped_at: datetime.datetime
    sitemap_priority: Optional[float] = None
    sitemap_lastmod: Optional[datetime.datetime] = None

class SitemapParser:
    """Handles sitemap discovery and parsing."""
    
    def __init__(self, base_url: str, user_agent: str = 'Marina-SitemapScraper/1.0'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.parsed_domain = urlparse(base_url)
        
    def discover_sitemaps(self) -> List[str]:
        """Discover sitemaps from robots.txt and common locations."""
        sitemaps = []
        
        # Try robots.txt first
        robots_url = urljoin(self.base_url, '/robots.txt')
        try:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # Extract sitemap URLs from robots.txt
            if hasattr(rp, 'site_maps') and rp.site_maps():
                sitemaps.extend(rp.site_maps())
                print(f"📍 Found {len(rp.site_maps())} sitemaps in robots.txt")
                
        except Exception as e:
            print(f"⚠️  Could not read robots.txt: {e}")
        
        # Try common sitemap locations
        common_sitemap_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps.xml',
            '/sitemap/sitemap.xml',
            '/sitemaps/sitemap.xml'
        ]
        
        for path in common_sitemap_paths:
            sitemap_url = urljoin(self.base_url, path)
            if sitemap_url not in sitemaps:
                try:
                    response = self.session.head(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        sitemaps.append(sitemap_url)
                        print(f"📍 Found sitemap at: {path}")
                except:
                    continue
        
        return sitemaps
    
    def parse_sitemap(self, sitemap_url: str) -> List[Dict]:
        """Parse a sitemap XML and return URL entries."""
        urls = []
        
        try:
            print(f"🗺️  Parsing sitemap: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=15)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle namespace
            namespaces = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Check if this is a sitemap index
            if root.tag.endswith('sitemapindex'):
                print(f"📂 Found sitemap index with sub-sitemaps")
                sitemap_elements = root.findall('.//sm:sitemap', namespaces)
                if not sitemap_elements:
                    # Try without namespace
                    sitemap_elements = root.findall('.//sitemap')
                    
                for sitemap in sitemap_elements:
                    loc_elem = sitemap.find('sm:loc', namespaces) or sitemap.find('loc')
                    if loc_elem is not None:
                        sub_urls = self.parse_sitemap(loc_elem.text.strip())
                        urls.extend(sub_urls)
                        
            else:
                # This is a regular sitemap
                url_elements = root.findall('.//sm:url', namespaces)
                if not url_elements:
                    # Try without namespace
                    url_elements = root.findall('.//url')
                
                print(f"🔗 Found {len(url_elements)} URLs in sitemap")
                
                for url_elem in url_elements:
                    loc_elem = url_elem.find('sm:loc', namespaces) or url_elem.find('loc')
                    if loc_elem is None:
                        continue
                        
                    url_data = {'url': loc_elem.text.strip()}
                    
                    # Extract optional metadata
                    priority_elem = url_elem.find('sm:priority', namespaces) or url_elem.find('priority')
                    if priority_elem is not None:
                        try:
                            url_data['priority'] = float(priority_elem.text.strip())
                        except:
                            pass
                    
                    lastmod_elem = url_elem.find('sm:lastmod', namespaces) or url_elem.find('lastmod')
                    if lastmod_elem is not None:
                        try:
                            url_data['lastmod'] = datetime.datetime.fromisoformat(
                                lastmod_elem.text.strip().replace('Z', '+00:00')
                            )
                        except:
                            pass
                    
                    urls.append(url_data)
                    
        except Exception as e:
            print(f"❌ Error parsing sitemap {sitemap_url}: {e}")
        
        return urls
    
    def get_all_urls(self) -> List[Dict]:
        """Get all URLs from discovered sitemaps."""
        all_urls = []
        sitemaps = self.discover_sitemaps()
        
        if not sitemaps:
            print(f"⚠️  No sitemaps found for {self.base_url}")
            return []
        
        for sitemap_url in sitemaps:
            urls = self.parse_sitemap(sitemap_url)
            all_urls.extend(urls)
            time.sleep(0.5)  # Brief pause between sitemap requests
        
        # Remove duplicates
        seen_urls = set()
        unique_urls = []
        for url_data in all_urls:
            url = url_data['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url_data)
        
        print(f"📊 Total unique URLs discovered: {len(unique_urls)}")
        return unique_urls

class AlphabeticalSitemapScraper:
    """Main scraper class for alphabetical sitemap-based scraping."""
    
    def __init__(self, delay_between_requests: float = 1.0, quality_threshold: float = 3.0):
        self.delay = delay_between_requests
        self.quality_threshold = quality_threshold
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-AlphabeticalScraper/1.0 (Educational Purpose)'
        })
        self.scraped_pages: List[ScrapedPage] = []
        self.corpus_builder = NeocorpusBuilder()
        
        # Quality scoring keywords
        self.quality_keywords = {
            'high': ['article', 'guide', 'tutorial', 'documentation', 'reference', 'manual'],
            'medium': ['news', 'blog', 'post', 'update', 'review', 'analysis'],
            'low': ['home', 'contact', 'about', 'privacy', 'terms', 'sitemap']
        }
    
    def calculate_quality_score(self, url: str, title: str, content: str, 
                              word_count: int, sitemap_priority: Optional[float] = None) -> float:
        """Calculate content quality score (0-10)."""
        score = 0.0
        
        # Base score from word count
        if word_count >= 1000:
            score += 3.0
        elif word_count >= 500:
            score += 2.0
        elif word_count >= 200:
            score += 1.0
        
        # URL structure scoring
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in self.quality_keywords['high']):
            score += 2.0
        elif any(keyword in url_lower for keyword in self.quality_keywords['medium']):
            score += 1.0
        elif any(keyword in url_lower for keyword in self.quality_keywords['low']):
            score -= 1.0
        
        # Title scoring
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in self.quality_keywords['high']):
            score += 1.5
        elif any(keyword in title_lower for keyword in self.quality_keywords['medium']):
            score += 1.0
        
        # Content depth indicators
        if 'table of contents' in content.lower() or 'toc' in content.lower():
            score += 1.0
        if content.count('\n') > 50:  # Many paragraphs
            score += 0.5
        if len(re.findall(r'https?://[^\s]+', content)) > 5:  # Many references
            score += 0.5
        
        # Sitemap priority bonus
        if sitemap_priority and sitemap_priority > 0.5:
            score += sitemap_priority * 2.0
        
        return min(10.0, max(0.0, score))
    
    def extract_topics(self, title: str, content: str, url: str) -> List[str]:
        """Extract key topics from the content."""
        topics = set()
        
        # Extract from title
        title_words = re.findall(r'\b[A-Za-z]{3,}\b', title.lower())
        topics.update(title_words[:5])
        
        # Extract from URL path
        url_path = urlparse(url).path
        path_words = re.findall(r'\b[A-Za-z]{3,}\b', url_path.lower())
        topics.update(path_words[:3])
        
        # Extract from headings (if HTML structure is available)
        heading_pattern = r'<h[1-6][^>]*>(.*?)</h[1-6]>'
        headings = re.findall(heading_pattern, content, re.IGNORECASE)
        for heading in headings[:10]:
            clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
            heading_words = re.findall(r'\b[A-Za-z]{3,}\b', clean_heading.lower())
            topics.update(heading_words[:2])
        
        # Remove common words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'www', 'com'
        }
        
        filtered_topics = [topic for topic in topics if topic not in stop_words and len(topic) > 2]
        return list(filtered_topics)[:15]  # Limit to top 15 topics
    
    def scrape_page(self, url_data: Dict) -> Optional[ScrapedPage]:
        """Scrape a single page."""
        url = url_data['url']
        
        try:
            print(f"🔍 Scraping: {url}")
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {url}")
                return None
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Untitled"
            
            # Extract main content
            content = soup.get_text(separator='\n', strip=True)
            word_count = len(content.split())
            
            if word_count < 50:  # Skip very short pages
                print(f"⚠️  Skipping short content: {word_count} words")
                return None
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(
                url, title, content, word_count, url_data.get('priority')
            )
            
            if quality_score < self.quality_threshold:
                print(f"⚠️  Low quality score ({quality_score:.1f}): {url}")
                return None
            
            # Extract topics
            topics = self.extract_topics(title, content, url)
            
            # Create scraped page object
            page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                topics=topics,
                word_count=word_count,
                quality_score=quality_score,
                scraped_at=datetime.datetime.now(),
                sitemap_priority=url_data.get('priority'),
                sitemap_lastmod=url_data.get('lastmod')
            )
            
            print(f"✅ Quality: {quality_score:.1f}, Words: {word_count}, Topics: {len(topics)}")
            return page
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def scrape_website_alphabetically(self, base_url: str, max_pages: int = 100) -> Dict:
        """Scrape a website alphabetically using sitemap discovery."""
        print(f"🚀 Starting alphabetical sitemap scraping of: {base_url}")
        print(f"📋 Max pages: {max_pages}, Quality threshold: {self.quality_threshold}")
        
        start_time = time.time()
        
        # Discover and parse sitemaps
        sitemap_parser = SitemapParser(base_url)
        all_urls = sitemap_parser.get_all_urls()
        
        if not all_urls:
            return {
                'error': 'No sitemap URLs found',
                'base_url': base_url,
                'total_pages_scraped': 0
            }
        
        # Sort URLs alphabetically
        print(f"🔤 Sorting {len(all_urls)} URLs alphabetically...")
        all_urls.sort(key=lambda x: x['url'].lower())
        
        # Limit to max_pages
        urls_to_scrape = all_urls[:max_pages]
        print(f"📄 Will scrape {len(urls_to_scrape)} pages (limited by max_pages)")
        
        # Scrape pages
        scraped_count = 0
        high_quality_count = 0
        
        for i, url_data in enumerate(urls_to_scrape, 1):
            print(f"\n[{i}/{len(urls_to_scrape)}] ", end="")
            
            page = self.scrape_page(url_data)
            if page:
                self.scraped_pages.append(page)
                scraped_count += 1
                
                if page.quality_score >= 7.0:
                    high_quality_count += 1
                
                # Add to corpus
                self._add_to_corpus(page)
        
        elapsed_time = time.time() - start_time
        
        # Generate results
        results = {
            'base_url': base_url,
            'scraping_method': 'alphabetical_sitemap',
            'total_urls_discovered': len(all_urls),
            'total_pages_scraped': scraped_count,
            'high_quality_pages': high_quality_count,
            'elapsed_time_seconds': elapsed_time,
            'average_quality_score': sum(p.quality_score for p in self.scraped_pages) / max(1, scraped_count),
            'total_words_scraped': sum(p.word_count for p in self.scraped_pages),
            'unique_topics_found': len(set(topic for page in self.scraped_pages for topic in page.topics)),
            'timestamp': datetime.datetime.now().isoformat(),
            'pages': [self._page_to_dict(page) for page in self.scraped_pages]
        }
        
        # Save results
        self._save_results(results)
        
        print(f"\n✅ Alphabetical sitemap scraping complete!")
        print(f"   📄 Pages scraped: {scraped_count}/{len(urls_to_scrape)}")
        print(f"   🏆 High quality: {high_quality_count}")
        print(f"   📊 Average quality: {results['average_quality_score']:.2f}/10.0")
        print(f"   📝 Total words: {results['total_words_scraped']:,}")
        print(f"   🔗 Unique topics: {results['unique_topics_found']}")
        print(f"   ⏱️  Time taken: {elapsed_time:.1f}s")
        
        return results
    
    def _page_to_dict(self, page: ScrapedPage) -> Dict:
        """Convert ScrapedPage to dictionary for JSON serialization."""
        return {
            'url': page.url,
            'title': page.title,
            'topics': page.topics,
            'word_count': page.word_count,
            'quality_score': page.quality_score,
            'scraped_at': page.scraped_at.isoformat(),
            'sitemap_priority': page.sitemap_priority,
            'sitemap_lastmod': page.sitemap_lastmod.isoformat() if page.sitemap_lastmod else None
        }
    
    def _add_to_corpus(self, page: ScrapedPage) -> None:
        """Add scraped page to Marina's corpus."""
        try:
            corpus_entry = {
                "id": f"sitemap_alpha_{hash(page.url) % 100000}",
                "source": {
                    "source_type": "alphabetical_sitemap_scrape",
                    "url": page.url,
                    "keywords": page.topics[:5],
                    "priority": "high" if page.quality_score >= 7.0 else "medium",
                    "content_type": "web_content",
                    "estimated_quality": min(1.0, page.quality_score / 10.0),
                    "sitemap_priority": page.sitemap_priority
                },
                "content": {
                    "title": page.title,
                    "body": page.content,
                    "topics": page.topics,
                    "metadata": {
                        "scraped_at": page.scraped_at.isoformat(),
                        "word_count": page.word_count,
                        "quality_score": page.quality_score,
                        "sitemap_lastmod": page.sitemap_lastmod.isoformat() if page.sitemap_lastmod else None
                    }
                },
                "timestamp": datetime.datetime.now().isoformat(),
                "quality_score": min(1.0, page.quality_score / 10.0)
            }
            
            # Save to neocorpus directory
            corpus_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "feedback", "neocorpus"
            )
            os.makedirs(corpus_dir, exist_ok=True)
            
            entry_file = os.path.join(corpus_dir, f"entry_{corpus_entry['id']}.json")
            
            with open(entry_file, 'w', encoding='utf-8') as f:
                json.dump(corpus_entry, f, indent=2, default=str)
                
        except Exception as e:
            print(f"⚠️  Failed to add page to corpus: {e}")
    
    def _save_results(self, results: Dict) -> None:
        """Save scraping results to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "scraping_results"
        )
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"sitemap_alphabetical_scrape_{timestamp}.json")
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

def main():
    """Main function for testing the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Marina Alphabetical Sitemap Scraper')
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to scrape')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')
    parser.add_argument('--quality-threshold', type=float, default=3.0, help='Quality threshold')
    
    args = parser.parse_args()
    
    scraper = AlphabeticalSitemapScraper(
        delay_between_requests=args.delay,
        quality_threshold=args.quality_threshold
    )
    
    results = scraper.scrape_website_alphabetically(args.url, max_pages=args.max_pages)
    
    if 'error' not in results:
        print(f"\n📋 Final Summary:")
        print(f"   Base URL: {results['base_url']}")
        print(f"   URLs discovered: {results['total_urls_discovered']}")
        print(f"   Pages scraped: {results['total_pages_scraped']}")
        print(f"   High quality pages: {results['high_quality_pages']}")
        print(f"   Average quality: {results['average_quality_score']:.2f}/10.0")
        print(f"   Unique topics: {results['unique_topics_found']}")

if __name__ == "__main__":
    main()
