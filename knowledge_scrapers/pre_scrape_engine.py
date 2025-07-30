#!/usr/bin/env python3
"""
Marina Pre-Scrape Engine

Comprehensive pre-scraping optimization and validation engine designed to:
- Analyze target websites and optimize scraping strategies
- Validate URLs and detect website characteristics
- Implement smart rate limiting and anti-detection measures
- Cache robots.txt and sitemap data
- Perform domain reputation and safety checks
- Optimize scraper selection based on target analysis
- Generate dynamic scraping configurations
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import requests
import hashlib
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin, parse_qs
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
import socket
from user_agents import parse as parse_user_agent
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class WebsiteCharacteristics:
    """Characteristics of a target website"""
    url: str
    domain: str
    cms_type: Optional[str] = None
    anti_bot_measures: List[str] = None
    javascript_heavy: bool = False
    api_endpoints: List[str] = None
    rate_limits: Dict[str, Any] = None
    robots_txt_url: Optional[str] = None
    sitemap_urls: List[str] = None
    security_headers: Dict[str, str] = None
    response_times: Dict[str, float] = None
    server_info: Dict[str, str] = None
    content_type: str = "unknown"
    estimated_pages: int = 0
    last_analyzed: str = None
    risk_score: float = 0.0
    recommended_delay: float = 1.5
    
    def __post_init__(self):
        if self.anti_bot_measures is None:
            self.anti_bot_measures = []
        if self.api_endpoints is None:
            self.api_endpoints = []
        if self.rate_limits is None:
            self.rate_limits = {}
        if self.sitemap_urls is None:
            self.sitemap_urls = []
        if self.security_headers is None:
            self.security_headers = {}
        if self.response_times is None:
            self.response_times = {}
        if self.server_info is None:
            self.server_info = {}
        if self.last_analyzed is None:
            self.last_analyzed = datetime.now().isoformat()

@dataclass
class ScrapingStrategy:
    """Optimized scraping strategy for a target"""
    target_url: str
    recommended_scraper: str
    scraper_config: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    anti_detection: Dict[str, Any]
    priority_urls: List[str]
    estimated_duration: float
    risk_assessment: Dict[str, Any]
    fallback_strategies: List[Dict[str, Any]]
    created_at: str
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class PreScrapeCache:
    """Caching system for pre-scrape analysis"""
    
    def __init__(self, cache_dir: str = "/tmp/marina_prescrape_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "prescrape_cache.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS website_analysis (
                    domain TEXT PRIMARY KEY,
                    url TEXT,
                    characteristics TEXT,
                    analyzed_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS robots_cache (
                    domain TEXT PRIMARY KEY,
                    robots_content TEXT,
                    cached_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sitemap_cache (
                    url TEXT PRIMARY KEY,
                    sitemap_content TEXT,
                    cached_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
    
    def get_website_analysis(self, domain: str) -> Optional[WebsiteCharacteristics]:
        """Get cached website analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT characteristics FROM website_analysis WHERE domain = ? AND expires_at > ?",
                (domain, datetime.now().isoformat())
            )
            result = cursor.fetchone()
            if result:
                try:
                    data = json.loads(result[0])
                    return WebsiteCharacteristics(**data)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached analysis: {e}")
        return None
    
    def save_website_analysis(self, characteristics: WebsiteCharacteristics, cache_hours: int = 24):
        """Save website analysis to cache"""
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO website_analysis 
                   (domain, url, characteristics, analyzed_at, expires_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    characteristics.domain,
                    characteristics.url,
                    json.dumps(asdict(characteristics)),
                    datetime.now().isoformat(),
                    expires_at.isoformat()
                )
            )
    
    def get_robots_txt(self, domain: str) -> Optional[str]:
        """Get cached robots.txt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT robots_content FROM robots_cache WHERE domain = ? AND expires_at > ?",
                (domain, datetime.now().isoformat())
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def save_robots_txt(self, domain: str, content: str, cache_hours: int = 168):  # 1 week
        """Save robots.txt to cache"""
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO robots_cache 
                   (domain, robots_content, cached_at, expires_at) 
                   VALUES (?, ?, ?, ?)""",
                (domain, content, datetime.now().isoformat(), expires_at.isoformat())
            )

class WebsiteAnalyzer:
    """Comprehensive website analysis for scraping optimization"""
    
    def __init__(self, cache: PreScrapeCache):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-PreScrapeAnalyzer/1.0 (Research Bot)'
        })
    
    def analyze_website(self, url: str, force_refresh: bool = False) -> WebsiteCharacteristics:
        """Comprehensive website analysis"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check cache first
        if not force_refresh:
            cached = self.cache.get_website_analysis(domain)
            if cached:
                logger.info(f"Using cached analysis for {domain}")
                return cached
        
        logger.info(f"Analyzing website: {url}")
        
        characteristics = WebsiteCharacteristics(url=url, domain=domain)
        
        try:
            # Parallel analysis tasks
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self._analyze_initial_response, url): 'initial',
                    executor.submit(self._detect_cms, url): 'cms',
                    executor.submit(self._check_robots_txt, domain): 'robots',
                    executor.submit(self._discover_sitemaps, url): 'sitemaps',
                    executor.submit(self._check_security_headers, url): 'security'
                }
                
                for future in as_completed(futures):
                    task_type = futures[future]
                    try:
                        result = future.result(timeout=30)
                        self._merge_analysis_result(characteristics, task_type, result)
                    except Exception as e:
                        logger.warning(f"Analysis task {task_type} failed: {e}")
            
            # Calculate derived metrics
            self._calculate_risk_score(characteristics)
            self._recommend_delay(characteristics)
            self._estimate_content_size(characteristics)
            
            # Cache results
            self.cache.save_website_analysis(characteristics)
            
        except Exception as e:
            logger.error(f"Website analysis failed: {e}")
            characteristics.risk_score = 5.0  # High risk for unknown sites
        
        return characteristics
    
    def _analyze_initial_response(self, url: str) -> Dict[str, Any]:
        """Analyze initial HTTP response"""
        result = {
            'response_times': {},
            'server_info': {},
            'anti_bot_measures': [],
            'javascript_heavy': False
        }
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response_time = time.time() - start_time
            
            result['response_times']['initial'] = response_time
            result['server_info']['status_code'] = response.status_code
            result['server_info']['server'] = response.headers.get('Server', 'Unknown')
            result['server_info']['content_length'] = len(response.content)
            
            # Check for anti-bot measures
            if response.status_code == 403:
                result['anti_bot_measures'].append('403_blocking')
            
            if 'cloudflare' in response.headers.get('Server', '').lower():
                result['anti_bot_measures'].append('cloudflare')
            
            if any(header in response.headers for header in ['cf-ray', 'cf-cache-status']):
                result['anti_bot_measures'].append('cloudflare_protection')
            
            # Check for JavaScript heavy content
            content = response.text.lower()
            js_indicators = ['<script', 'javascript:', 'document.', 'window.', 'react', 'angular', 'vue']
            js_count = sum(content.count(indicator) for indicator in js_indicators)
            result['javascript_heavy'] = js_count > 10
            
            # Check for rate limiting headers
            rate_limit_headers = ['x-ratelimit', 'x-rate-limit', 'retry-after']
            for header in response.headers:
                if any(rl_header in header.lower() for rl_header in rate_limit_headers):
                    result['anti_bot_measures'].append('rate_limiting_headers')
                    break
                    
        except requests.RequestException as e:
            logger.warning(f"Initial response analysis failed: {e}")
            result['response_times']['initial'] = 30.0  # Assume slow
        
        return result
    
    def _detect_cms(self, url: str) -> Dict[str, Any]:
        """Detect CMS and platform"""
        result = {'cms_type': None, 'api_endpoints': []}
        
        try:
            response = self.session.get(url, timeout=10)
            content = response.text.lower()
            headers = response.headers
            
            # WordPress detection
            if any(indicator in content for indicator in ['wp-content', 'wp-includes', 'wordpress']):
                result['cms_type'] = 'wordpress'
                result['api_endpoints'].append('/wp-json/wp/v2/')
            
            # Shopify detection
            elif 'shopify' in content or 'cdn.shopify.com' in content:
                result['cms_type'] = 'shopify'
                result['api_endpoints'].extend(['/products.json', '/collections.json'])
            
            # Drupal detection
            elif any(indicator in content for indicator in ['drupal', '/sites/default/', 'drupal.js']):
                result['cms_type'] = 'drupal'
            
            # React/SPA detection
            elif any(indicator in content for indicator in ['react', '__react', 'reactdom']):
                result['cms_type'] = 'react_spa'
            
            # Check for API endpoints in headers
            if 'application/json' in headers.get('content-type', ''):
                result['api_endpoints'].append(urlparse(url).path)
                
        except Exception as e:
            logger.warning(f"CMS detection failed: {e}")
        
        return result
    
    def _check_robots_txt(self, domain: str) -> Dict[str, Any]:
        """Check and parse robots.txt"""
        result = {'robots_txt_url': None, 'rate_limits': {}}
        
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            # Check cache first
            cached_robots = self.cache.get_robots_txt(domain)
            
            if cached_robots:
                robots_content = cached_robots
            else:
                response = self.session.get(robots_url, timeout=10)
                if response.status_code == 200:
                    robots_content = response.text
                    self.cache.save_robots_txt(domain, robots_content)
                else:
                    return result
            
            result['robots_txt_url'] = robots_url
            
            # Parse robots.txt for crawl delays
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            crawl_delay = rp.crawl_delay('*')
            if crawl_delay:
                result['rate_limits']['crawl_delay'] = float(crawl_delay)
            
            # Look for sitemap references
            sitemaps = []
            for line in robots_content.split('\n'):
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemaps.append(sitemap_url)
            
            if sitemaps:
                result['sitemap_urls'] = sitemaps
                
        except Exception as e:
            logger.warning(f"Robots.txt analysis failed: {e}")
        
        return result
    
    def _discover_sitemaps(self, url: str) -> Dict[str, Any]:
        """Discover and analyze sitemaps"""
        result = {'sitemap_urls': [], 'estimated_pages': 0}
        
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Common sitemap locations
        sitemap_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps.xml',
            '/sitemap1.xml'
        ]
        
        for location in sitemap_locations:
            try:
                sitemap_url = base_url + location
                response = self.session.get(sitemap_url, timeout=10)
                
                if response.status_code == 200:
                    result['sitemap_urls'].append(sitemap_url)
                    
                    # Parse sitemap to estimate page count
                    try:
                        root = ET.fromstring(response.content)
                        # Count URL entries
                        url_count = len(root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'))
                        # Count sitemap entries (for sitemap index files)
                        sitemap_count = len(root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'))
                        
                        if url_count > 0:
                            result['estimated_pages'] += url_count
                        elif sitemap_count > 0:
                            # Estimate pages in sub-sitemaps
                            result['estimated_pages'] += sitemap_count * 1000  # Conservative estimate
                            
                    except ET.ParseError:
                        pass
                        
            except Exception as e:
                logger.debug(f"Sitemap check failed for {location}: {e}")
        
        return result
    
    def _check_security_headers(self, url: str) -> Dict[str, Any]:
        """Check security headers that might affect scraping"""
        result = {'security_headers': {}, 'anti_bot_measures': []}
        
        try:
            response = self.session.head(url, timeout=10)
            
            security_headers = [
                'x-frame-options', 'x-content-type-options', 'x-xss-protection',
                'strict-transport-security', 'content-security-policy',
                'referrer-policy', 'x-robots-tag'
            ]
            
            for header in security_headers:
                if header in response.headers:
                    result['security_headers'][header] = response.headers[header]
            
            # Check for bot-blocking headers
            if 'x-robots-tag' in response.headers:
                robots_value = response.headers['x-robots-tag'].lower()
                if any(directive in robots_value for directive in ['noindex', 'nofollow', 'none']):
                    result['anti_bot_measures'].append('x_robots_tag_blocking')
                    
        except Exception as e:
            logger.warning(f"Security headers check failed: {e}")
        
        return result
    
    def _merge_analysis_result(self, characteristics: WebsiteCharacteristics, task_type: str, result: Dict[str, Any]):
        """Merge analysis result into characteristics"""
        if task_type == 'initial':
            characteristics.response_times.update(result.get('response_times', {}))
            characteristics.server_info.update(result.get('server_info', {}))
            characteristics.anti_bot_measures.extend(result.get('anti_bot_measures', []))
            characteristics.javascript_heavy = result.get('javascript_heavy', False)
            
        elif task_type == 'cms':
            characteristics.cms_type = result.get('cms_type')
            characteristics.api_endpoints.extend(result.get('api_endpoints', []))
            
        elif task_type == 'robots':
            characteristics.robots_txt_url = result.get('robots_txt_url')
            characteristics.rate_limits.update(result.get('rate_limits', {}))
            if 'sitemap_urls' in result:
                characteristics.sitemap_urls.extend(result['sitemap_urls'])
                
        elif task_type == 'sitemaps':
            characteristics.sitemap_urls.extend(result.get('sitemap_urls', []))
            characteristics.estimated_pages += result.get('estimated_pages', 0)
            
        elif task_type == 'security':
            characteristics.security_headers.update(result.get('security_headers', {}))
            characteristics.anti_bot_measures.extend(result.get('anti_bot_measures', []))
    
    def _calculate_risk_score(self, characteristics: WebsiteCharacteristics):
        """Calculate risk score for scraping"""
        risk_score = 0.0
        
        # Anti-bot measures increase risk
        risk_score += len(characteristics.anti_bot_measures) * 1.5
        
        # JavaScript-heavy sites are riskier
        if characteristics.javascript_heavy:
            risk_score += 2.0
        
        # Response time affects risk
        initial_time = characteristics.response_times.get('initial', 1.0)
        if initial_time > 5.0:
            risk_score += 1.5
        elif initial_time > 2.0:
            risk_score += 0.5
        
        # Security headers can indicate stricter policies
        if 'x-robots-tag' in characteristics.security_headers:
            risk_score += 1.0
        
        # Rate limiting indicators
        if characteristics.rate_limits:
            risk_score += 1.0
        
        # Unknown CMS types are riskier
        if not characteristics.cms_type:
            risk_score += 0.5
        
        characteristics.risk_score = min(risk_score, 10.0)
    
    def _recommend_delay(self, characteristics: WebsiteCharacteristics):
        """Recommend optimal delay between requests"""
        base_delay = 1.0
        
        # Adjust based on risk score
        base_delay += characteristics.risk_score * 0.3
        
        # Respect robots.txt crawl delay
        if 'crawl_delay' in characteristics.rate_limits:
            base_delay = max(base_delay, characteristics.rate_limits['crawl_delay'])
        
        # Adjust for response times
        initial_time = characteristics.response_times.get('initial', 1.0)
        if initial_time > 3.0:
            base_delay += 1.0
        
        # Additional delay for anti-bot measures
        if 'cloudflare' in characteristics.anti_bot_measures:
            base_delay += 1.0
        
        characteristics.recommended_delay = min(base_delay, 10.0)
    
    def _estimate_content_size(self, characteristics: WebsiteCharacteristics):
        """Estimate content size and type"""
        if characteristics.estimated_pages > 0:
            if characteristics.estimated_pages > 10000:
                characteristics.content_type = "large_site"
            elif characteristics.estimated_pages > 1000:
                characteristics.content_type = "medium_site"
            else:
                characteristics.content_type = "small_site"
        else:
            characteristics.content_type = "unknown_size"

class StrategyOptimizer:
    """Optimizes scraping strategies based on website analysis"""
    
    def __init__(self):
        self.scraper_capabilities = {
            'python': {
                'javascript_support': False,
                'concurrency': 'medium',
                'anti_detection': 'basic',
                'api_support': 'excellent',
                'best_for': ['api_heavy', 'academic', 'structured_data']
            },
            'javascript': {
                'javascript_support': True,
                'concurrency': 'medium',
                'anti_detection': 'excellent',
                'api_support': 'good',
                'best_for': ['javascript_heavy', 'spa', 'dynamic_content']
            },
            'go': {
                'javascript_support': False,
                'concurrency': 'excellent',
                'anti_detection': 'good',
                'api_support': 'good',
                'best_for': ['high_volume', 'concurrent_requests', 'forums']
            },
            'rust': {
                'javascript_support': False,
                'concurrency': 'excellent',
                'anti_detection': 'good',
                'api_support': 'excellent',
                'best_for': ['performance_critical', 'large_scale', 'documentation']
            }
        }
    
    def optimize_strategy(self, characteristics: WebsiteCharacteristics, scraping_goals: Dict[str, Any] = None) -> ScrapingStrategy:
        """Generate optimized scraping strategy"""
        if scraping_goals is None:
            scraping_goals = {}
        
        # Select optimal scraper
        recommended_scraper = self._select_optimal_scraper(characteristics, scraping_goals)
        
        # Generate scraper configuration
        scraper_config = self._generate_scraper_config(characteristics, recommended_scraper, scraping_goals)
        
        # Configure rate limiting
        rate_limiting = self._configure_rate_limiting(characteristics)
        
        # Configure anti-detection measures
        anti_detection = self._configure_anti_detection(characteristics, recommended_scraper)
        
        # Identify priority URLs
        priority_urls = self._identify_priority_urls(characteristics, scraping_goals)
        
        # Estimate duration
        estimated_duration = self._estimate_scraping_duration(characteristics, scraper_config)
        
        # Assess risks
        risk_assessment = self._assess_scraping_risks(characteristics)
        
        # Generate fallback strategies
        fallback_strategies = self._generate_fallback_strategies(characteristics, recommended_scraper)
        
        return ScrapingStrategy(
            target_url=characteristics.url,
            recommended_scraper=recommended_scraper,
            scraper_config=scraper_config,
            rate_limiting=rate_limiting,
            anti_detection=anti_detection,
            priority_urls=priority_urls,
            estimated_duration=estimated_duration,
            risk_assessment=risk_assessment,
            fallback_strategies=fallback_strategies,
            created_at=datetime.now().isoformat()
        )
    
    def _select_optimal_scraper(self, characteristics: WebsiteCharacteristics, goals: Dict[str, Any]) -> str:
        """Select the most suitable scraper"""
        scores = {}
        
        # Score each scraper type
        for scraper_type, capabilities in self.scraper_capabilities.items():
            score = 0.0
            
            # JavaScript requirement
            if characteristics.javascript_heavy and capabilities['javascript_support']:
                score += 3.0
            elif characteristics.javascript_heavy and not capabilities['javascript_support']:
                score -= 2.0
            
            # Concurrency needs
            volume = goals.get('expected_volume', 'medium')
            if volume == 'high' and capabilities['concurrency'] == 'excellent':
                score += 2.0
            elif volume == 'low' and capabilities['concurrency'] == 'excellent':
                score += 0.5  # Still good, but not necessary
            
            # Anti-detection requirements
            if characteristics.risk_score > 5.0 and capabilities['anti_detection'] == 'excellent':
                score += 2.0
            
            # API support
            if characteristics.api_endpoints and capabilities['api_support'] == 'excellent':
                score += 1.5
            
            # CMS-specific optimizations
            if characteristics.cms_type == 'shopify' and scraper_type == 'javascript':
                score += 1.0
            elif characteristics.cms_type == 'wordpress' and scraper_type == 'python':
                score += 1.0
            
            scores[scraper_type] = score
        
        # Return the highest scoring scraper
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _generate_scraper_config(self, characteristics: WebsiteCharacteristics, scraper_type: str, goals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scraper-specific configuration"""
        config = {
            'delay_between_requests': characteristics.recommended_delay,
            'timeout': 30,
            'retries': 3,
            'max_pages': goals.get('max_pages', 50),
            'respect_robots_txt': True
        }
        
        # Scraper-specific configurations
        if scraper_type == 'javascript':
            config.update({
                'headless': True,
                'stealth_mode': characteristics.risk_score > 3.0,
                'wait_for_content': characteristics.javascript_heavy,
                'block_resources': ['images', 'stylesheets'] if goals.get('fast_mode') else []
            })
        
        elif scraper_type == 'go':
            config.update({
                'concurrent_workers': min(10, max(2, 20 // max(int(characteristics.recommended_delay), 1))),
                'connection_pool_size': 100
            })
        
        elif scraper_type == 'rust':
            config.update({
                'max_concurrent': min(15, max(3, 30 // max(int(characteristics.recommended_delay), 1))),
                'connection_timeout': 30
            })
        
        # Platform-specific optimizations
        if characteristics.cms_type == 'shopify':
            config['api_endpoints'] = characteristics.api_endpoints
        elif characteristics.cms_type == 'wordpress':
            config['wp_api_endpoint'] = '/wp-json/wp/v2/'
        
        return config
    
    def _configure_rate_limiting(self, characteristics: WebsiteCharacteristics) -> Dict[str, Any]:
        """Configure intelligent rate limiting"""
        config = {
            'base_delay': characteristics.recommended_delay,
            'adaptive': True,
            'backoff_strategy': 'exponential',
            'max_delay': 30.0,
            'burst_protection': characteristics.risk_score > 4.0
        }
        
        # Respect robots.txt crawl delay
        if 'crawl_delay' in characteristics.rate_limits:
            config['min_delay'] = characteristics.rate_limits['crawl_delay']
        
        # Time-based rate limiting for busy sites
        if characteristics.response_times.get('initial', 0) > 3.0:
            config['time_based_limiting'] = True
            config['requests_per_minute'] = 10
        
        return config
    
    def _configure_anti_detection(self, characteristics: WebsiteCharacteristics, scraper_type: str) -> Dict[str, Any]:
        """Configure anti-detection measures"""
        config = {
            'rotate_user_agents': True,
            'randomize_headers': True,
            'session_rotation': characteristics.risk_score > 5.0
        }
        
        # High-risk sites need extra measures
        if characteristics.risk_score > 6.0:
            config.update({
                'proxy_rotation': True,
                'request_spacing_randomization': True,
                'behavioral_mimicking': True
            })
        
        # Anti-bot specific measures
        if 'cloudflare' in characteristics.anti_bot_measures:
            config.update({
                'cloudflare_bypass': True,
                'tls_fingerprint_randomization': True
            })
        
        # JavaScript scraper specific
        if scraper_type == 'javascript':
            config.update({
                'stealth_plugin': True,
                'viewport_randomization': True,
                'mouse_movement_simulation': characteristics.risk_score > 7.0
            })
        
        return config
    
    def _identify_priority_urls(self, characteristics: WebsiteCharacteristics, goals: Dict[str, Any]) -> List[str]:
        """Identify high-priority URLs to scrape first"""
        priority_urls = []
        
        # Start with the main URL
        priority_urls.append(characteristics.url)
        
        # Add API endpoints if available
        if characteristics.api_endpoints:
            base_url = f"{urlparse(characteristics.url).scheme}://{characteristics.domain}"
            for endpoint in characteristics.api_endpoints[:3]:  # Top 3 endpoints
                priority_urls.append(base_url + endpoint)
        
        # Add sitemap URLs for discovery
        if characteristics.sitemap_urls:
            priority_urls.extend(characteristics.sitemap_urls[:2])  # Top 2 sitemaps
        
        # Goal-specific priorities
        if goals.get('content_type') == 'products' and characteristics.cms_type == 'shopify':
            base_url = f"{urlparse(characteristics.url).scheme}://{characteristics.domain}"
            priority_urls.extend([
                base_url + '/products.json',
                base_url + '/collections.json'
            ])
        
        return priority_urls
    
    def _estimate_scraping_duration(self, characteristics: WebsiteCharacteristics, config: Dict[str, Any]) -> float:
        """Estimate total scraping duration"""
        max_pages = config.get('max_pages', 50)
        delay = config.get('delay_between_requests', 1.5)
        response_time = characteristics.response_times.get('initial', 1.0)
        
        # Base calculation
        duration = max_pages * (delay + response_time)
        
        # Add overhead for retries and errors
        error_overhead = duration * 0.2  # 20% overhead
        
        # Add setup time
        setup_time = 30  # 30 seconds for initialization
        
        return setup_time + duration + error_overhead
    
    def _assess_scraping_risks(self, characteristics: WebsiteCharacteristics) -> Dict[str, Any]:
        """Assess risks associated with scraping"""
        risks = {
            'overall_risk': characteristics.risk_score,
            'risk_factors': [],
            'mitigation_strategies': [],
            'success_probability': max(0.1, 1.0 - (characteristics.risk_score / 10))
        }
        
        # Identify specific risks
        if 'cloudflare' in characteristics.anti_bot_measures:
            risks['risk_factors'].append('cloudflare_protection')
            risks['mitigation_strategies'].append('use_javascript_scraper_with_stealth')
        
        if characteristics.javascript_heavy:
            risks['risk_factors'].append('javascript_dependency')
            risks['mitigation_strategies'].append('use_browser_automation')
        
        if 'rate_limiting_headers' in characteristics.anti_bot_measures:
            risks['risk_factors'].append('aggressive_rate_limiting')
            risks['mitigation_strategies'].append('implement_adaptive_delays')
        
        if characteristics.response_times.get('initial', 0) > 5.0:
            risks['risk_factors'].append('slow_response_times')
            risks['mitigation_strategies'].append('increase_timeouts_and_retries')
        
        return risks
    
    def _generate_fallback_strategies(self, characteristics: WebsiteCharacteristics, primary_scraper: str) -> List[Dict[str, Any]]:
        """Generate fallback strategies if primary fails"""
        fallbacks = []
        
        # If primary is not JavaScript, add JavaScript as fallback for JS-heavy sites
        if primary_scraper != 'javascript' and characteristics.javascript_heavy:
            fallbacks.append({
                'scraper_type': 'javascript',
                'reason': 'javascript_fallback',
                'config_changes': {'stealth_mode': True, 'wait_for_content': True}
            })
        
        # Add slower, more conservative approach
        fallbacks.append({
            'scraper_type': primary_scraper,
            'reason': 'conservative_approach',
            'config_changes': {
                'delay_between_requests': characteristics.recommended_delay * 2,
                'max_pages': 10,
                'retries': 5
            }
        })
        
        # API-only approach if available
        if characteristics.api_endpoints:
            fallbacks.append({
                'scraper_type': 'python',
                'reason': 'api_only',
                'config_changes': {
                    'api_only': True,
                    'endpoints': characteristics.api_endpoints
                }
            })
        
        return fallbacks

class PreScrapeEngine:
    """Main pre-scrape engine orchestrator"""
    
    def __init__(self, cache_dir: str = "/tmp/marina_prescrape_cache"):
        self.cache = PreScrapeCache(cache_dir)
        self.analyzer = WebsiteAnalyzer(self.cache)
        self.optimizer = StrategyOptimizer()
        logger.info("Pre-scrape engine initialized")
    
    def analyze_and_optimize(self, url: str, scraping_goals: Dict[str, Any] = None, force_refresh: bool = False) -> Tuple[WebsiteCharacteristics, ScrapingStrategy]:
        """Complete pre-scrape analysis and optimization"""
        logger.info(f"Starting pre-scrape analysis for: {url}")
        
        try:
            # Analyze website
            characteristics = self.analyzer.analyze_website(url, force_refresh)
            
            # Optimize scraping strategy
            strategy = self.optimizer.optimize_strategy(characteristics, scraping_goals)
            
            logger.info(f"Pre-scrape analysis complete. Risk score: {characteristics.risk_score:.1f}, Recommended scraper: {strategy.recommended_scraper}")
            
            return characteristics, strategy
            
        except Exception as e:
            logger.error(f"Pre-scrape analysis failed: {e}")
            raise
    
    def quick_assessment(self, url: str) -> Dict[str, Any]:
        """Quick assessment for immediate decisions"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Check if we have cached data
            cached = self.cache.get_website_analysis(domain)
            if cached:
                return {
                    'recommended_scraper': self._quick_scraper_recommendation(cached),
                    'recommended_delay': cached.recommended_delay,
                    'risk_score': cached.risk_score,
                    'estimated_duration': cached.estimated_pages * cached.recommended_delay * 1.2,
                    'cached': True
                }
            
            # Quick network check
            start_time = time.time()
            try:
                response = requests.head(url, timeout=5)
                response_time = time.time() - start_time
                
                # Basic assessment
                risk_score = 1.0
                if response.status_code >= 400:
                    risk_score += 2.0
                if response_time > 3.0:
                    risk_score += 1.0
                if 'cloudflare' in response.headers.get('Server', '').lower():
                    risk_score += 1.5
                
                return {
                    'recommended_scraper': 'python',  # Default
                    'recommended_delay': max(1.0, response_time + 0.5),
                    'risk_score': min(risk_score, 10.0),
                    'estimated_duration': 300,  # 5 minutes default
                    'cached': False
                }
                
            except Exception:
                return {
                    'recommended_scraper': 'python',
                    'recommended_delay': 3.0,
                    'risk_score': 5.0,
                    'estimated_duration': 600,
                    'cached': False
                }
                
        except Exception as e:
            logger.error(f"Quick assessment failed: {e}")
            return {
                'recommended_scraper': 'python',
                'recommended_delay': 2.0,
                'risk_score': 5.0,
                'estimated_duration': 600,
                'cached': False
            }
    
    def _quick_scraper_recommendation(self, characteristics: WebsiteCharacteristics) -> str:
        """Quick scraper recommendation based on characteristics"""
        if characteristics.javascript_heavy:
            return 'javascript'
        elif characteristics.estimated_pages > 1000:
            return 'go'
        elif characteristics.cms_type == 'documentation':
            return 'rust'
        else:
            return 'python'
    
    def batch_analyze(self, urls: List[str], max_workers: int = 5) -> Dict[str, Tuple[WebsiteCharacteristics, ScrapingStrategy]]:
        """Analyze multiple URLs concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.analyze_and_optimize, url): url 
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    characteristics, strategy = future.result()
                    results[url] = (characteristics, strategy)
                    logger.info(f"Completed analysis for {url}")
                except Exception as e:
                    logger.error(f"Failed to analyze {url}: {e}")
                    results[url] = None
        
        return results
    
    def export_strategy(self, strategy: ScrapingStrategy, filepath: str):
        """Export strategy to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(strategy), f, indent=2)
            logger.info(f"Strategy exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export strategy: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with sqlite3.connect(self.cache.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM website_analysis WHERE expires_at > ?", 
                                    (datetime.now().isoformat(),))
                active_analyses = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM robots_cache WHERE expires_at > ?", 
                                    (datetime.now().isoformat(),))
                active_robots = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sitemap_cache WHERE expires_at > ?", 
                                    (datetime.now().isoformat(),))
                active_sitemaps = cursor.fetchone()[0]
                
                return {
                    'active_website_analyses': active_analyses,
                    'active_robots_cache': active_robots,
                    'active_sitemap_cache': active_sitemaps,
                    'cache_directory': str(self.cache.cache_dir),
                    'database_size': self.cache.db_path.stat().st_size if self.cache.db_path.exists() else 0
                }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

if __name__ == "__main__":
    # Demo usage
    engine = PreScrapeEngine()
    
    # Test URLs
    test_urls = [
        "https://docs.python.org/",
        "https://github.com/",
        "https://stackoverflow.com/"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Analyzing: {url}")
        print('='*60)
        
        try:
            characteristics, strategy = engine.analyze_and_optimize(url)
            
            print(f"Domain: {characteristics.domain}")
            print(f"CMS Type: {characteristics.cms_type}")
            print(f"Risk Score: {characteristics.risk_score:.1f}/10")
            print(f"JavaScript Heavy: {characteristics.javascript_heavy}")
            print(f"Recommended Delay: {characteristics.recommended_delay:.1f}s")
            print(f"Estimated Pages: {characteristics.estimated_pages}")
            print(f"Anti-bot Measures: {characteristics.anti_bot_measures}")
            
            print(f"\nRecommended Scraper: {strategy.recommended_scraper}")
            print(f"Estimated Duration: {strategy.estimated_duration:.1f}s")
            print(f"Success Probability: {strategy.risk_assessment['success_probability']:.2f}")
            
        except Exception as e:
            print(f"Analysis failed: {e}")
