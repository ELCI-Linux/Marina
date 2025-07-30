#!/usr/bin/env python3
"""
Enhanced Scraper Registry and Manager

This module provides a centralized registry and management system for all Marina scrapers,
now supporting multiple languages: Python, JavaScript (Node.js), Go, and Rust.

Features include:
- Multi-language scraper support (Python, JavaScript, Go, Rust)
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
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Ensure Marina root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the pre and post scrape engines
try:
    from knowledge_scrapers.pre_scrape_engine import PreScrapeEngine
    from knowledge_scrapers.scrape_engines import PreScrapeEngine as AltPreScrapeEngine, PostScrapeEngine
    PRE_SCRAPE_AVAILABLE = True
except ImportError:
    PRE_SCRAPE_AVAILABLE = False
    logger.warning("Pre/Post scrape engines not available")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScraperInfo:
    """Information about a registered scraper"""
    name: str
    description: str
    supported_platforms: List[str]
    example_usage: str
    is_active: bool = True
    # Type can be 'python', 'javascript', 'go', or 'rust'
    scraper_type: str = 'python'
    # For Python scrapers
    module_path: Optional[str] = None
    scraper_class: Optional[str] = None
    # For external executable scrapers
    executable_path: Optional[str] = None

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

class ExternalScraperWrapper:
    """Wrapper for external scraper executables (JavaScript, Go, Rust)"""
    
    def __init__(self, scraper_info: ScraperInfo, base_directory: str):
        self.scraper_info = scraper_info
        self.base_directory = base_directory
        self.executable_path = os.path.join(base_directory, scraper_info.executable_path)
    
    def run_external(self, *args) -> List[Any]:
        """Execute the external scraper and return parsed results"""
        try:
            # Build command based on scraper type
            if self.scraper_info.scraper_type == 'javascript':
                cmd = ['node', self.executable_path] + [str(arg) for arg in args]
            elif self.scraper_info.scraper_type in ['go', 'rust']:
                cmd = [self.executable_path] + [str(arg) for arg in args]
            else:
                raise ValueError(f"Unsupported scraper type: {self.scraper_info.scraper_type}")
            
            logger.info(f"🚀 Executing external scraper: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                cwd=self.base_directory,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"❌ External scraper failed: {result.stderr}")
                return []
            
            # Try to parse the output as JSON
            output_lines = result.stdout.strip().split('\n')
            
            # Look for JSON output or results file
            results = []
            for line in output_lines:
                if line.startswith('{') or line.startswith('['):
                    try:
                        data = json.loads(line)
                        if isinstance(data, list):
                            results.extend(data)
                        else:
                            results.append(data)
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON in stdout, check for results file
            if not results:
                results_dir = os.path.join(self.base_directory, 'scraping_results')
                if os.path.exists(results_dir):
                    # Find the most recent results file
                    result_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
                    if result_files:
                        latest_file = max(result_files, key=lambda f: os.path.getctime(os.path.join(results_dir, f)))
                        try:
                            with open(os.path.join(results_dir, latest_file), 'r') as f:
                                data = json.load(f)
                                if isinstance(data, dict):
                                    # Extract data based on scraper type
                                    if 'pages' in data:
                                        results = data['pages']
                                    elif 'posts' in data:
                                        results = data['posts']
                                    elif 'products' in data:
                                        results = data['products']
                                    elif 'threads' in data:
                                        results = data['threads']
                                    else:
                                        results = [data]
                                elif isinstance(data, list):
                                    results = data
                                else:
                                    results = [data]
                        except Exception as e:
                            logger.warning(f"⚠️ Could not parse results file: {e}")
            
            logger.info(f"✅ External scraper completed: {len(results)} items")
            return results
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ External scraper timed out after 10 minutes")
            return []
        except Exception as e:
            logger.error(f"❌ Error executing external scraper: {e}")
            return []
    
    def save_results(self, results):
        """External scrapers handle their own result saving"""
        pass

class ScraperRegistry:
    """
    Enhanced central registry for managing all Marina scrapers
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
                'type': 'javascript',
                'executable_path': 'ecommerce_scraper.js',
                'description': 'Extract product information from e-commerce websites using Puppeteer',
                'supported_platforms': ['shopify', 'woocommerce', 'magento', 'generic'],
                'example_usage': 'node ecommerce_scraper.js shopify https://store.example.com 20'
            },
            {
                'name': 'social_media',
                'type': 'javascript',
                'executable_path': 'social_media_scraper.js',
                'description': 'Extract posts and content from social media platforms using Puppeteer',
                'supported_platforms': ['twitter', 'reddit', 'facebook', 'instagram'],
                'example_usage': 'node social_media_scraper.js twitter https://twitter.com/user 25'
            },
            {
                'name': 'forum',
                'type': 'go',
                'executable_path': 'forum_scraper',
                'description': 'Extract discussions and posts from forum platforms with high concurrency',
                'supported_platforms': ['phpbb', 'vbulletin', 'discourse', 'reddit', 'generic'],
                'example_usage': './forum_scraper phpbb https://forum.example.com 10 25'
            },
            {
                'name': 'documentation',
                'type': 'rust',
                'executable_path': 'target/release/documentation_scraper',
                'description': 'Extract technical documentation and API references with high performance',
                'supported_platforms': ['gitbook', 'readthedocs', 'swagger', 'sphinx', 'generic'],
                'example_usage': './documentation_scraper readthedocs https://docs.python.org/ 30'
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
                # Determine scraper type
                scraper_type = scraper_def.get('type', 'python')
                
                scraper_info = ScraperInfo(
                    name=scraper_def['name'],
                    description=scraper_def['description'],
                    supported_platforms=scraper_def['supported_platforms'],
                    example_usage=scraper_def['example_usage'],
                    scraper_type=scraper_type,
                    module_path=scraper_def.get('module_path'),
                    scraper_class=scraper_def.get('scraper_class'),
                    executable_path=scraper_def.get('executable_path')
                )
                
                # Verify scraper availability based on type
                is_available = self._verify_scraper_availability(scraper_info)
                scraper_info.is_active = is_available
                
                self.registered_scrapers[scraper_info.name] = scraper_info
                
                status = "✅" if is_available else "⚠️"
                logger.info(f"{status} Registered {scraper_type} scraper: {scraper_info.name}")
                    
            except Exception as e:
                logger.error(f"❌ Error registering scraper {scraper_def['name']}: {e}")
        
        logger.info(f"📊 Total scrapers registered: {len(self.registered_scrapers)}")
        active_count = sum(1 for s in self.registered_scrapers.values() if s.is_active)
        logger.info(f"📊 Active scrapers: {active_count}")
    
    def _verify_scraper_availability(self, scraper_info: ScraperInfo) -> bool:
        """Verify if a scraper is available based on its type"""
        try:
            if scraper_info.scraper_type == 'python':
                # Try to import the Python module
                if scraper_info.module_path:
                    importlib.import_module(scraper_info.module_path)
                    return True
                return False
                
            elif scraper_info.scraper_type in ['javascript', 'go', 'rust']:
                # Check if executable exists
                if scraper_info.executable_path:
                    executable_full_path = os.path.join(self.scrapers_directory, scraper_info.executable_path)
                    
                    if scraper_info.scraper_type == 'javascript':
                        # Check if Node.js is available and file exists
                        node_available = subprocess.run(['which', 'node'], capture_output=True).returncode == 0
                        file_exists = os.path.exists(executable_full_path)
                        return node_available and file_exists
                        
                    elif scraper_info.scraper_type == 'go':
                        # Check if Go binary exists
                        return os.path.exists(executable_full_path) and os.access(executable_full_path, os.X_OK)
                        
                    elif scraper_info.scraper_type == 'rust':
                        # Check if Rust binary exists
                        return os.path.exists(executable_full_path) and os.access(executable_full_path, os.X_OK)
                        
                return False
                
        except Exception as e:
            logger.debug(f"Error verifying {scraper_info.name}: {e}")
            return False
    
    def list_scrapers(self) -> Dict[str, ScraperInfo]:
        """List all registered scrapers"""
        return self.registered_scrapers.copy()
    
    def get_scraper_info(self, scraper_name: str) -> Optional[ScraperInfo]:
        """Get information about a specific scraper"""
        return self.registered_scrapers.get(scraper_name)
    
    def create_scraper_instance(self, scraper_name: str, platform: str = None, **kwargs):
        """Create an instance of the specified scraper or return command executor wrapper"""
        scraper_info = self.registered_scrapers.get(scraper_name)
        
        if not scraper_info:
            raise ValueError(f"Scraper '{scraper_name}' not found in registry")
        
        if not scraper_info.is_active:
            raise ValueError(f"Scraper '{scraper_name}' is not active")
        
        # For external executable scrapers, return a command executor wrapper
        if scraper_info.scraper_type in ['javascript', 'go', 'rust']:
            return ExternalScraperWrapper(scraper_info, self.scrapers_directory)
        
        # For Python scrapers, use the original logic
        try:
            # Import the module
            module = importlib.import_module(scraper_info.module_path)
            
            # Get the scraper class
            scraper_class = getattr(module, scraper_info.scraper_class)
            
            # Filter kwargs to only include constructor parameters
            init_kwargs = {}
            if scraper_name in ['academic', 'job', 'real_estate']:
                # These scrapers take platform as first argument and delay_between_requests
                if not platform:
                    platform = scraper_info.supported_platforms[0]  # Use first as default
                if 'delay_between_requests' in kwargs:
                    init_kwargs['delay_between_requests'] = kwargs['delay_between_requests']
                return scraper_class(platform, **init_kwargs)
            
            elif scraper_name in ['general']:
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
        """Execute a single scraping job with pre/post processing"""
        logger.info(f"🚀 Starting scraping job: {job.scraper_name} on {job.platform}")
        
        start_time = time.time()
        pre_scrape_analysis = None
        scraping_strategy = None
        
        # Pre-scrape analysis if available
        if PRE_SCRAPE_AVAILABLE and job.target_url:
            try:
                logger.info(f"🔍 Running pre-scrape analysis for {job.target_url}")
                pre_engine = PreScrapeEngine()
                
                # Quick assessment for immediate insights
                quick_assessment = pre_engine.quick_assessment(job.target_url)
                
                # Full analysis for optimal strategy
                scraping_goals = {
                    'max_pages': job.parameters.get('max_pages', 50),
                    'content_type': job.scraper_name,
                    'expected_volume': 'medium'
                }
                
                characteristics, strategy = pre_engine.analyze_and_optimize(
                    job.target_url, 
                    scraping_goals
                )
                
                pre_scrape_analysis = characteristics
                scraping_strategy = strategy
                
                # Update job parameters based on strategy
                if strategy.scraper_config.get('delay_between_requests'):
                    job.parameters['delay_between_requests'] = strategy.scraper_config['delay_between_requests']
                
                logger.info(f"📊 Pre-scrape analysis: Risk {characteristics.risk_score:.1f}/10, "
                          f"Recommended scraper: {strategy.recommended_scraper}, "
                          f"Delay: {characteristics.recommended_delay:.1f}s")
                
            except Exception as e:
                logger.warning(f"⚠️ Pre-scrape analysis failed: {e}")
        
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
                # External JavaScript scraper
                if hasattr(scraper, 'run_external'):
                    results = scraper.run_external(
                        job.platform or 'generic',
                        job.target_url,
                        job.parameters.get('max_pages', 10)
                    )
                else:
                    results = scraper.start_scraping(job.parameters.get('max_pages', 10))
                
            elif job.scraper_name == 'social_media':
                # External JavaScript scraper
                if hasattr(scraper, 'run_external'):
                    results = scraper.run_external(
                        job.platform or 'generic',
                        job.target_url,
                        job.parameters.get('max_posts', 10)
                    )
                else:
                    results = scraper.scrape_feed(job.target_url, job.parameters.get('max_posts', 10))
                
            elif job.scraper_name == 'forum':
                # External Go scraper
                if hasattr(scraper, 'run_external'):
                    results = scraper.run_external(
                        job.platform or 'generic',
                        job.target_url,
                        job.parameters.get('max_threads', 10),
                        job.parameters.get('max_posts_per_thread', 25)
                    )
                else:
                    results = scraper.scrape_forum(job.target_url, 
                                                 job.parameters.get('max_threads', 10),
                                                 job.parameters.get('max_posts_per_thread', 25))
                
            elif job.scraper_name == 'documentation':
                # External Rust scraper
                if hasattr(scraper, 'run_external'):
                    results = scraper.run_external(
                        job.platform or 'generic',
                        job.target_url,
                        job.parameters.get('max_pages', 30)
                    )
                else:
                    results = scraper.scrape_documentation_site(job.target_url, 
                                                              job.parameters.get('max_pages', 30))
                
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
                
            else:
                # Generic approach - try common methods
                if hasattr(scraper, 'scrape_comprehensive_knowledge'):
                    results = scraper.scrape_comprehensive_knowledge()
                elif hasattr(scraper, 'scrape_news_site'):
                    results = scraper.scrape_news_site(job.target_url, 
                                                     job.parameters.get('keywords', []))
                else:
                    raise ValueError(f"Don't know how to run scraper: {job.scraper_name}")
            
            # Post-scrape processing if available
            processed_results = results
            post_scrape_analysis = None
            
            if PRE_SCRAPE_AVAILABLE and results:
                try:
                    logger.info(f"🔧 Running post-scrape processing...")
                    post_engine = PostScrapeEngine()
                    
                    # Add result validators
                    post_engine.add_validator(lambda x: len(x) > 0 if isinstance(x, list) else bool(x))
                    
                    # Add result processors for deduplication and cleaning
                    def deduplicate_results(data):
                        if isinstance(data, list):
                            seen = set()
                            unique_results = []
                            for item in data:
                                item_key = str(item.get('url', '')) + str(item.get('title', ''))
                                if item_key not in seen:
                                    seen.add(item_key)
                                    unique_results.append(item)
                            return unique_results
                        return data
                    
                    post_engine.add_processor(deduplicate_results)
                    
                    # Add analyzers for quality metrics
                    def analyze_content_quality(data):
                        if isinstance(data, list):
                            total_items = len(data)
                            items_with_content = sum(1 for item in data if item.get('content', '').strip())
                            content_quality = items_with_content / total_items if total_items > 0 else 0
                            
                            avg_content_length = 0
                            if items_with_content > 0:
                                total_length = sum(len(str(item.get('content', ''))) for item in data)
                                avg_content_length = total_length / items_with_content
                            
                            return {
                                'content_quality_score': content_quality,
                                'average_content_length': avg_content_length,
                                'total_items': total_items,
                                'items_with_content': items_with_content
                            }
                        return {}
                    
                    post_engine.add_analyzer(analyze_content_quality)
                    
                    # Execute post-processing pipeline
                    pipeline_result = post_engine.execute_pipeline(results)
                    processed_results = pipeline_result.get('processed_results', results)
                    post_scrape_analysis = pipeline_result.get('analysis', {})
                    
                    logger.info(f"✅ Post-scrape processing complete: "
                              f"Quality score: {post_scrape_analysis.get('content_quality_score', 0):.2f}, "
                              f"Items processed: {post_scrape_analysis.get('total_items', 0)}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Post-scrape processing failed: {e}")
                    processed_results = results
            
            # Save processed results
            if processed_results and hasattr(scraper, 'save_results'):
                scraper.save_results(processed_results)
            
            execution_time = time.time() - start_time
            
            result_dict = {
                'status': 'success',
                'scraper_name': job.scraper_name,
                'platform': job.platform,
                'target_url': job.target_url,
                'results_count': len(processed_results) if processed_results else 0,
                'execution_time': execution_time,
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add analysis data if available
            if pre_scrape_analysis:
                result_dict['pre_scrape_analysis'] = {
                    'risk_score': pre_scrape_analysis.risk_score,
                    'recommended_delay': pre_scrape_analysis.recommended_delay,
                    'anti_bot_measures': pre_scrape_analysis.anti_bot_measures,
                    'estimated_pages': pre_scrape_analysis.estimated_pages
                }
            
            if scraping_strategy:
                result_dict['scraping_strategy'] = {
                    'recommended_scraper': scraping_strategy.recommended_scraper,
                    'estimated_duration': scraping_strategy.estimated_duration,
                    'success_probability': scraping_strategy.risk_assessment.get('success_probability', 0)
                }
            
            if post_scrape_analysis:
                result_dict['post_scrape_analysis'] = post_scrape_analysis
            
            return result_dict
            
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
        
        # Group by scraper type
        scrapers_by_type = {}
        for scraper_name, scraper_info in self.registered_scrapers.items():
            scraper_type = scraper_info.scraper_type
            if scraper_type not in scrapers_by_type:
                scrapers_by_type[scraper_type] = []
            scrapers_by_type[scraper_type].append((scraper_name, scraper_info))
        
        for scraper_type in ['python', 'javascript', 'go', 'rust']:
            if scraper_type in scrapers_by_type:
                type_icon = {
                    'python': '🐍',
                    'javascript': '🟨',
                    'go': '🔵',
                    'rust': '🦀'
                }[scraper_type]
                
                print(f"\n{type_icon} {scraper_type.upper()} SCRAPERS:")
                print("-" * 40)
                
                for scraper_name, scraper_info in scrapers_by_type[scraper_type]:
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
            scraper_name='forum',
            platform='generic',
            target_url='https://forum.example.com/',
            parameters={'max_threads': 5, 'max_posts_per_thread': 10},
            priority=3
        )
    ]

if __name__ == '__main__':
    # Initialize the enhanced scraper registry
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
    print("🎉 Enhanced Scraper Registry Demo Complete!")
    print("="*80)
