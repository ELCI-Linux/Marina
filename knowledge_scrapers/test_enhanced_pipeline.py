#!/usr/bin/env python3
"""
Test Enhanced Scraping Pipeline
Demonstrates the complete workflow: Scrape → 4-Engine Analysis → LLM Revision
"""

import asyncio
import sys
import os

# Add Marina paths
sys.path.append('/home/adminx/Marina')
sys.path.append('/home/adminx/Marina/knowledge_scrapers')

from enhanced_scraping_pipeline import EnhancedScrapingPipeline

async def test_enhanced_pipeline():
    """Test the enhanced scraping pipeline with a sample website"""
    
    print("🧪 Testing Enhanced Scraping Pipeline")
    print("="*60)
    
    # Create pipeline with test configuration
    config = {
        "scraping": {
            "max_depth": 1,  # Keep it light for testing
            "delay_between_requests": 0.5,
            "quality_threshold": 3.0  # Lower threshold for testing
        },
        "analysis": {
            "saveless_mode": True,
            "enable_asymmetry_detection": True,
            "token_optimization": True,
            "pattern_analysis": True
        },
        "llm_training": {
            "auto_retrain": False,  # Disable for initial test
            "improvement_threshold": 0.05,
            "max_training_time": 1800,  # 30 minutes
            "base_model": "microsoft/DialoGPT-small"
        }
    }
    
    pipeline = EnhancedScrapingPipeline(config)
    
    # Test URLs (choose based on what's accessible)
    test_urls = [
        "https://example.com",  # Simple test site
        "https://httpbin.org/html",  # Another simple test
        "https://quotes.toscrape.com"  # Scraping-friendly test site
    ]
    
    for url in test_urls:
        print(f"\n🎯 Testing with URL: {url}")
        try:
            results = await pipeline.process_scraped_data(
                root_url=url,
                keywords=["test", "example", "demo"]
            )
            
            if results.get("scraping_results"):
                scraping = results["scraping_results"]
                print(f"   ✅ Scraping: {scraping.get('total_pages_scraped', 0)} pages")
                
            if results.get("analysis_results"):
                analysis = results["analysis_results"]
                print(f"   ✅ Analysis: Quality score {analysis.quality_score:.2f}")
                
            if results.get("pipeline_summary"):
                summary = results["pipeline_summary"]
                print(f"   ✅ Pipeline: {summary['execution_time']:.2f}s total")
                
            # Test successful, we can stop here
            return results
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue
    
    print("\n⚠️  All test URLs failed. This might be due to network issues or missing dependencies.")
    return None

def test_engine_availability():
    """Test which analysis engines are available"""
    print("\n🔍 Testing Analysis Engine Availability")
    print("-" * 40)
    
    try:
        from enhanced_scraping_pipeline import (
            SAVELESS_AVAILABLE, ASYMMETRY_AVAILABLE, 
            TOKEN_MIN_AVAILABLE, PATTERN_ANALYSIS_AVAILABLE,
            LLM_TRAINING_AVAILABLE
        )
        
        engines = {
            "Saveless Ingest": SAVELESS_AVAILABLE,
            "Knowledge Asymmetry": ASYMMETRY_AVAILABLE,
            "Token Minimization": TOKEN_MIN_AVAILABLE,
            "Pattern Analysis": PATTERN_ANALYSIS_AVAILABLE,
            "LLM Training": LLM_TRAINING_AVAILABLE
        }
        
        for name, available in engines.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"   {name}: {status}")
            
        available_count = sum(engines.values())
        print(f"\nTotal: {available_count}/5 engines available")
        
        if available_count >= 2:
            print("✅ Sufficient engines for testing")
        else:
            print("⚠️  Limited engine availability - some features may not work")
            
    except Exception as e:
        print(f"❌ Engine availability test failed: {e}")

def main():
    """Main test runner"""
    print("🚀 Enhanced Scraping Pipeline Test Suite")
    print("=" * 60)
    
    # Test 1: Engine availability
    test_engine_availability()
    
    # Test 2: Full pipeline test
    print("\n" + "=" * 60)
    results = asyncio.run(test_enhanced_pipeline())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    if results:
        print("✅ Enhanced scraping pipeline test completed successfully!")
        print("   The integration is working and ready for use.")
        print("\n🎯 Next steps:")
        print("   1. Run: python marina_cli.py scrape enhanced <url>")
        print("   2. Test with real websites like BBC News")
        print("   3. Enable LLM retraining for full pipeline")
    else:
        print("❌ Pipeline test failed - check network connectivity and dependencies")
        print("   You can still use the basic scraper: python marina_cli.py scrape general <url>")

if __name__ == "__main__":
    main()
