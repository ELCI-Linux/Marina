#!/usr/bin/env python3
"""
ArchWiki Flatpak/Flathub Knowledge Scraper
Uses rabbithole reasoning to deeply scrape ArchWiki for comprehensive Flatpak knowledge.

This module implements intelligent crawling of ArchWiki to build Marina's knowledge
base about Flatpaks, Flathub, and related technologies.
"""

import os
import sys
import requests
import json
import re
import time
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import datetime
from dataclasses import dataclass

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning.llm_builder.crawler.page_deconstructor import PageDeconstructor
from feedback.neocorpus_builder import NeocorpusBuilder

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph."""
    url: str
    title: str
    content: str
    topics: List[str]
    related_links: List[str]
    depth: int
    relevance_score: float
    scraped_at: datetime.datetime

class RabbitholeReasoner:
    """
    Implements rabbithole reasoning for deep knowledge extraction.
    Follows related links and topics recursively to build comprehensive understanding.
    """
    
    def __init__(self, max_depth: int = 3, delay_between_requests: float = 1.0):
        self.max_depth = max_depth
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-KnowledgeScraper/1.0 (Educational Purpose)'
        })
        self.visited_urls: Set[str] = set()
        self.knowledge_graph: Dict[str, KnowledgeNode] = {}
        
        # Primary seed topics for Flatpak knowledge
        self.seed_topics = [
            'flatpak', 'flathub', 'sandboxing', 'application packaging',
            'containerized applications', 'runtime', 'software distribution',
            'package management', 'application isolation', 'portals'
        ]
        
        # Relevance keywords for filtering content
        self.relevance_keywords = {
            'high': ['flatpak', 'flathub', 'sandbox', 'runtime', 'portal', 'permissions'],
            'medium': ['package', 'application', 'install', 'distribution', 'container'],
            'low': ['software', 'linux', 'system', 'user', 'security']
        }

    def calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate relevance score based on keyword presence and frequency."""
        title_lower = title.lower()
        content_lower = content.lower()
        
        score = 0.0
        
        # Title relevance (weighted higher)
        for keyword in self.relevance_keywords['high']:
            if keyword in title_lower:
                score += 3.0
        
        for keyword in self.relevance_keywords['medium']:
            if keyword in title_lower:
                score += 2.0
                
        for keyword in self.relevance_keywords['low']:
            if keyword in title_lower:
                score += 1.0
        
        # Content relevance
        for keyword in self.relevance_keywords['high']:
            count = content_lower.count(keyword)
            score += count * 0.5
            
        for keyword in self.relevance_keywords['medium']:
            count = content_lower.count(keyword)
            score += count * 0.3
            
        for keyword in self.relevance_keywords['low']:
            count = content_lower.count(keyword)
            score += count * 0.1
        
        # Normalize by content length (prevent bias toward long pages)
        if len(content) > 1000:
            score = score / (len(content) / 1000)
        
        return min(10.0, score)  # Cap at 10.0

    def extract_related_topics(self, content: str, soup: BeautifulSoup) -> List[str]:
        """Extract related topics and concepts from the page content."""
        topics = set()
        
        # Extract from headers
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            header_text = header.get_text().strip()
            if len(header_text) < 100:  # Avoid very long headers
                topics.add(header_text.lower())
        
        # Extract from category tags
        categories = soup.find_all('div', {'class': 'mw-category-group'})
        for category in categories:
            category_links = category.find_all('a')
            for link in category_links:
                topics.add(link.get_text().strip().lower())
        
        # Extract technical terms using regex patterns
        technical_patterns = [
            r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)*\b',  # CamelCase terms
            r'\b\w+\.(?:desktop|flatpakref|flatpak)\b',  # File extensions
            r'\bcom\.\w+\.\w+\b',  # Package identifiers
            r'\borg\.\w+\.\w+\b',  # Package identifiers
            r'\bflatpak\s+\w+\b',  # Flatpak commands
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:10]:  # Limit to prevent overwhelming
                if len(match) > 3:
                    topics.add(match.lower())
        
        # Filter out common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that'}
        filtered_topics = [topic for topic in topics if topic not in stop_words and len(topic) > 2]
        
        return list(filtered_topics)[:20]  # Limit to top 20

    def extract_related_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract related ArchWiki links from the page."""
        related_links = set()
        
        # Get all internal wiki links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Filter for ArchWiki internal links
            if href.startswith('/title/') or href.startswith('/index.php'):
                full_url = urljoin(base_url, href)
                
                # Check if link text contains relevant keywords
                link_text = link.get_text().lower()
                if any(keyword in link_text for keyword in self.seed_topics):
                    related_links.add(full_url)
                elif any(keyword in href.lower() for keyword in self.seed_topics):
                    related_links.add(full_url)
        
        # Also extract from "See also" sections
        see_also_sections = soup.find_all(['div', 'section'], 
                                        string=re.compile(r'see also|related|references', re.I))
        
        for section in see_also_sections:
            parent = section.find_parent()
            if parent:
                section_links = parent.find_all('a', href=True)
                for link in section_links:
                    href = link.get('href', '')
                    if href.startswith('/title/') or href.startswith('/index.php'):
                        related_links.add(urljoin(base_url, href))
        
        return list(related_links)[:10]  # Limit to prevent excessive crawling

    def scrape_page(self, url: str, depth: int = 0) -> Optional[KnowledgeNode]:
        """Scrape a single ArchWiki page and extract knowledge."""
        if url in self.visited_urls or depth > self.max_depth:
            return None
            
        try:
            print(f"{'  ' * depth}🔍 Scraping: {url} (depth: {depth})")
            
            # Rate limiting
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"{'  ' * depth}❌ Failed to fetch {url}: HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', {'class': 'firstHeading'}) or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # Extract main content
            content_div = (soup.find('div', {'id': 'mw-content-text'}) or 
                          soup.find('div', {'class': 'mw-parser-output'}) or
                          soup.find('main'))
            
            if not content_div:
                print(f"{'  ' * depth}⚠️  No content found for {url}")
                return None
            
            # Remove navigation elements, edit links, etc.
            for unwanted in content_div.find_all(['div'], {'class': ['mw-editsection', 'navbox', 'navigation-not-searchable']}):
                unwanted.decompose()
            
            content = content_div.get_text(separator='\n', strip=True)
            
            if len(content) < 100:  # Skip very short pages
                print(f"{'  ' * depth}⚠️  Content too short for {url}")
                return None
            
            # Calculate relevance
            relevance_score = self.calculate_relevance_score(title, content)
            
            if relevance_score < 1.0:  # Skip irrelevant pages
                print(f"{'  ' * depth}⚠️  Low relevance score ({relevance_score:.2f}) for {url}")
                return None
            
            # Extract topics and related links
            topics = self.extract_related_topics(content, soup)
            related_links = self.extract_related_links(soup, url)
            
            # Create knowledge node
            node = KnowledgeNode(
                url=url,
                title=title,
                content=content,
                topics=topics,
                related_links=related_links,
                depth=depth,
                relevance_score=relevance_score,
                scraped_at=datetime.datetime.now()
            )
            
            self.visited_urls.add(url)
            self.knowledge_graph[url] = node
            
            print(f"{'  ' * depth}✅ Scraped: {title} (score: {relevance_score:.2f}, topics: {len(topics)})")
            
            return node
            
        except Exception as e:
            print(f"{'  ' * depth}❌ Error scraping {url}: {e}")
            return None

    def follow_rabbithole(self, node: KnowledgeNode) -> List[KnowledgeNode]:
        """Recursively follow related links (the rabbithole reasoning part)."""
        discovered_nodes = []
        
        if node.depth >= self.max_depth:
            return discovered_nodes
        
        # Sort related links by potential relevance
        relevant_links = []
        for link in node.related_links:
            link_score = 0
            link_lower = link.lower()
            
            # Boost score for links containing seed topics
            for topic in self.seed_topics:
                if topic in link_lower:
                    link_score += 2
            
            relevant_links.append((link_score, link))
        
        # Sort by score and take top links
        relevant_links.sort(key=lambda x: x[0], reverse=True)
        top_links = [link for score, link in relevant_links[:5]]  # Follow top 5 links
        
        for link in top_links:
            if link not in self.visited_urls:
                child_node = self.scrape_page(link, node.depth + 1)
                if child_node:
                    discovered_nodes.append(child_node)
                    # Recursive rabbithole dive
                    grandchildren = self.follow_rabbithole(child_node)
                    discovered_nodes.extend(grandchildren)
        
        return discovered_nodes

class ArchWikiFlatpakScraper:
    """Main scraper class that orchestrates the knowledge extraction process."""
    
    def __init__(self):
        self.reasoner = RabbitholeReasoner(max_depth=3, delay_between_requests=1.5)
        self.corpus_builder = NeocorpusBuilder()
        
        # ArchWiki entry points for Flatpak-related content
        self.entry_points = [
            "https://wiki.archlinux.org/title/Flatpak",
            "https://wiki.archlinux.org/title/Bubblewrap", 
            "https://wiki.archlinux.org/title/Sandboxing",
            "https://wiki.archlinux.org/title/Application_sandboxing",
            "https://wiki.archlinux.org/title/Package_management"
        ]
        
    def scrape_comprehensive_knowledge(self) -> Dict[str, any]:
        """
        Perform comprehensive scraping of ArchWiki for Flatpak knowledge.
        Uses rabbithole reasoning to discover related content.
        """
        print("🚀 Starting comprehensive ArchWiki Flatpak knowledge scraping...")
        print(f"📍 Entry points: {len(self.entry_points)}")
        
        scraping_results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "entry_points": self.entry_points,
            "total_pages_scraped": 0,
            "knowledge_nodes": [],
            "corpus_entries": [],
            "summary": {}
        }
        
        all_nodes = []
        
        # Start from each entry point
        for entry_url in self.entry_points:
            print(f"\n🎯 Starting from entry point: {entry_url}")
            
            # Scrape the entry page
            root_node = self.reasoner.scrape_page(entry_url, depth=0)
            if root_node:
                all_nodes.append(root_node)
                
                # Follow the rabbithole from this entry point
                child_nodes = self.reasoner.follow_rabbithole(root_node)
                all_nodes.extend(child_nodes)
                
                print(f"   📊 Discovered {len(child_nodes)} related pages from this entry point")
        
        # Process and filter knowledge nodes
        scraping_results["total_pages_scraped"] = len(all_nodes)
        
        # Convert to corpus entries
        for node in all_nodes:
            corpus_entry = self._convert_node_to_corpus_entry(node)
            scraping_results["corpus_entries"].append(corpus_entry)
            
            # Add to Marina's corpus
            self._add_to_marina_corpus(corpus_entry)
        
        # Generate summary statistics
        scraping_results["summary"] = self._generate_summary(all_nodes)
        
        # Save results
        self._save_scraping_results(scraping_results)
        
        print(f"\n✅ Scraping complete!")
        print(f"   📄 Total pages scraped: {scraping_results['total_pages_scraped']}")
        print(f"   🏆 Average relevance score: {scraping_results['summary']['average_relevance']:.2f}")
        print(f"   🔗 Total unique topics discovered: {scraping_results['summary']['unique_topics']}")
        
        return scraping_results
    
    def _convert_node_to_corpus_entry(self, node: KnowledgeNode) -> Dict[str, any]:
        """Convert a knowledge node to a corpus entry format."""
        return {
            "id": f"archwiki_flatpak_{hash(node.url) % 100000}",
            "source": {
                "source_type": "archwiki_scrape",
                "url": node.url,
                "keywords": node.topics[:5],
                "priority": "high" if node.relevance_score > 5.0 else "medium",
                "content_type": "documentation",
                "estimated_quality": min(1.0, node.relevance_score / 10.0)
            },
            "content": {
                "title": node.title,
                "body": node.content,
                "topics": node.topics,
                "related_links": node.related_links,
                "metadata": {
                    "scraped_at": node.scraped_at.isoformat(),
                    "depth": node.depth,
                    "relevance_score": node.relevance_score
                }
            },
            "timestamp": datetime.datetime.now().isoformat(),
            "quality_score": min(1.0, node.relevance_score / 10.0)
        }
    
    def _add_to_marina_corpus(self, corpus_entry: Dict[str, any]) -> None:
        """Add the corpus entry to Marina's knowledge base."""
        try:
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
            print(f"⚠️  Failed to add corpus entry {corpus_entry['id']} to Marina: {e}")
    
    def _generate_summary(self, nodes: List[KnowledgeNode]) -> Dict[str, any]:
        """Generate summary statistics from scraped nodes."""
        if not nodes:
            return {}
        
        total_relevance = sum(node.relevance_score for node in nodes)
        average_relevance = total_relevance / len(nodes)
        
        all_topics = []
        for node in nodes:
            all_topics.extend(node.topics)
        
        unique_topics = len(set(all_topics))
        
        # Group by depth
        depth_distribution = {}
        for node in nodes:
            depth = node.depth
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        return {
            "total_nodes": len(nodes),
            "average_relevance": average_relevance,
            "max_relevance": max(node.relevance_score for node in nodes),
            "unique_topics": unique_topics,
            "total_topics": len(all_topics),
            "depth_distribution": depth_distribution,
            "high_relevance_pages": len([n for n in nodes if n.relevance_score > 5.0])
        }
    
    def _save_scraping_results(self, results: Dict[str, any]) -> None:
        """Save scraping results to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "scraping_results"
        )
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"archwiki_flatpak_scrape_{timestamp}.json")
        
        # Remove large content from summary file (keep metadata only)
        summary_results = dict(results)
        summary_results["corpus_entries"] = [
            {
                "id": entry["id"],
                "source": entry["source"],
                "metadata": entry["content"]["metadata"],
                "quality_score": entry["quality_score"]
            }
            for entry in results["corpus_entries"]
        ]
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(summary_results, f, indent=2, default=str)
            print(f"💾 Scraping results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Failed to save scraping results: {e}")

def main():
    """Main function to run the ArchWiki Flatpak scraper."""
    scraper = ArchWikiFlatpakScraper()
    results = scraper.scrape_comprehensive_knowledge()
    
    print(f"\n📋 Scraping Summary:")
    print(f"   Pages processed: {results['total_pages_scraped']}")
    if results['total_pages_scraped'] > 0:
        print(f"   Average relevance: {results['summary']['average_relevance']:.2f}/10.0")
        print(f"   Unique topics: {results['summary']['unique_topics']}")
        print(f"   High relevance pages: {results['summary']['high_relevance_pages']}")
    
    return results

if __name__ == "__main__":
    results = main()
