#!/usr/bin/env python3
"""
Usage examples for the General Natural Language Scraper.
Demonstrates how to use the scraper with different websites and configurations.
"""

from general_scraper import NewsArticleScraper

def example_news_sites():
    """Example of scraping various news sites."""
    scraper = NewsArticleScraper(max_depth=2, delay_between_requests=1.0)
    
    # Example websites and their appropriate keywords
    examples = [
        {
            "url": "https://bbc.co.uk/news",
            "keywords": ["news", "breaking", "latest", "update", "report"],
            "description": "BBC News main page"
        },
        {
            "url": "https://bbc.co.uk/sport",
            "keywords": ["sport", "football", "cricket", "tennis", "match", "game"],
            "description": "BBC Sport main page"
        },
        {
            "url": "https://www.cnn.com",
            "keywords": ["news", "breaking", "politics", "world", "latest"],
            "description": "CNN News (if accessible)"
        },
        {
            "url": "https://www.reuters.com",
            "keywords": ["reuters", "news", "world", "business", "technology"],
            "description": "Reuters News (if accessible)"
        }
    ]
    
    for example in examples:
        print(f"\n{'='*60}")
        print(f"Example: {example['description']}")
        print(f"URL: {example['url']}")
        print(f"Keywords: {example['keywords']}")
        print(f"{'='*60}")
        
        try:
            results = scraper.scrape_news_site(example["url"], example["keywords"])
            
            if results["total_pages_scraped"] > 0:
                print(f"✅ Successfully scraped {results['total_pages_scraped']} pages")
                print(f"📊 Topics discovered: {results['summary']['unique_topics']}")
                print(f"🎯 Average relevance: {results['summary']['average_relevance']:.2f}")
            else:
                print("❌ No pages were successfully scraped")
                
        except Exception as e:
            print(f"❌ Error scraping {example['url']}: {e}")


def example_custom_scraping():
    """Example of custom scraping with specific configurations."""
    
    print("\n🔧 Custom Scraping Examples")
    print("="*60)
    
    # High-depth scraping for comprehensive coverage
    deep_scraper = NewsArticleScraper(max_depth=3, delay_between_requests=0.5)
    
    print("\n📊 Deep scraping example (max depth = 3):")
    results = deep_scraper.scrape_news_site(
        "https://bbc.co.uk/news/technology", 
        ["technology", "AI", "artificial intelligence", "tech", "digital"]
    )
    
    # Fast scraping for quick overview
    fast_scraper = NewsArticleScraper(max_depth=1, delay_between_requests=0.2)
    
    print("\n⚡ Fast scraping example (max depth = 1):")
    results = fast_scraper.scrape_news_site(
        "https://bbc.co.uk/news/health",
        ["health", "medical", "healthcare", "medicine", "NHS"]
    )


def example_topic_focused_scraping():
    """Example of topic-focused scraping."""
    
    scraper = NewsArticleScraper(max_depth=2, delay_between_requests=1.0)
    
    # Technology focused
    print("\n💻 Technology-focused scraping:")
    tech_results = scraper.scrape_news_site(
        "https://bbc.co.uk/news/technology",
        ["AI", "artificial intelligence", "machine learning", "technology", "robots", "automation"]
    )
    
    # Climate focused  
    print("\n🌍 Climate-focused scraping:")
    climate_results = scraper.scrape_news_site(
        "https://bbc.co.uk/news/science-environment",
        ["climate", "environment", "global warming", "carbon", "renewable", "sustainability"]
    )
    
    # Business focused
    print("\n💼 Business-focused scraping:")
    business_results = scraper.scrape_news_site(
        "https://bbc.co.uk/news/business",
        ["business", "economy", "finance", "markets", "investment", "trade"]
    )


def example_results_analysis():
    """Example of analyzing scraping results."""
    
    scraper = NewsArticleScraper(max_depth=2, delay_between_requests=1.0)
    
    results = scraper.scrape_news_site(
        "https://bbc.co.uk/news",
        ["news", "breaking", "latest", "update"]
    )
    
    print("\n📊 Results Analysis:")
    print(f"Total pages scraped: {results['total_pages_scraped']}")
    
    if results.get('summary'):
        summary = results['summary']
        print(f"Average relevance score: {summary['average_relevance']:.2f}/10.0")
        print(f"Unique topics found: {summary['unique_topics']}")
        print(f"High-relevance pages (>6.0): {summary['high_relevance_pages']}")
        print(f"Depth distribution: {summary['depth_distribution']}")
    
    print(f"\nFirst 3 knowledge nodes:")
    for i, node in enumerate(results['knowledge_nodes'][:3]):
        print(f"{i+1}. {node['title']}")
        print(f"   URL: {node['url']}")
        print(f"   Score: {node['relevance_score']:.2f}")
        print(f"   Topics: {len(node['topics'])} found")
        print(f"   Content preview: {node['content_preview'][:100]}...")
        print()


if __name__ == "__main__":
    print("🚀 General Natural Language Scraper - Usage Examples")
    print("="*60)
    
    # Uncomment the examples you want to run:
    
    # Example 1: Basic news site scraping
    example_news_sites()
    
    # Example 2: Custom configurations
    # example_custom_scraping()
    
    # Example 3: Topic-focused scraping
    # example_topic_focused_scraping()
    
    # Example 4: Results analysis
    # example_results_analysis()
    
    print("\n✅ Examples completed!")
    print("\n📝 Note: The scraper integrates with Marina's corpus system.")
    print("   Scraped content is automatically added to Marina's knowledge base")
    print("   and can be used to improve response quality.")
