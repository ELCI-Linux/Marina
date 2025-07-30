# Marina CLI Scraper Usage Examples

This document provides comprehensive examples of using Marina's integrated knowledge scraping system through the command line interface.

## 🚀 Quick Start

### List Available Scrapers
```bash
python3 marina_cli.py scrape list
```

### Check Scraper Status
```bash
python3 marina_cli.py scrape status
```

## 🎯 Quick Scraping Commands

### Academic Paper Search
```bash
# Search arXiv for machine learning papers
python3 marina_cli.py scrape quick academic "machine learning" --papers 5

# Search PubMed for medical research
python3 marina_cli.py scrape quick academic "covid-19" --papers 10 --source pubmed
```

### Job Listings
```bash
# Search Indeed for Python developer jobs
python3 marina_cli.py scrape quick jobs "python developer" --jobs 15

# Search LinkedIn for data scientist positions
python3 marina_cli.py scrape quick jobs "data scientist" --jobs 10 --site linkedin
```

### Documentation Scraping
```bash
# Scrape Python documentation
python3 marina_cli.py scrape quick docs "https://docs.python.org/" --pages 20

# Scrape a GitBook documentation site
python3 marina_cli.py scrape quick docs "https://docs.gitbook.com/" --platform gitbook --pages 15
```

## 🔧 Advanced Single Scraper Usage

### Academic Scraper
```bash
# Run academic scraper with custom parameters
python3 marina_cli.py scrape run academic \
  --platform arxiv \
  --query "artificial intelligence" \
  --max-items 20 \
  --delay 2.0
```

### Social Media Scraper
```bash
# Scrape Twitter-like content
python3 marina_cli.py scrape run social_media \
  --platform twitter \
  --url "https://twitter.com/user/feed" \
  --max-items 25 \
  --delay 3.0
```

### Forum Scraper
```bash
# Scrape phpBB forum discussions
python3 marina_cli.py scrape run forum \
  --platform phpbb \
  --url "https://forum.example.com/" \
  --max-items 10 \
  --delay 2.0
```

### E-commerce Scraper
```bash
# Scrape product listings
python3 marina_cli.py scrape run ecommerce \
  --url "https://store.example.com/" \
  --max-items 50 \
  --delay 1.5
```

### Real Estate Scraper
```bash
# Scrape property listings from Zillow-like sites
python3 marina_cli.py scrape run real_estate \
  --platform zillow \
  --url "https://zillow.com/search/" \
  --max-items 30 \
  --delay 2.5
```

## 🎬 Campaign Examples

### Demo Campaign
```bash
# Run a demo campaign with sample jobs
python3 marina_cli.py scrape campaign demo_campaign --demo
```

### Custom Campaign with Configuration
```bash
# Create a config file: campaign_config.json
cat > campaign_config.json << EOF
{
  "jobs": [
    {
      "scraper": "academic",
      "platform": "arxiv",
      "url": "",
      "parameters": {
        "search_query": "quantum computing",
        "max_papers": 10,
        "delay_between_requests": 2.0
      },
      "priority": 1
    },
    {
      "scraper": "documentation",
      "platform": "readthedocs",
      "url": "https://pytorch.org/docs/",
      "parameters": {
        "max_pages": 25,
        "delay_between_requests": 1.0
      },
      "priority": 2
    },
    {
      "scraper": "job",
      "platform": "indeed",
      "url": "https://indeed.com/jobs?q=machine+learning",
      "parameters": {
        "max_jobs": 15,
        "delay_between_requests": 1.5
      },
      "priority": 3
    }
  ]
}
EOF

# Run the campaign
python3 marina_cli.py scrape campaign research_campaign \
  --config campaign_config.json \
  --workers 3
```

### Multi-Domain Research Campaign
```bash
# Large-scale research campaign
python3 marina_cli.py scrape campaign comprehensive_research \
  --config research_config.json \
  --workers 5
```

## 📊 Specialized Use Cases

### Academic Research Workflow
```bash
# Step 1: Search for papers
python3 marina_cli.py scrape quick academic "deep learning" --papers 20 --source arxiv

# Step 2: Scrape related documentation
python3 marina_cli.py scrape quick docs "https://pytorch.org/docs/" --platform generic --pages 30

# Step 3: Find relevant job opportunities
python3 marina_cli.py scrape quick jobs "deep learning engineer" --jobs 10 --site linkedin
```

### Market Research Workflow
```bash
# Step 1: Scrape real estate listings
python3 marina_cli.py scrape run real_estate \
  --platform zillow \
  --url "https://zillow.com/san-francisco/" \
  --max-items 100

# Step 2: Scrape job market
python3 marina_cli.py scrape quick jobs "real estate agent" --jobs 50

# Step 3: Scrape forum discussions
python3 marina_cli.py scrape run forum \
  --platform reddit \
  --url "https://reddit.com/r/realestate/" \
  --max-items 20
```

### Technical Documentation Aggregation
```bash
# Create a comprehensive documentation campaign
cat > docs_campaign.json << EOF
{
  "jobs": [
    {
      "scraper": "documentation",
      "platform": "readthedocs",
      "url": "https://docs.python.org/",
      "parameters": {"max_pages": 50},
      "priority": 1
    },
    {
      "scraper": "documentation", 
      "platform": "gitbook",
      "url": "https://docs.docker.com/",
      "parameters": {"max_pages": 40},
      "priority": 2
    },
    {
      "scraper": "documentation",
      "platform": "sphinx",
      "url": "https://pytorch.org/docs/",
      "parameters": {"max_pages": 60},
      "priority": 3
    }
  ]
}
EOF

python3 marina_cli.py scrape campaign tech_docs --config docs_campaign.json
```

## 🛠️ Advanced Configuration

### Custom Delay and Rate Limiting
```bash
# High-traffic site with conservative scraping
python3 marina_cli.py scrape run general \
  --url "https://high-traffic-site.com/" \
  --delay 5.0 \
  --max-items 20
```

### Platform-Specific Configurations
```bash
# Configure for specific forum platform
python3 marina_cli.py scrape run forum \
  --platform discourse \
  --url "https://discourse.example.com/" \
  --max-items 15

# Configure for specific documentation platform  
python3 marina_cli.py scrape run documentation \
  --platform swagger \
  --url "https://api.example.com/docs/" \
  --max-items 25
```

## 📈 Monitoring and Results

### Check Results Directory
```bash
ls -la /home/adminx/Marina/knowledge_scrapers/scraping_results/
```

### View Campaign Summary
```bash
# Campaign results are automatically saved as JSON
cat /home/adminx/Marina/knowledge_scrapers/scraping_results/campaign_*.json | jq .
```

### Analyze Scraped Data
```bash
# Count total items scraped today
find /home/adminx/Marina/knowledge_scrapers/scraping_results/ -name "*$(date +%Y%m%d)*" -exec jq '.total_papers // .total_jobs // .total_properties // .total_posts // .total_pages // length' {} \; | awk '{sum+=$1} END{print "Total items:", sum}'
```

## 🚨 Error Handling

### Debug Failed Scraping
```bash
# Run with verbose logging (check logs for detailed error info)
python3 marina_cli.py scrape run academic --platform arxiv --query "test" --max-items 1
```

### Retry Failed Jobs
```bash
# Re-run individual scrapers that failed in a campaign
python3 marina_cli.py scrape run [scraper_name] --platform [platform] --url [url]
```

## 💡 Best Practices

1. **Start Small**: Begin with `--max-items 5` to test scrapers
2. **Respect Rate Limits**: Use appropriate `--delay` values (1.5-3.0 seconds)
3. **Use Campaigns**: For multiple related scraping tasks
4. **Monitor Results**: Check the results directory regularly
5. **Platform Selection**: Choose the most appropriate platform for each scraper

## 🔗 Integration with Marina

The scraped data automatically integrates with Marina's knowledge base:

```bash
# After scraping, you can query Marina about the collected data
python3 marina_cli.py llm "What did you learn from the recent academic papers about machine learning?"

# Use Marina's context system to incorporate scraped data
python3 marina_cli.py context --mode complete
```

## 📚 Further Reading

- Check `scraper_registry.py` for programmatic usage
- See individual scraper files for platform-specific details
- Review `README.md` for system architecture information
