# !/usr/bin/env python3
"""
Generalized Natural Language Scraper using Rabbithole Reasoning
This module implements a flexible web scraper that starts from a user-defined root URL
and uses Marina's rabbithole reasoning mechanism for deep content discovery.
"""

import os
import sys
import requests
import json
import time
import re
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
import datetime
from collections import Counter

# Ensure the project root is in the path for Marina modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Marina's hybrid prompting engine and models
try:
    from learning.hybrid_prompting_engine import HybridPromptingEngine
    from learning.models.analysis_models import Keyword
    HYBRID_PROMPTING_AVAILABLE = True
except ImportError:
    HYBRID_PROMPTING_AVAILABLE = False
    
try:
    from learning.keyword_generator import KeywordGenerator
    KEYWORD_GENERATOR_AVAILABLE = True
except ImportError:
    KEYWORD_GENERATOR_AVAILABLE = False
    
try:
    from llm.gemini_dispatcher import GeminiDispatcher
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    
try:
    from llm.tinyllama_dispatcher import TinyLlamaDispatcher
    TINYLLAMA_AVAILABLE = True
except ImportError:
    TINYLLAMA_AVAILABLE = False

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph"""
    url: str
    title: str
    content: str
    topics: List[str]
    related_links: List[str]
    depth: int
    relevance_score: float
    scraped_at: datetime.datetime

class GeneralScraper:
    """
    General scraper using rabbithole reasoning to extract knowledge starting from
    a user-defined root URL.
    """
    
    def __init__(self, root_url: str, max_depth: int = 3, delay_between_requests: float = 1.0, time_limit: int = 300):
        self.root_url = root_url
        self.max_depth = max_depth
        self.delay = delay_between_requests
        self.time_limit = time_limit
        self.start_time = time.time()
        self.rejected_sources = 0
        self.root_url = root_url
        self.max_depth = max_depth
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-GeneralScraper/1.0 (Educational Purpose)'
        })
        self.visited_urls: Set[str] = set()
        self.knowledge_graph: Dict[str, KnowledgeNode] = {}

        # Disabled complex initialization for simplification
        self.keyword_generator = None
        self.hybrid_engine = None

        # Cache for generated keywords to avoid redundant API calls
        self.keyword_cache: Dict[str, List[Tuple[str, float]]] = {}
        
    def _initialize_keyword_generator(self) -> Optional[KeywordGenerator]:
        """Initialize the keyword generator with fallback preference (faster-whisper -> tinyllama)"""
        if not KEYWORD_GENERATOR_AVAILABLE:
            print("⚠️  LLM-based keyword generator not available. Using basic keywords.")
            return None
            
        # Build config following user preference: faster-whisper (interpreted as TinyLlama) first, then Gemini fallback
        config = {
            'llm_settings': {
                'preferred_model': 'tinyllama' if TINYLLAMA_AVAILABLE else ('gemini' if GEMINI_AVAILABLE else None)
            },
            'research_settings': {
                'keywords_per_iteration': 30  # More keywords for better coverage
            }
        }
        
        if config['llm_settings']['preferred_model'] is None:
            print("⚠️  No LLM models available for keyword generation. Using basic keywords.")
            return None
            
        try:
            generator = KeywordGenerator(config)
            print(f"✅ Keyword generator initialized with {config['llm_settings']['preferred_model']}")
            return generator
        except Exception as e:
            print(f"⚠️  Failed to initialize keyword generator: {e}")
            return None
    
    def _initialize_hybrid_prompting_engine(self) -> Optional['HybridPromptingEngine']:
        """Initialize the hybrid prompting engine if available"""
        if not HYBRID_PROMPTING_AVAILABLE:
            print("⚠️  Hybrid prompting engine not available. Using fallback keyword generation.")
            return None
            
        try:
            engine = HybridPromptingEngine(timeout_per_model=10.0, max_keywords_per_model=25)
            print("✅ Hybrid prompting engine initialized with TinyLlama + cloud LLM support")
            return engine
        except Exception as e:
            print(f"⚠️  Failed to initialize hybrid prompting engine: {e}")
            return None
    
    def _generate_enhanced_keywords(self, initial_keywords: List[str], root_url: str) -> List[Tuple[str, float]]:
        """Generate enhanced keywords using only Gemini to simplify the process and avoid errors."""
        from llm.llm_router import route_task
        from urllib.parse import urlparse

        # Create a topic context from URL and initial keywords
        parsed_url = urlparse(root_url)
        domain_context = parsed_url.netloc.replace('www.', '').replace('.com', '').replace('.co.uk', '')
        topic_context = f"{domain_context} {' '.join(initial_keywords)}"
        
        # Check cache first
        if topic_context in self.keyword_cache:
            print("U+1F504 Using cached keywords for similar topic")
            return self.keyword_cache[topic_context]

        print(f"U+1F9E0 Generating keywords for topic: '{topic_context}' using Gemini...")
        
        prompt = f"Generate 20-25 keywords and phrases related to the topic: '{topic_context}'. Return as a comma-separated list."
        
        # Directly call llm_router, forcing gemini
        model, llm_response = route_task(prompt, token_estimate=150, run=True, force_model='gemini')
        
        if not llm_response or llm_response.startswith('[ERROR]'):
            print(f"U+26A0U+FE0F Gemini failed to generate keywords: {llm_response}. Using initial keywords as fallback.")
            return [(kw, 1.0) for kw in initial_keywords]
            
        # Parse LLM response into keyword list with weights
        raw_words = llm_response.replace('*', '').replace('-', '').strip()
        keyword_terms = [term.strip() for term in raw_words.replace('\n', ',').split(',') if term.strip()]
        
        weighted_keywords = []
        for term in keyword_terms:
            if term and len(term.strip()) > 2:
                weighted_keywords.append((term, 1.0))  # Default weight of 1.0
                
        # Add original keywords with high weight for focus
        for original_kw in initial_keywords:
            weighted_keywords.append((original_kw, 2.0))
            
        # Cache the result
        self.keyword_cache[topic_context] = weighted_keywords
            
        print(f"U+2705 Generated {len(weighted_keywords)} keywords using Gemini.")
        return list(set(weighted_keywords))
        
    def calculate_relevance_score(self, title: str, content: str, keywords: List[str], weighted_keywords: Optional[List[Tuple[str, float]]] = None) -> float:
        """Calculate the relevance score based on keyword presence and frequency with optional weights"""
        title_lower = title.lower()
        content_lower = content.lower()

        score = 0.0
        
        # Use weighted keywords if available, otherwise fallback to basic keywords
        if weighted_keywords:
            keyword_list = weighted_keywords
        else:
            keyword_list = [(kw, 1.0) for kw in keywords]

        # Title relevance (weighted higher with LLM-generated weights)
        for keyword, weight in keyword_list:
            keyword_lower = keyword.lower()
            if keyword_lower in title_lower:
                score += 5.0 * weight  # Apply weight to title matches

        # Content relevance with weighted scoring
        for keyword, weight in keyword_list:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            if count > 0:
                # Logarithmic scoring with weight multiplier
                weighted_score = min(count * 0.8, 3.0) * weight
                score += weighted_score

        # Content quality indicators (unchanged)
        content_indicators = {
            'article': 2.0, 'news': 2.0, 'story': 1.5, 'report': 1.5, 
            'breaking': 2.5, 'update': 2.0, 'analysis': 2.0, 'latest': 1.5,
            'headline': 1.5, 'published': 1.0, 'journalist': 1.0
        }
        
        for indicator, weight in content_indicators.items():
            if indicator in content_lower:
                score += weight

        # Length bonus for substantial content
        if len(content) > 500:
            score += 1.0
        if len(content) > 2000:
            score += 1.0
            
        # Normalize by excessive length to prevent very long pages from dominating
        if len(content) > 5000:
            score = score * 0.8

        return min(10.0, score)  # Cap at 10.0

    def extract_related_topics(self, content: str, soup: BeautifulSoup) -> List[str]:
        """Extract related topics and concepts from the page content."""
        topics = set()
        
        # Extract from headers (h1, h2, h3, etc.)
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
            header_text = header.get_text().strip()
            if 5 <= len(header_text) <= 100:  # Reasonable header length
                topics.add(header_text.lower())
        
        # Extract from article titles and metadata
        for meta in soup.find_all('meta', {'name': ['description', 'keywords']}):
            meta_content = meta.get('content', '')
            if meta_content:
                # Split by common separators and add individual terms
                terms = re.split(r'[,;\|\n]', meta_content)
                for term in terms[:5]:  # Limit to prevent overwhelming
                    term = term.strip()
                    if 3 <= len(term) <= 50:
                        topics.add(term.lower())
        
        # Extract prominent words (potential topics)
        # Remove common stop words and extract meaningful terms
        words = re.findall(r'\b[A-Za-z]{3,}\b', content)
        word_freq = Counter(word.lower() for word in words)
        
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our',
            'had', 'what', 'said', 'each', 'which', 'she', 'how', 'other', 'than', 'now', 'very', 'they',
            'this', 'that', 'with', 'have', 'from', 'will', 'been', 'more', 'when', 'where', 'some',
            'time', 'has', 'may', 'use', 'its', 'most', 'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea'
        }
        
        # Get top frequent words that aren't stop words
        for word, freq in word_freq.most_common(15):
            if word not in stop_words and len(word) >= 4 and freq >= 2:
                topics.add(word)
        
        # Extract from article/news specific elements
        for elem in soup.find_all(['article', 'section'], class_=re.compile(r'story|article|news')):
            elem_text = elem.get_text()[:200]  # First 200 chars
            key_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', elem_text)
            for phrase in key_phrases[:5]:
                if 3 <= len(phrase) <= 50:
                    topics.add(phrase.lower())
        
        # Filter and limit topics
        filtered_topics = [topic for topic in topics if len(topic.split()) <= 4]  # Max 4 words
        return list(filtered_topics)[:25]  # Limit to top 25 topics

    def extract_related_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract related links from the page."""
        related_links = set()
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Skip empty links, fragments, or javascript
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
                
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Focus on same domain links to maintain coherence
            if parsed_url.netloc == base_domain:
                link_text = link.get_text().strip().lower()
                
                # Prioritize content-rich links
                content_indicators = ['article', 'news', 'story', 'report', 'analysis', 'feature']
                skip_indicators = ['login', 'register', 'subscribe', 'contact', 'about', 'privacy', 'terms']
                
                # Skip navigation and utility links
                if any(skip in href.lower() for skip in skip_indicators):
                    continue
                    
                # Prefer content links
                if any(indicator in href.lower() or indicator in link_text for indicator in content_indicators):
                    related_links.add(full_url)
                elif len(link_text) > 10 and not any(skip in link_text for skip in skip_indicators):
                    related_links.add(full_url)

        return list(related_links)[:15]  # Limit to prevent excessive crawling

    def scrape_page(self, url: str, keywords: List[str], depth: int = 0) -> Optional[KnowledgeNode]:
        if (time.time() - self.start_time) > self.time_limit:
            print(f"Time limit of {self.time_limit}s reached. Stopping scrape.")
            self.rejected_sources += 1
            return None

        if url in self.visited_urls or depth > self.max_depth:
            self.rejected_sources += 1
            return None

        try:
            print(f"{'  ' * depth}🔍 Scraping: {url} (depth: {depth})")
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"{'  ' * depth}U+274C Failed to fetch {url}: HTTP {response.status_code}")
                self.rejected_sources += 1
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"

            # Extract main content
            content_div = soup.find('body')
            if not content_div:
                print(f"{'  ' * depth}⚠️  No content found for {url}")
                return None

            content = content_div.get_text(separator='\n', strip=True)

            if len(content) < 100:  # Skip very short pages
                print(f"{'  ' * depth}⚠️  Content too short for {url}")
                return None

            relevance_score = self.calculate_relevance_score(title, content, keywords)

            if relevance_score < 1.0:  # Skip irrelevant pages
                print(f"{'  ' * depth}⚠️  Low relevance score ({relevance_score:.2f}) for {url}")
                return None

            topics = self.extract_related_topics(content, soup)
            related_links = self.extract_related_links(soup, url)

            node = KnowledgeNode(
                url=url,
                title=title,
                content=content[:3000],  # Limit content size
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

    def follow_rabbithole(self, node: KnowledgeNode, keywords: List[str]) -> List[KnowledgeNode]:
        """Recursively follow related links (the rabbithole reasoning part)."""
        discovered_nodes = []
        
        if node.depth >= self.max_depth:
            return discovered_nodes
        
        # Sort related links by potential relevance
        relevant_links = []
        for link in node.related_links:
            link_score = 0
            link_lower = link.lower()
            
            # Boost score for links containing keywords
            for keyword in keywords:
                if keyword.lower() in link_lower:
                    link_score += 2
            
            # Boost for content indicators
            content_indicators = ['news', 'article', 'story', 'report', 'breaking']
            for indicator in content_indicators:
                if indicator in link_lower:
                    link_score += 1
            
            relevant_links.append((link_score, link))
        
        # Sort by score and take top links
        relevant_links.sort(key=lambda x: x[0], reverse=True)
        top_links = [link for score, link in relevant_links[:5]]  # Follow top 5 links
        
        for link in top_links:
            if link not in self.visited_urls:
                child_node = self.scrape_page(link, keywords, node.depth + 1)
                if child_node:
                    discovered_nodes.append(child_node)
                    # Recursive rabbithole dive
                    grandchildren = self.follow_rabbithole(child_node, keywords)
                    discovered_nodes.extend(grandchildren)
        
        return discovered_nodes


class NewsArticleScraper:
    """Specialized news article scraper that integrates with Marina's corpus system."""
    
    def __init__(self, max_depth: int = 2, delay_between_requests: float = 1.5, time_limit: int = 300):
        self.max_depth = max_depth
        self.delay = delay_between_requests
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.delay = delay_between_requests
        
        # Try to import Marina's corpus builder
        try:
            sys.path.append('/home/adminx/Marina')
            from feedback.neocorpus_builder import NeocorpusBuilder
            self.corpus_builder = NeocorpusBuilder()
            self.corpus_integration = True
        except ImportError:
            print("⚠️  Marina corpus builder not available. Scraped data will not be added to corpus.")
            self.corpus_integration = False
            self.corpus_builder = None
        
    def scrape_news_site(self, root_url: str, keywords: List[str] = None) -> Dict[str, any]:
        """
        Scrape a news site comprehensively using rabbithole reasoning with LLM-enhanced keywords.
        
        Args:
            root_url: The starting URL for scraping
            keywords: Keywords to focus the scraping on (optional)
        
        Returns:
            Dictionary containing scraping results and statistics
        """
        if keywords is None:
            # Default keywords for general news scraping
            keywords = ['news', 'article', 'breaking', 'latest', 'update']
        
        print(f"🚀 Starting enhanced news scraping from: {root_url}")
        print(f"📝 Initial focus keywords: {keywords}")
        
        scraper = GeneralScraper(root_url, max_depth=self.max_depth, delay_between_requests=self.delay, time_limit=self.time_limit)
        
        # Generate enhanced keywords with weights
        enhanced_keywords = scraper._generate_enhanced_keywords(keywords, root_url)
        print(f"🧠 Enhanced keyword pool: {len(enhanced_keywords)} terms with relevance weights")
        
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "root_url": root_url,
            "keywords": keywords,
            "enhanced_keywords": [(term, weight) for term, weight in enhanced_keywords[:10]],  # Show top 10
            "total_pages_scraped": 0,
            "knowledge_nodes": [],
            "corpus_entries": [],
            "summary": {}
        }
        
        all_nodes = []
        
        # Start with the root page using enhanced keyword scoring
        print(f"\n🎯 Starting from root URL: {root_url}")
        root_node = self._scrape_page_enhanced(scraper, root_url, keywords, enhanced_keywords, depth=0)
        
        if root_node:
            all_nodes.append(root_node)
            
            # Follow the rabbithole from the root using enhanced keywords
            child_nodes = self._follow_rabbithole_enhanced(scraper, root_node, keywords, enhanced_keywords)
            all_nodes.extend(child_nodes)
            
            print(f"   📊 Discovered {len(child_nodes)} related pages from root")
        else:
            print(f"   ❌ Failed to scrape root URL")
            return results
        
        # Process and filter knowledge nodes
        results["total_pages_scraped"] = len(all_nodes)
        results["knowledge_nodes"] = [self._node_to_dict(node) for node in all_nodes]
        
        # Convert to corpus entries if corpus integration is available
        if self.corpus_integration:
            for node in all_nodes:
                corpus_entry = self._convert_node_to_corpus_entry(node)
                results["corpus_entries"].append(corpus_entry)
                
                # Add to Marina's corpus
                self._add_to_marina_corpus(corpus_entry)
        
        # Generate summary statistics
        results["summary"] = self._generate_summary(all_nodes)
        results["rejected_sources"] = scraper.rejected_sources
        
        # Save results
        self._save_scraping_results(results, root_url)
        
        print(f"\n✅ News scraping complete!")
        print(f"   📄 Total pages scraped: {results['total_pages_scraped']}")
        if results["summary"]:
            print(f"   🏆 Average relevance score: {results['summary']['average_relevance']:.2f}")
            print(f"   🔗 Total unique topics discovered: {results['summary']['unique_topics']}")
        
        return results
    
    def _scrape_page_enhanced(self, scraper: GeneralScraper, url: str, keywords: List[str], enhanced_keywords: List[Tuple[str, float]], depth: int = 0) -> Optional[KnowledgeNode]:
        """Scrape a single page using enhanced keyword scoring"""
        node = scraper.scrape_page(url, keywords, depth)
        if node:
            # Recalculate relevance score using enhanced keywords
            enhanced_score = scraper.calculate_relevance_score(
                node.title, node.content, keywords, enhanced_keywords
            )
            node.relevance_score = enhanced_score
        return node
    
    def _follow_rabbithole_enhanced(self, scraper: GeneralScraper, node: KnowledgeNode, keywords: List[str], enhanced_keywords: List[Tuple[str, float]]) -> List[KnowledgeNode]:
        """Follow rabbithole using enhanced keyword scoring"""
        discovered_nodes = []
        
        if node.depth >= scraper.max_depth:
            return discovered_nodes
        
        # Use enhanced keyword weights for link relevance scoring
        relevant_links = []
        for link in node.related_links:
            link_score = 0
            link_lower = link.lower()
            
            # Enhanced scoring with keyword weights
            for keyword, weight in enhanced_keywords:
                if keyword.lower() in link_lower:
                    link_score += 2 * weight  # Apply weight to keyword matches
            
            # Content indicators (unchanged)
            content_indicators = ['news', 'article', 'story', 'report', 'breaking']
            for indicator in content_indicators:
                if indicator in link_lower:
                    link_score += 1
            
            relevant_links.append((link_score, link))
        
        # Sort by score and take top links
        relevant_links.sort(key=lambda x: x[0], reverse=True)
        top_links = [link for score, link in relevant_links[:5]]  # Follow top 5 links
        
        for link in top_links:
            if link not in scraper.visited_urls:
                child_node = self._scrape_page_enhanced(scraper, link, keywords, enhanced_keywords, node.depth + 1)
                if child_node:
                    discovered_nodes.append(child_node)
                    # Recursive rabbithole dive with enhanced scoring
                    grandchildren = self._follow_rabbithole_enhanced(scraper, child_node, keywords, enhanced_keywords)
                    discovered_nodes.extend(grandchildren)
        
        return discovered_nodes
    
    def _node_to_dict(self, node: KnowledgeNode) -> Dict[str, any]:
        """Convert a knowledge node to dictionary format."""
        return {
            "url": node.url,
            "title": node.title,
            "content_preview": node.content[:200] + "..." if len(node.content) > 200 else node.content,
            "topics": node.topics,
            "related_links_count": len(node.related_links),
            "depth": node.depth,
            "relevance_score": node.relevance_score,
            "scraped_at": node.scraped_at.isoformat()
        }
    
    def _convert_node_to_corpus_entry(self, node: KnowledgeNode) -> Dict[str, any]:
        """Convert a knowledge node to Marina corpus entry format."""
        return {
            "id": f"news_{hash(node.url) % 100000}",
            "source": {
                "source_type": "news_scrape",
                "url": node.url,
                "keywords": node.topics[:5],
                "priority": "high" if node.relevance_score > 6.0 else "medium",
                "content_type": "news_article",
                "estimated_quality": min(1.0, node.relevance_score / 10.0)
            },
            "content": {
                "title": node.title,
                "body": node.content,
                "topics": node.topics,
                "related_links": node.related_links[:5],  # Limit related links
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
            corpus_dir = "/home/adminx/Marina/feedback/neocorpus"
            os.makedirs(corpus_dir, exist_ok=True)
            
            entry_file = os.path.join(corpus_dir, f"entry_{corpus_entry['id']}.json")
            
            with open(entry_file, 'w', encoding='utf-8') as f:
                json.dump(corpus_entry, f, indent=2, default=str)
                
            print(f"   💾 Added to corpus: {corpus_entry['id']}")
                
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
            "high_relevance_pages": len([n for n in nodes if n.relevance_score > 6.0])
        }
    
    def _save_scraping_results(self, results: Dict[str, any], root_url: str) -> None:
        """Save scraping results to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(root_url).netloc.replace('.', '_')
        
        results_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "scraping_results"
        )
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(results_dir, f"news_scrape_{domain}_{timestamp}.json")
        
        # Create summary without full content to keep file size manageable
        summary_results = dict(results)
        if "knowledge_nodes" in summary_results:
            summary_results["knowledge_nodes"] = [
                {
                    "url": node["url"],
                    "title": node["title"],
                    "relevance_score": node["relevance_score"],
                    "topics_count": len(node["topics"]),
                    "depth": node["depth"]
                }
                for node in results["knowledge_nodes"]
            ]
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(summary_results, f, indent=2, default=str)
            print(f"💾 Scraping results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Failed to save scraping results: {e}")


def main():
    """Main function to demonstrate the news scraper."""
    scraper = NewsArticleScraper(max_depth=2, delay_between_requests=1.0)
    
    # Test URLs
    test_urls = [
        "https://bbc.co.uk/news",
        "https://bbc.co.uk/sport"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing scraper on: {url}")
        print(f"{'='*60}")
        
        # Custom keywords based on the URL
        if 'news' in url:
            keywords = ['news', 'breaking', 'latest', 'update', 'report']
        elif 'sport' in url:
            keywords = ['sport', 'football', 'cricket', 'tennis', 'match', 'game']
        else:
            keywords = ['news', 'article']
        
        results = scraper.scrape_news_site(url, keywords)
        
        print(f"\n📋 Summary for {url}:")
        if results['total_pages_scraped'] > 0 and results.get('summary'):
            summary = results['summary']
            print(f"   📄 Pages scraped: {summary['total_nodes']}")
            print(f"   🎯 Average relevance: {summary['average_relevance']:.2f}/10.0")
            print(f"   🔗 Unique topics: {summary['unique_topics']}")
            print(f"   📊 Depth distribution: {summary['depth_distribution']}")
        else:
            print("   ❌ No pages successfully scraped")


if __name__ == "__main__":
    main()
