#!/usr/bin/env python3
"""
Job Listings Scraper

This modular scraper extracts job listings from online job portals and career sites. Features include:
- Extraction of job title, company, location, description, and requirements
- Industry categorization
- Support for common job sites (Indeed, LinkedIn, Glassdoor)
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
class JobListing:
    """Represents a job listing with extracted details"""
    url: str
    job_title: str
    company: str
    location: str
    description: str
    posted_date: Optional[str]
    requirements: List[str]
    job_type: Optional[str]
    industry: Optional[str]
    experience_level: Optional[str]
    scraped_at: str

class JobScraper:
    """
    Modular job listing scraper supporting various online job portals
    """
    
    def __init__(self, portal: str, delay_between_requests: float = 1.5):
        self.portal = portal.lower()
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Marina-JobScraper/1.0 (Educational Research)'
        })
        self.visited_urls = set()
        
        # Portal-specific configurations
        self.portal_configs = {
            'indeed': {
                'job_selector': '.jobsearch-SerpJobCard',
                'title_selector': '.jobtitle',
                'company_selector': '.company',
                'location_selector': '.location',
                'description_selector': '.summary',
                'posted_date_selector': '.date'
            },
            'linkedin': {
                'job_selector': '.result-card',
                'title_selector': '.result-card__title',
                'company_selector': '.result-card__subtitle',
                'location_selector': '.result-card__meta > span:nth-child(1)',
                'description_selector': '.result-card__snippets',
                'posted_date_selector': '.posted-time-ago__text'
            },
            'glassdoor': {
                'job_selector': '.jl',
                'title_selector': '.jobLink',
                'company_selector': '.emp',
                'location_selector': '.loc',
                'description_selector': '.jobDesc',
                'posted_date_selector': '.date'
            }
        }
    
    def extract_requirements(self, description: str) -> List[str]:
        """Extract job requirements from job description"""
        requirements = []
        lines = description.split('\n')
        requirement_patterns = [r'\bRequirements?\b', r'\bQualifications?\b', r'\bSkills?\b']
        
        for line in lines:
            for pattern in requirement_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    bullets = line.split(',')
                    requirements.extend(bullets)
        
        # Clean up requirements
        cleaned_requirements = [req.strip() for req in requirements if req.strip()]
        return cleaned_requirements
    
    def extract_industry(self, title: str, description: str) -> str:
        """Detect industry based on job title and description"""
        text = f"{title} {description}".lower()
        
        industry_patterns = {
            'Software & IT': [r'software', r'developer', r'engineer', r'it'],
            'Finance': [r'finance', r'accountant', r'banking', r'investment'],
            'Healthcare': [r'healthcare', r'nurse', r'medical', r'doctor'],
            'Education': [r'teacher', r'education', r'trainer'],
            'Construction': [r'construction', r'engineer', r'architect', r'project manager'],
        }
        
        for industry, patterns in industry_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                return industry
        
        return 'General'
    
    def scrape_job(self, job_element) -> Optional[JobListing]:
        """Extract data from a single job listing element"""
        try:
            config = self.portal_configs.get(self.portal, {})
            
            # Extract job title
            title_elem = job_element.select_one(config.get('title_selector', ''))
            job_title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Extract company
            company_elem = job_element.select_one(config.get('company_selector', ''))
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
            
            # Extract location
            location_elem = job_element.select_one(config.get('location_selector', ''))
            location = location_elem.get_text(strip=True) if location_elem else 'Unknown'
            
            # Extract description
            description_elem = job_element.select_one(config.get('description_selector', ''))
            description = description_elem.get_text(strip=True) if description_elem else 'No description available'
            
            # Extract posted date
            posted_date_elem = job_element.select_one(config.get('posted_date_selector', ''))
            posted_date = posted_date_elem.get_text(strip=True) if posted_date_elem else None
            
            # Derive additional metadata
            requirements = self.extract_requirements(description)
            industry = self.extract_industry(job_title, description)
            job_type = 'Full-time' if 'full-time' in description.lower() else 'Part-time'
            experience_level = 'Entry Level' if 'entry level' in description.lower() else 'Mid Level'
            
            # Generate job URL
            link_elem = job_element.find('a', href=True)
            job_url = urljoin('https://example-job-portal.com', link_elem['href']) if link_elem else 'Unknown'
            
            return JobListing(
                url=job_url,
                job_title=job_title,
                company=company,
                location=location,
                description=description,
                posted_date=posted_date,
                requirements=requirements,
                job_type=job_type,
                industry=industry,
                experience_level=experience_level,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            print(f"❌ Error extracting job listing: {e}")
            return None
    
    def discover_jobs(self, search_url: str, max_jobs: int = 10) -> List[JobListing]:
        """Discover and scrape job listings from a portal"""
        jobs = []
        
        try:
            print(f"🔍 Starting job scraping from: {search_url}")
            time.sleep(self.delay)
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to fetch job listings: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            config = self.portal_configs.get(self.portal, {})
            
            # Find job elements
            job_elements = soup.select(config.get('job_selector', '.job'))
            
            for job_element in job_elements[:max_jobs]:
                job = self.scrape_job(job_element)
                if job:
                    jobs.append(job)
            
            print(f"✅ Scraped {len(jobs)} jobs from {self.portal}")
            
        except Exception as e:
            print(f"❌ Error discovering jobs: {e}")
        
        return jobs
    
    def save_results(self, jobs: List[JobListing], filename: str = None):
        """Save scraped job listings to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"job_scrape_{self.portal}_{timestamp}.json"
        
        results_dir = "/home/adminx/Marina/knowledge_scrapers/scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # Convert dataclass instances to dictionaries for JSON serialization
        jobs_data = [job.__dict__ for job in jobs]
        
        with open(filepath, 'w') as f:
            json.dump({
                'portal': self.portal,
                'total_jobs': len(jobs),
                'industries': list(set(job.industry for job in jobs)),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'jobs': jobs_data
            }, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")

# Usage examples
if __name__ == '__main__':
    # Example: Scrape Indeed for software jobs
    indeed_scraper = JobScraper('indeed', delay_between_requests=2.0)
    
    # Discover jobs
    jobs = indeed_scraper.discover_jobs('https://www.indeed.com/jobs?q=software+developer&l=', max_jobs=10)
    
    if jobs:
        print(f"Found {len(jobs)} job listings:")
        for job in jobs[:3]:  # Show first 3
            print(f"- {job.job_title} at {job.company}, {job.location}")
            print()
        
        indeed_scraper.save_results(jobs)
    
    print("Job Scraper modules loaded successfully!")
    print("Usage:")
    print("  scraper = JobScraper('linkedin')")
    print("  jobs = scraper.discover_jobs('https://www.linkedin.com/jobs/search/')")
    print("  scraper.save_results(jobs)")
