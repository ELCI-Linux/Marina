#!/usr/bin/env python3
"""
Scraper Registry and Manager

This module provides a centralized registry and management system for all Marina scrapers.
Features include:
- Automatic scraper discovery and registration
- Unified interface for running multiple scrapers
- Progress tracking and logging
- Result aggregation and analysis
- Scheduling and automation support
"""

import os
import sys
import json
import time
import importlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScraperInfo:
    """Information about a registered scraper"""
    name: str
    module_path: str
    scraper_class: str
    description: str
    supported_platforms: List[str]
    example_usage: str
    is_active: bool = True

@dataclass
class ScrapingJob:
    """Represents a scraping job to be executed"""
    scraper_name: str
    platform: str
    target_url: str
    parameters: Dict[str, Any]
    priority: int = 1  # 1 = highest, 5 = lowest
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class ScraperRegistry:
    """
    Central registry for managing all Marina scrapers
    """
    
    def __init__(self, scrapers_directory: str = None):
        self.scrapers_directory = scrapers_directory or "/home/adminx/Marina/knowledge_scrapers"
        self.registered_scrapers: Dict[str, ScraperInfo] = {}
        self.results_directory = os.path.join(self.scrapers_directory, "scraping_results")
        
        # Ensure results directory exists
        os.makedirs(self.results_directory, exist_ok=True)
        
        # Auto-discover and register scrapers
        self.discover_scrapers()
    
    def discover_scrapers(self):
        """Automatically discover and register available scrapers"""
        logger.info("🔍 Discovering available scrapers...")
        
        scraper_definitions = [
            {
                'name': 'ecommerce',
                'module_path': 'knowledge_scrapers.ecommerce_scraper',
                'scraper_class': 'EcommerceScraper',
                'description': 'Extract product information from e-commerce websites',
                'supported_platforms': ['generic'],
                'example_usage': 'scraper = EcommerceScraper("https://example-store.com")'
            },
            {
                'name': 'social_media',
                'module_path': 'knowledge_scrapers.social_media_scraper',
                'scraper_class': 'SocialMediaScraper',
                'description': 'Extract posts and content from social media platforms',
                'supported_platforms': ['twitter', 'reddit', 'facebook'],
                'example_usage': 'scraper = SocialMediaScraper("twitter")'
            },
            {
                'name': 'forum',
                'module_path': 'knowledge_scrapers.forum_scraper',
                'scraper_class': 'ForumScraper',
                'description': 'Extract discussions and posts from forum platforms',
                'supported_platforms': ['phpbb', 'vbulletin', 'discourse', 'reddit', 'generic'],
                'example_usage': 'scraper = ForumScraper("phpbb")'
            },
            {
                'name': 'academic',
                'module_path': 'knowledge_scrapers.academic_scraper',
                'scraper_class': 'AcademicScraper',
                'description': 'Extract academic papers and research content',
                'supported_platforms': ['arxiv', 'pubmed', 'ieee', 'acm', 'scholar'],
                'example_usage': 'scraper = AcademicScraper("arxiv")'
            },
            {
                'name': 'job',
                'module_path': 'knowledge_scrapers.job_scraper',
                'scraper_class': 'JobScraper',
                'description': 'Extract job listings from career websites',
                'supported_platforms': ['indeed', 'linkedin', 'glassdoor'],
                'example_usage': 'scraper = JobScraper("indeed")'
            },
            {
                'name': 'real_estate',
                'module_path': 'knowledge_scrapers.real_estate_scraper',
                'scraper_class': 'RealEstateScraper',
                'description': 'Extract property listings from real estate websites',
                'supported_platforms': ['zillow', 'realtor', 'trulia'],
                'example_usage': 'scraper = RealEstateScraper("zillow")'
            },
            {
                'name': 'documentation',
                'module_path': 'knowledge_scrapers.documentation_scraper',
                'scraper_class': 'DocumentationScraper',
                'description': 'Extract technical documentation and API references',
                'supported_platforms': ['gitbook', 'readthedocs', 'swagger', 'sphinx', 'generic'],
                'example_usage': 'scraper = DocumentationScraper("readthedocs")'
            },
            {
                'name': 'general',
                'module_path': 'knowledge_scrapers.general_scraper',
                'scraper_class': 'GeneralScraper',
                'description': 'General web scraper using rabbithole reasoning',
                'supported_platforms': ['generic'],
                'example_usage': 'scraper = GeneralScraper("https://example.com")'
            },
            {
                'name': 'archwiki_flatpak',
                'module_path': 'knowledge_scrapers.archwiki_flatpak_scraper',
                'scraper_class': 'ArchWikiFlatpakScraper',
                'description': 'Specialized scraper for ArchWiki Flatpak documentation',
                'supported_platforms': ['archwiki'],
                'example_usage': 'scraper = ArchWikiFlatpakScraper()'
            },
            {
                'name': 'sitemap',
                'module_path': 'knowledge_scrapers.sitemap_alphabetical_scraper',
                'scraper_class': 'AlphabeticalSitemapScraper',
                'description': 'Scrape websites systematically using sitemaps',
                'supported_platforms': ['generic'],
                'example_usage': 'scraper = AlphabeticalSitemapScraper()'
            }
        ]
        
        for scraper_def in scraper_definitions:
            try:
                scraper_info = ScraperInfo(
                    name=scraper_def['name'],
                    module_path=scraper_def['module_path'],
                    scraper_class=scraper_def['scraper_class'],
                    description=scraper_def['description'],
                    supported_platforms=scraper_def['supported_platforms'],
                    example_usage=scraper_def['example_usage']
                )
                
                # Try to import the module to verify it exists
                try:
                    importlib.import_module(scraper_info.module_path)
                    self.registered_scrapers[scraper_info.name] = scraper_info
                    logger.info(f"✅ Registered scraper: {scraper_info.name}")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import {scraper_info.name}: {e}")
                    scraper_info.is_active = False
                    self.registered_scrapers[scraper_info.name] = scraper_info
                    
            except Exception as e:
                logger.error(f"❌ Error registering scraper {scraper_def['name']}: {e}")
        
        logger.info(f"📊 Total scrapers registered: {len(self.registered_scrapers)}")
        active_count = sum(1 for s in self.registered_scrapers.values() if s.is_active)
        logger.info(f"📊 Active scrapers: {active_count}")
    
    def list_scrapers(self) -> Dict[str, ScraperInfo]:
        """List all registered scrapers"""
        return self.registered_scrapers.copy()
    
    def get_scraper_info(self, scraper_name: str) -> Optional[ScraperInfo]:
        """Get information about a specific scraper"""
        return self.registered_scrapers.get(scraper_name)
    
    def create_scraper_instance(self, scraper_name: str, platform: str = None, **kwargs):
        """Create an instance of the specified scraper"""
        scraper_info = self.registered_scrapers.get(scraper_name)
        
        if not scraper_info:
            raise ValueError(f"Scraper '{scraper_name}' not found in registry")
        
        if not scraper_info.is_active:
            raise ValueError(f"Scraper '{scraper_name}' is not active")
        
        try:
            # Import the module
            module = importlib.import_module(scraper_info.module_path)
            
            # Get the scraper class
            scraper_class = getattr(module, scraper_info.scraper_class)
            
            # Filter kwargs to only include constructor parameters
            init_kwargs = {}
            if scraper_name in ['social_media', 'forum', 'academic', 'job', 'real_estate', 'documentation']:
                # These scrapers take platform as first argument and delay_between_requests
                if not platform:
                    platform = scraper_info.supported_platforms[0]  # Use first as default
                if 'delay_between_requests' in kwargs:
                    init_kwargs['delay_between_requests'] = kwargs['delay_between_requests']
                return scraper_class(platform, **init_kwargs)
            
            elif scraper_name in ['ecommerce', 'general']:
                # These scrapers take root_url as first argument
                root_url = kwargs.pop('root_url', 'https://example.com')
                if 'delay_between_requests' in kwargs:
                    init_kwargs['delay_between_requests'] = kwargs['delay_between_requests']
                return scraper_class(root_url, **init_kwargs)
            
            else:
                # Default: try to create with filtered kwargs
                for param in ['delay_between_requests', 'max_depth', 'quality_threshold']:
                    if param in kwargs:
                        init_kwargs[param] = kwargs[param]
                return scraper_class(**init_kwargs)
                
        except Exception as e:
            logger.error(f"❌ Error creating scraper instance: {e}")
            raise
    
    def run_scraping_job(self, job: ScrapingJob) -> Dict[str, Any]:
        """Execute a single scraping job"""
        logger.info(f"🚀 Starting scraping job: {job.scraper_name} on {job.platform}")
        
        start_time = time.time()
        
        try:
            # Create scraper instance
            scraper = self.create_scraper_instance(
                job.scraper_name, 
                job.platform, 
                **job.parameters
            )
            
            # Execute scraping based on scraper type
            results = None
            
            if job.scraper_name == 'ecommerce':
                results = scraper.start_scraping(job.parameters.get('max_pages', 10))
                
            elif job.scraper_name == 'social_media':
                results = scraper.scrape_feed(job.target_url, job.parameters.get('max_posts', 10))
                
            elif job.scraper_name == 'forum':
                results = scraper.scrape_forum(job.target_url, 
                                             job.parameters.get('max_threads', 10),
                                             job.parameters.get('max_posts_per_thread', 25))
                
            elif job.scraper_name == 'academic':
                if 'search_query' in job.parameters:
                    results = scraper.search_papers(job.parameters['search_query'], 
                                                  job.parameters.get('max_papers', 20))
                else:
                    results = scraper.scrape_repository(job.target_url, 
                                                      job.parameters.get('max_papers', 20))
                
            elif job.scraper_name == 'job':
                results = scraper.discover_jobs(job.target_url, job.parameters.get('max_jobs', 10))
                
            elif job.scraper_name == 'real_estate':
                results = scraper.discover_properties(job.target_url, 
                                                    job.parameters.get('max_properties', 20))
                
            elif job.scraper_name == 'documentation':
                results = scraper.scrape_documentation_site(job.target_url, 
                                                          job.parameters.get('max_pages', 30))
                
            else:
                # Generic approach - try common methods
                if hasattr(scraper, 'scrape_comprehensive_knowledge'):
                    results = scraper.scrape_comprehensive_knowledge()
                elif hasattr(scraper, 'scrape_news_site'):
                    results = scraper.scrape_news_site(job.target_url, 
                                                     job.parameters.get('keywords', []))
                else:
                    raise ValueError(f"Don't know how to run scraper: {job.scraper_name}")
            
            # Save results
            if results and hasattr(scraper, 'save_results'):
                scraper.save_results(results)
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success',
                'scraper_name': job.scraper_name,
                'platform': job.platform,
                'target_url': job.target_url,
                'results_count': len(results) if results else 0,
                'execution_time': execution_time,
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Scraping job failed: {e}")
            
            return {
                'status': 'failed',
                'scraper_name': job.scraper_name,
                'platform': job.platform,
                'target_url': job.target_url,
                'error': str(e),
                'execution_time': execution_time,
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def run_multiple_jobs(self, jobs: List[ScrapingJob], max_workers: int = 3) -> List[Dict[str, Any]]:
        """Execute multiple scraping jobs concurrently"""
        logger.info(f"🔄 Running {len(jobs)} scraping jobs with {max_workers} workers")
        
        results = []
        
        # Sort jobs by priority
        sorted_jobs = sorted(jobs, key=lambda x: x.priority)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self.run_scraping_job, job): job 
                for job in sorted_jobs
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'success':
                        logger.info(f"✅ Completed job: {job.scraper_name} ({result['results_count']} items)")
                    else:
                        logger.error(f"❌ Failed job: {job.scraper_name} - {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Job execution error: {e}")
                    results.append({
                        'status': 'failed',
                        'scraper_name': job.scraper_name,
                        'error': str(e),
                        'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return results
    
    def create_scraping_campaign(self, campaign_name: str, jobs: List[ScrapingJob]) -> Dict[str, Any]:
        """Create and execute a coordinated scraping campaign"""
        logger.info(f"🎯 Starting scraping campaign: {campaign_name}")
        
        campaign_start = time.time()
        
        # Execute all jobs
        job_results = self.run_multiple_jobs(jobs)
        
        # Aggregate results
        successful_jobs = [r for r in job_results if r['status'] == 'success']
        failed_jobs = [r for r in job_results if r['status'] == 'failed']
        
        total_items = sum(r.get('results_count', 0) for r in successful_jobs)
        total_execution_time = time.time() - campaign_start
        
        campaign_summary = {
            'campaign_name': campaign_name,
            'total_jobs': len(jobs),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': len(failed_jobs),
            'total_items_scraped': total_items,
            'total_execution_time': total_execution_time,
            'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'job_results': job_results
        }
        
        # Save campaign summary
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_filename = f"campaign_{campaign_name}_{timestamp}.json"
        summary_path = os.path.join(self.results_directory, summary_filename)
        
        with open(summary_path, 'w') as f:
            json.dump(campaign_summary, f, indent=2)
        
        logger.info(f"✅ Campaign completed: {len(successful_jobs)}/{len(jobs)} jobs successful")
        logger.info(f"📊 Total items scraped: {total_items}")
        logger.info(f"💾 Campaign summary saved: {summary_path}")
        
        return campaign_summary
    
    def print_scraper_status(self):
        """Print a formatted status report of all scrapers"""
        print("\n" + "="*80)
        print("🕷️  Marina Knowledge Scrapers Registry Status")
        print("="*80)
        
        active_scrapers = [s for s in self.registered_scrapers.values() if s.is_active]
        inactive_scrapers = [s for s in self.registered_scrapers.values() if not s.is_active]
        
        print(f"📊 Total Scrapers: {len(self.registered_scrapers)}")
        print(f"✅ Active: {len(active_scrapers)}")
        print(f"❌ Inactive: {len(inactive_scrapers)}")
        print("\n" + "-"*80)
        
        for scraper_name, scraper_info in self.registered_scrapers.items():
            status_icon = "✅" if scraper_info.is_active else "❌"
            platforms = ", ".join(scraper_info.supported_platforms)
            
            print(f"{status_icon} {scraper_name.upper()}")
            print(f"   Description: {scraper_info.description}")
            print(f"   Platforms: {platforms}")
            print(f"   Usage: {scraper_info.example_usage}")
            print()
        
        print("="*80)

# Usage examples and convenience functions
def create_sample_jobs() -> List[ScrapingJob]:
    """Create sample scraping jobs for demonstration"""
    return [
        ScrapingJob(
            scraper_name='academic',
            platform='arxiv',
            target_url='',
            parameters={'search_query': 'machine learning', 'max_papers': 5},
            priority=1
        ),
        ScrapingJob(
            scraper_name='documentation',
            platform='readthedocs',
            target_url='https://docs.python.org/',
            parameters={'max_pages': 10},
            priority=2
        ),
        ScrapingJob(
            scraper_name='job',
            platform='indeed',
            target_url='https://www.indeed.com/jobs?q=python+developer',
            parameters={'max_jobs': 5},
            priority=3
        )
    ]

if __name__ == '__main__':
    # Initialize the scraper registry
    registry = ScraperRegistry()
    
    # Print status
    registry.print_scraper_status()
    
    # Example: Run a small scraping campaign
    print("\n🎯 Running sample scraping campaign...")
    
    sample_jobs = create_sample_jobs()
    campaign_results = registry.create_scraping_campaign("demo_campaign", sample_jobs)
    
    print(f"\n✅ Campaign completed successfully!")
    print(f"📊 Results summary: {campaign_results['successful_jobs']}/{campaign_results['total_jobs']} jobs successful")
    print(f"🕒 Total execution time: {campaign_results['total_execution_time']:.2f} seconds")
    
    print("\n" + "="*80)
    print("🎉 Scraper Registry Demo Complete!")
    print("="*80)
