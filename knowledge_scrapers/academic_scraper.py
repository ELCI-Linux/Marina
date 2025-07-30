#!/usr/bin/env python3
"""
Academic Paper Scraper

This modular scraper extracts academic papers and research content from repositories like:
- arXiv
- PubMed
- IEEE Xplore
- ACM Digital Library
- ResearchGate
- Google Scholar

Features include:
- Paper metadata extraction (title, authors, abstract, citations)
- PDF content extraction
- Citation analysis
- Research field categorization
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
import xml.etree.ElementTree as ET

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class AcademicPaper:
    """Represents an academic paper with extracted metadata"""
    url: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: Optional[str]
    journal: Optional[str]
    keywords: List[str]
    citations_count: Optional[int]
    doi: Optional[str]
    pdf_url: Optional[str]
    research_field: Optional[str]
    institution: Optional[str]
    scraped_at: str

class AcademicScraper:
    """
    Modular academic paper scraper supporting various research repositories
    """
    
    def __init__(self, repository: str = 'arxiv', delay_between_requests: float = 2.0):
        self.repository = repository.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-AcademicScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Repository-specific configurations
        self.repo_configs = {
            'arxiv': {
                'paper_selector': '.arxiv-result',
                'title_selector': 'p.title',
                'authors_selector': 'p.authors a',
                'abstract_selector': 'p.abstract span',
                'date_selector': 'p.is-size-7',
                'pdf_pattern': r'https://arxiv\.org/pdf/[\d\.]+\.pdf'
            },
            'pubmed': {
                'paper_selector': '.search-result',
                'title_selector': '.heading-title',
                'authors_selector': '.authors .author',
                'abstract_selector': '.abstract-text',
                'date_selector': '.publication-date',
                'journal_selector': '.journal-title'
            },
            'ieee': {
                'paper_selector': '.List-results-items',
                'title_selector': '.fw-bold a',
                'authors_selector': '.author',
                'abstract_selector': '.abstract',
                'date_selector': '.date',
                'journal_selector': '.publisher'
            },
            'acm': {
                'paper_selector': '.issue-item',
                'title_selector': '.hlFld-Title',
                'authors_selector': '.hlFld-ContribAuthor',
                'abstract_selector': '.abstract',
                'date_selector': '.core-date-published',
                'journal_selector': '.journal-title'
            },
            'scholar': {
                'paper_selector': '.gs_ri',
                'title_selector': 'h3 a',
                'authors_selector': '.gs_a',
                'abstract_selector': '.gs_rs',
                'citations_selector': '.gs_fl a'
            }
        }
    
    def extract_authors(self, soup_element, config: Dict) -> List[str]:
        """Extract author names from paper element"""
        authors = []
        
        author_elements = soup_element.select(config.get('authors_selector', ''))
        
        for author_elem in author_elements:
            author_text = author_elem.get_text(strip=True)
            # Clean up author names
            author_text = re.sub(r'\d+$', '', author_text)  # Remove trailing numbers
            author_text = re.sub(r'[,;]$', '', author_text)  # Remove trailing punctuation
            
            if author_text and len(author_text) > 2:
                authors.append(author_text)
        
        return authors[:10]  # Limit to first 10 authors
    
    def extract_keywords(self, title: str, abstract: str) -> List[str]:
        """Extract keywords from title and abstract using pattern matching"""
        text = f"{title} {abstract}".lower()
        
        # Common academic keywords patterns
        keyword_patterns = [
            r'\bmachine learning\b',
            r'\bartificial intelligence\b',
            r'\bdeep learning\b',
            r'\bneural network\b',
            r'\bnatural language processing\b',
            r'\bcomputer vision\b',
            r'\bdata mining\b',
            r'\bbig data\b',
            r'\balgorithm\b',
            r'\bclassification\b',
            r'\bregression\b',
            r'\bclustering\b',
            r'\boptimization\b',
            r'\bstatistics\b',
            r'\bbioinformatics\b',
            r'\bmedicine\b',
            r'\bphysics\b',
            r'\bchemistry\b',
            r'\bsoftware engineering\b',
            r'\bdatabase\b'
        ]
        
        keywords = []
        for pattern in keyword_patterns:
            if re.search(pattern, text):
                keywords.append(pattern.replace(r'\b', '').replace('\\', ''))
        
        return keywords
    
    def extract_research_field(self, title: str, abstract: str, journal: str = '') -> str:
        """Classify research field based on content"""
        text = f"{title} {abstract} {journal}".lower()
        
        field_patterns = {
            'Computer Science': [r'algorithm', r'software', r'computer', r'programming', r'database'],
            'Machine Learning': [r'machine learning', r'neural network', r'deep learning', r'ai'],
            'Medicine': [r'medical', r'patient', r'clinical', r'health', r'disease'],
            'Physics': [r'quantum', r'particle', r'physics', r'energy', r'matter'],
            'Biology': [r'biological', r'gene', r'protein', r'cell', r'organism'],
            'Mathematics': [r'mathematical', r'theorem', r'proof', r'equation', r'statistics'],
            'Chemistry': [r'chemical', r'molecule', r'reaction', r'compound', r'synthesis'],
            'Engineering': [r'engineering', r'design', r'system', r'optimization', r'control']
        }
        
        for field, patterns in field_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                return field
        
        return 'General'
    
    def scrape_arxiv_paper(self, paper_element) -> Optional[AcademicPaper]:
        """Specialized scraper for arXiv papers"""
        try:
            config = self.repo_configs['arxiv']
            
            # Extract title
            title_elem = paper_element.select_one(config['title_selector'])
            title = title_elem.get_text(strip=True).replace('Title:', '') if title_elem else 'Unknown'
            
            # Extract authors
            authors = self.extract_authors(paper_element, config)
            
            # Extract abstract
            abstract_elem = paper_element.select_one(config['abstract_selector'])
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else 'No abstract available'
            
            # Extract publication date
            date_elem = paper_element.select_one(config['date_selector'])
            pub_date = None
            if date_elem:
                date_text = date_elem.get_text()
                date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', date_text)
                if date_match:
                    pub_date = date_match.group(1)
            
            # Extract PDF URL
            pdf_links = paper_element.find_all('a', href=re.compile(r'\.pdf'))
            pdf_url = pdf_links[0]['href'] if pdf_links else None
            
            # Extract arXiv ID for DOI-like identifier
            arxiv_links = paper_element.find_all('a', href=re.compile(r'arxiv\.org/abs/'))
            doi = None
            if arxiv_links:
                arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', arxiv_links[0]['href'])
                if arxiv_match:
                    doi = f"arXiv:{arxiv_match.group(1)}"
            
            # Generate paper URL
            paper_url = arxiv_links[0]['href'] if arxiv_links else 'Unknown'
            
            keywords = self.extract_keywords(title, abstract)
            research_field = self.extract_research_field(title, abstract)
            
            return AcademicPaper(
                url=paper_url,
                title=title,
                authors=authors,
                abstract=abstract,
                publication_date=pub_date,
                journal='arXiv',
                keywords=keywords,
                citations_count=None,  # arXiv doesn't show citation counts
                doi=doi,
                pdf_url=pdf_url,
                research_field=research_field,
                institution=None,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error scraping arXiv paper: {e}")
            return None
    
    def scrape_paper(self, paper_element, base_url: str) -> Optional[AcademicPaper]:
        """Generic paper scraper that delegates to repository-specific methods"""
        
        if self.repository == 'arxiv':
            return self.scrape_arxiv_paper(paper_element)
        
        # Generic scraping for other repositories
        try:
            config = self.repo_configs.get(self.repository, {})
            
            # Extract title
            title_elem = paper_element.select_one(config.get('title_selector', 'h3, .title'))
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Extract authors
            authors = self.extract_authors(paper_element, config)
            
            # Extract abstract
            abstract_elem = paper_element.select_one(config.get('abstract_selector', '.abstract'))
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else 'No abstract available'
            
            # Extract other metadata
            date_elem = paper_element.select_one(config.get('date_selector', '.date'))
            pub_date = date_elem.get_text(strip=True) if date_elem else None
            
            journal_elem = paper_element.select_one(config.get('journal_selector', '.journal'))
            journal = journal_elem.get_text(strip=True) if journal_elem else None
            
            # Extract paper URL
            link_elem = paper_element.select_one('a[href]')
            paper_url = urljoin(base_url, link_elem['href']) if link_elem else base_url
            
            keywords = self.extract_keywords(title, abstract)
            research_field = self.extract_research_field(title, abstract, journal or '')
            
            return AcademicPaper(
                url=paper_url,
                title=title,
                authors=authors,
                abstract=abstract,
                publication_date=pub_date,
                journal=journal,
                keywords=keywords,
                citations_count=None,
                doi=None,
                pdf_url=None,
                research_field=research_field,
                institution=None,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error scraping paper: {e}")
            return None
    
    def search_papers(self, query: str, max_papers: int = 20) -> List[AcademicPaper]:
        """Search for papers using repository-specific search endpoints"""
        papers = []
        
        if self.repository == 'arxiv':
            papers = self._search_arxiv(query, max_papers)
        elif self.repository == 'pubmed':
            papers = self._search_pubmed(query, max_papers)
        else:
            print(f"⚠️  Search not implemented for {self.repository}")
        
        return papers
    
    def _search_arxiv(self, query: str, max_papers: int) -> List[AcademicPaper]:
        """Search arXiv using their API"""
        papers = []
        
        try:
            # arXiv API endpoint
            api_url = 'http://export.arxiv.org/api/query'
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_papers,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            print(f"🔍 Searching arXiv for: {query}")
            time.sleep(self.delay)
            
            response = self.session.get(api_url, params=params, timeout=30)
            if response.status_code != 200:
                print(f"❌ arXiv API request failed: {response.status_code}")
                return []
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Handle namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Extract metadata from XML
                    title = entry.find('atom:title', namespaces).text.strip()
                    summary = entry.find('atom:summary', namespaces).text.strip()
                    
                    # Extract authors
                    authors = []
                    author_elements = entry.findall('atom:author', namespaces)
                    for author in author_elements:
                        name_elem = author.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # Extract dates
                    published = entry.find('atom:published', namespaces)
                    pub_date = published.text[:10] if published is not None else None  # YYYY-MM-DD
                    
                    # Extract URLs
                    paper_url = entry.find('atom:id', namespaces).text.strip()
                    
                    # Find PDF link
                    pdf_url = None
                    links = entry.findall('atom:link', namespaces)
                    for link in links:
                        if link.get('type') == 'application/pdf':
                            pdf_url = link.get('href')
                            break
                    
                    # Extract arXiv ID
                    arxiv_id_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', paper_url)
                    doi = f"arXiv:{arxiv_id_match.group(1)}" if arxiv_id_match else None
                    
                    keywords = self.extract_keywords(title, summary)
                    research_field = self.extract_research_field(title, summary)
                    
                    paper = AcademicPaper(
                        url=paper_url,
                        title=title,
                        authors=authors,
                        abstract=summary,
                        publication_date=pub_date,
                        journal='arXiv',
                        keywords=keywords,
                        citations_count=None,
                        doi=doi,
                        pdf_url=pdf_url,
                        research_field=research_field,
                        institution=None,
                        scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"❌ Error parsing arXiv entry: {e}")
                    continue
            
            print(f"✅ Found {len(papers)} papers on arXiv")
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
        
        return papers
    
    def _search_pubmed(self, query: str, max_papers: int) -> List[AcademicPaper]:
        """Search PubMed using their API (placeholder - would need API key)"""
        print("⚠️  PubMed search requires API key and is not implemented in this demo")
        return []
    
    def scrape_repository(self, search_url: str, max_papers: int = 20) -> List[AcademicPaper]:
        """Scrape papers from a repository search results page"""
        papers = []
        
        try:
            print(f"🚀 Scraping {self.repository} from: {search_url}")
            time.sleep(self.delay)
            
            response = self.session.get(search_url, timeout=30)
            if response.status_code != 200:
                print(f"❌ Failed to fetch search results: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.repo_configs.get(self.repository, {})
            
            # Find paper elements
            paper_elements = soup.select(config.get('paper_selector', '.paper, .result'))
            
            for paper_element in paper_elements[:max_papers]:
                paper = self.scrape_paper(paper_element, search_url)
                if paper:
                    papers.append(paper)
            
            print(f"✅ Scraped {len(papers)} papers from {self.repository}")
            
        except Exception as e:
            print(f"❌ Error scraping repository: {e}")
        
        return papers
    
    def save_results(self, papers: List[AcademicPaper], filename: str = None):
        """Save scraped papers to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"academic_scrape_{self.repository}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        papers_data = [paper.__dict__ for paper in papers]
        
        with open(filepath, 'w') as f:
            json.dump({
                'repository': self.repository,
                'total_papers': len(papers),
                'research_fields': list(set(paper.research_field for paper in papers)),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'papers': papers_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples
if __name__ == '__main__':
    # Example: Search arXiv for machine learning papers
    arxiv_scraper = AcademicScraper('arxiv', delay_between_requests=3.0)
    
    # Search for papers
    papers = arxiv_scraper.search_papers('machine learning', max_papers=10)
    
    if papers:
        print(f"Found {len(papers)} papers:")
        for paper in papers[:3]:  # Show first 3
            print(f"- {paper.title}")
            print(f"  Authors: {', '.join(paper.authors[:3])}")
            print(f"  Field: {paper.research_field}")
            print()
        
        arxiv_scraper.save_results(papers)
    
    print("Academic Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = AcademicScraper('arxiv')")
    print("  papers = scraper.search_papers('quantum computing')")
    print("  scraper.save_results(papers)")
