#!/usr/bin/env python3
"""
Documentation Scraper

This modular scraper extracts technical documentation and API references from various sources. Features include:
- API documentation extraction (methods, parameters, examples)
- Technical guide parsing
- Code example extraction
- Support for popular documentation platforms (GitBook, ReadTheDocs, Swagger)
- Hierarchical content organization
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
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from datetime import datetime

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class CodeExample:
    """Represents a code example from documentation"""
    language: str
    code: str
    description: Optional[str]

@dataclass
class APIEndpoint:
    """Represents an API endpoint documentation"""
    method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    description: str
    parameters: List[Dict]
    response_format: Optional[str]
    code_examples: List[CodeExample]

@dataclass
class DocumentationPage:
    """Represents a documentation page with extracted content"""
    url: str
    title: str
    content: str
    section: Optional[str]
    subsection: Optional[str]
    api_endpoints: List[APIEndpoint]
    code_examples: List[CodeExample]
    last_updated: Optional[str]
    tags: List[str]
    scraped_at: str

class DocumentationScraper:
    """
    Modular documentation scraper supporting various documentation platforms
    """
    
    def __init__(self, platform: str = 'generic', delay_between_requests: float = 1.0):
        self.platform = platform.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-DocumentationScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Platform-specific configurations
        self.platform_configs = {
            'gitbook': {
                'content_selector': '.page-inner',
                'title_selector': 'h1',
                'section_selector': '.summary .chapter.active',
                'code_selector': 'pre code',
                'navigation_selector': '.summary a'
            },
            'readthedocs': {
                'content_selector': '[role="main"]',
                'title_selector': 'h1',
                'section_selector': '.toctree-l1.current',
                'code_selector': '.highlight pre',
                'navigation_selector': '.toctree-l1 a'
            },
            'swagger': {
                'content_selector': '.swagger-ui',
                'endpoint_selector': '.opblock',
                'method_selector': '.opblock-summary-method',
                'path_selector': '.opblock-summary-path',
                'description_selector': '.opblock-description'
            },
            'sphinx': {
                'content_selector': '.body',
                'title_selector': 'h1',
                'section_selector': '.toctree-l1',
                'code_selector': '.highlight pre',
                'navigation_selector': '.toctree-l1 a'
            },
            'generic': {
                'content_selector': 'main, .content, .documentation',
                'title_selector': 'h1',
                'section_selector': '.section, .chapter',
                'code_selector': 'pre, code',
                'navigation_selector': 'nav a, .toc a'
            }
        }
    
    def extract_code_examples(self, soup: BeautifulSoup) -> List[CodeExample]:
        """Extract code examples from documentation page"""
        examples = []
        config = self.platform_configs.get(self.platform, self.platform_configs['generic'])
        
        code_blocks = soup.select(config['code_selector'])
        
        for block in code_blocks:
            # Try to detect language from class names
            language = 'text'  # default
            class_names = block.get('class', [])
            
            for class_name in class_names:
                if 'language-' in class_name:
                    language = class_name.replace('language-', '')
                    break
                elif class_name in ['python', 'javascript', 'java', 'c', 'cpp', 'bash', 'sql']:
                    language = class_name
                    break
            
            code_content = block.get_text()
            
            # Skip very short code snippets (likely not examples)
            if len(code_content.strip()) < 10:
                continue
            
            # Try to find description from preceding elements
            description = None
            prev_elem = block.find_previous(['p', 'h1', 'h2', 'h3', 'h4'])
            if prev_elem and prev_elem.name in ['p']:
                desc_text = prev_elem.get_text(strip=True)
                if len(desc_text) < 200:  # Reasonable description length
                    description = desc_text
            
            examples.append(CodeExample(
                language=language,
                code=code_content.strip(),
                description=description
            ))
        
        return examples
    
    def extract_api_endpoints(self, soup: BeautifulSoup) -> List[APIEndpoint]:
        """Extract API endpoint information (mainly for Swagger/OpenAPI docs)"""
        endpoints = []
        
        if self.platform == 'swagger':
            config = self.platform_configs['swagger']
            endpoint_blocks = soup.select(config.get('endpoint_selector', ''))
            
            for block in endpoint_blocks:
                method_elem = block.select_one(config.get('method_selector', ''))
                path_elem = block.select_one(config.get('path_selector', ''))
                desc_elem = block.select_one(config.get('description_selector', ''))
                
                if method_elem and path_elem:
                    method = method_elem.get_text(strip=True).upper()
                    path = path_elem.get_text(strip=True)
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    # Extract parameters (simplified)
                    parameters = []
                    param_elements = block.select('.parameters .parameter')
                    for param_elem in param_elements:
                        param_name = param_elem.select_one('.parameter-name')
                        param_type = param_elem.select_one('.parameter-type')
                        param_desc = param_elem.select_one('.parameter-description')
                        
                        if param_name:
                            parameters.append({
                                'name': param_name.get_text(strip=True),
                                'type': param_type.get_text(strip=True) if param_type else 'string',
                                'description': param_desc.get_text(strip=True) if param_desc else ''
                            })
                    
                    # Extract code examples for this endpoint
                    code_examples = []
                    example_blocks = block.select('.example pre')
                    for example in example_blocks:
                        code_examples.append(CodeExample(
                            language='json',  # Most API examples are JSON
                            code=example.get_text(strip=True),
                            description='API response example'
                        ))
                    
                    endpoints.append(APIEndpoint(
                        method=method,
                        path=path,
                        description=description,
                        parameters=parameters,
                        response_format=None,  # Could be extracted from examples
                        code_examples=code_examples
                    ))
        
        return endpoints
    
    def extract_section_info(self, soup: BeautifulSoup, url: str) -> tuple:
        """Extract section and subsection information"""
        config = self.platform_configs.get(self.platform, self.platform_configs['generic'])
        
        section = None
        subsection = None
        
        # Try to extract from navigation breadcrumbs
        breadcrumbs = soup.select('.breadcrumb li, .breadcrumbs a')
        if breadcrumbs and len(breadcrumbs) > 1:
            section = breadcrumbs[-2].get_text(strip=True)
            if len(breadcrumbs) > 2:
                subsection = breadcrumbs[-1].get_text(strip=True)
        
        # Fallback: extract from URL structure
        if not section:
            path_parts = urlparse(url).path.strip('/').split('/')
            if len(path_parts) > 1:
                section = path_parts[-2].replace('-', ' ').replace('_', ' ').title()
                if len(path_parts) > 2:
                    subsection = path_parts[-1].replace('-', ' ').replace('_', ' ').title()
        
        return section, subsection
    
    def extract_tags(self, title: str, content: str, section: str = None) -> List[str]:
        """Extract relevant tags from documentation content"""
        text = f"{title} {content} {section or ''}".lower()
        
        # Common documentation tags
        tag_patterns = {
            'api': [r'\bapi\b', r'\bendpoint\b', r'\brest\b'],
            'tutorial': [r'\btutorial\b', r'\bguide\b', r'\bwalkthrough\b'],
            'reference': [r'\breference\b', r'\bdocs\b', r'\bdocumentation\b'],
            'installation': [r'\binstall\b', r'\bsetup\b', r'\bconfiguration\b'],
            'authentication': [r'\bauth\b', r'\blogin\b', r'\btoken\b', r'\bsecurity\b'],
            'database': [r'\bdatabase\b', r'\bsql\b', r'\bmongo\b', r'\bmysql\b'],
            'frontend': [r'\bfrontend\b', r'\bui\b', r'\bjavascript\b', r'\breact\b'],
            'backend': [r'\bbackend\b', r'\bserver\b', r'\bnode\b', r'\bpython\b'],
            'mobile': [r'\bmobile\b', r'\bios\b', r'\bandroid\b', r'\bapp\b'],
            'deployment': [r'\bdeploy\b', r'\bproduction\b', r'\bhosting\b']
        }
        
        tags = []
        for tag, patterns in tag_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                tags.append(tag)
        
        return tags
    
    def scrape_documentation_page(self, url: str) -> Optional[DocumentationPage]:
        """Scrape a single documentation page"""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        try:
            print(f"📚 Scraping documentation: {url}")
            time.sleep(self.delay)
            
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                print(f"❌ Failed to fetch {url}: HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.platform_configs.get(self.platform, self.platform_configs['generic'])
            
            # Extract title
            title_elem = soup.select_one(config['title_selector'])
            title = title_elem.get_text(strip=True) if title_elem else 'Documentation Page'
            
            # Extract main content
            content_elem = soup.select_one(config['content_selector'])
            content = content_elem.get_text(separator='\n', strip=True) if content_elem else ''
            
            # Skip pages with very little content
            if len(content) < 100:
                print(f"⚠️  Skipping page with minimal content: {url}")
                return None
            
            # Extract section information
            section, subsection = self.extract_section_info(soup, url)
            
            # Extract code examples
            code_examples = self.extract_code_examples(soup)
            
            # Extract API endpoints (if applicable)
            api_endpoints = self.extract_api_endpoints(soup)
            
            # Extract last updated date
            last_updated = None
            date_patterns = [
                '.last-updated', '.date-modified', '.updated-date'
            ]
            for pattern in date_patterns:
                date_elem = soup.select_one(pattern)
                if date_elem:
                    last_updated = date_elem.get_text(strip=True)
                    break
            
            # Extract tags
            tags = self.extract_tags(title, content, section)
            
            return DocumentationPage(
                url=url,
                title=title,
                content=content,
                section=section,
                subsection=subsection,
                api_endpoints=api_endpoints,
                code_examples=code_examples,
                last_updated=last_updated,
                tags=tags,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error scraping documentation page {url}: {e}")
            return None
    
    def discover_documentation_links(self, base_url: str, max_pages: int = 50) -> List[str]:
        """Discover documentation page links from navigation or sitemap"""
        doc_links = []
        
        try:
            response = self.session.get(base_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch base documentation: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.platform_configs.get(self.platform, self.platform_configs['generic'])
            
            # Find navigation links
            nav_links = soup.select(config['navigation_selector'])
            
            for link in nav_links[:max_pages]:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    
                    # Filter out external links and non-documentation pages
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        doc_links.append(full_url)
            
            # Also look for sitemap or index pages
            sitemap_patterns = [
                'a[href*="sitemap"]', 'a[href*="index"]', 
                'a[href*="contents"]', 'a[href*="toc"]'
            ]
            
            for pattern in sitemap_patterns:
                sitemap_links = soup.select(pattern)
                for link in sitemap_links:
                    href = link.get('href')
                    if href:
                        sitemap_url = urljoin(base_url, href)
                        if sitemap_url not in doc_links:
                            doc_links.append(sitemap_url)
                            
        except Exception as e:
            print(f"❌ Error discovering documentation links: {e}")
        
        return list(set(doc_links))[:max_pages]  # Remove duplicates and limit
    
    def scrape_documentation_site(self, base_url: str, max_pages: int = 30) -> List[DocumentationPage]:
        """Scrape multiple pages from a documentation site"""
        print(f"📖 Starting documentation scraping from: {base_url}")
        
        # Start with the base URL
        doc_urls = [base_url]
        
        # Discover additional documentation pages
        discovered_urls = self.discover_documentation_links(base_url, max_pages - 1)
        doc_urls.extend(discovered_urls)
        
        scraped_pages = []
        
        for url in doc_urls[:max_pages]:
            page = self.scrape_documentation_page(url)
            if page:
                scraped_pages.append(page)
        
        print(f"✅ Scraped {len(scraped_pages)} documentation pages")
        return scraped_pages
    
    def analyze_documentation(self, pages: List[DocumentationPage]) -> Dict:
        """Analyze scraped documentation for insights"""
        if not pages:
            return {}
        
        analysis = {
            'total_pages': len(pages),
            'sections': {},
            'tags': {},
            'programming_languages': {},
            'total_code_examples': 0,
            'total_api_endpoints': 0,
            'avg_content_length': 0
        }
        
        # Analyze sections
        for page in pages:
            if page.section:
                analysis['sections'][page.section] = analysis['sections'].get(page.section, 0) + 1
        
        # Analyze tags
        for page in pages:
            for tag in page.tags:
                analysis['tags'][tag] = analysis['tags'].get(tag, 0) + 1
        
        # Analyze programming languages in code examples
        for page in pages:
            analysis['total_code_examples'] += len(page.code_examples)
            for example in page.code_examples:
                lang = example.language
                analysis['programming_languages'][lang] = analysis['programming_languages'].get(lang, 0) + 1
        
        # Count API endpoints
        for page in pages:
            analysis['total_api_endpoints'] += len(page.api_endpoints)
        
        # Calculate average content length
        content_lengths = [len(page.content) for page in pages]
        analysis['avg_content_length'] = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        return analysis
    
    def save_results(self, pages: List[DocumentationPage], filename: str = None):
        """Save scraped documentation to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"documentation_scrape_{self.platform}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        pages_data = []
        for page in pages:
            page_dict = page.__dict__.copy()
            # Convert nested dataclasses
            page_dict['code_examples'] = [ex.__dict__ for ex in page.code_examples]
            page_dict['api_endpoints'] = []
            for endpoint in page.api_endpoints:
                endpoint_dict = endpoint.__dict__.copy()
                endpoint_dict['code_examples'] = [ex.__dict__ for ex in endpoint.code_examples]
                page_dict['api_endpoints'].append(endpoint_dict)
            pages_data.append(page_dict)
        
        # Generate analysis
        analysis = self.analyze_documentation(pages)
        
        with open(filepath, 'w') as f:
            json.dump({
                'platform': self.platform,
                'total_pages': len(pages),
                'analysis': analysis,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pages': pages_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples
if __name__ == '__main__':
    # Example: Scrape ReadTheDocs documentation
    rtd_scraper = DocumentationScraper('readthedocs', delay_between_requests=1.5)
    
    # Scrape documentation site
    pages = rtd_scraper.scrape_documentation_site('https://docs.example.com/', max_pages=20)
    
    if pages:
        print(f"Found {len(pages)} documentation pages:")
        for page in pages[:3]:  # Show first 3
            print(f"- {page.title}")
            print(f"  Section: {page.section}")
            print(f"  Code Examples: {len(page.code_examples)}")
            print(f"  Tags: {', '.join(page.tags)}")
            print()
        
        # Analyze documentation
        analysis = rtd_scraper.analyze_documentation(pages)
        if analysis:
            print("Documentation Analysis:")
            print(f"  Total Code Examples: {analysis.get('total_code_examples', 0)}")
            print(f"  Programming Languages: {list(analysis.get('programming_languages', {}).keys())}")
            print(f"  Common Tags: {list(analysis.get('tags', {}).keys())}")
        
        rtd_scraper.save_results(pages)
    
    print("Documentation Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = DocumentationScraper('gitbook')")
    print("  pages = scraper.scrape_documentation_site('https://docs.example.com/')")
    print("  scraper.save_results(pages)")
