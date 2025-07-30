# Marina Multi-Language Scraper Integration

Marina now supports **four programming languages** for specialized web scraping, each optimized for specific use cases:

## 🚀 Architecture Overview

| Language | Use Case | Scrapers | Key Benefits |
|----------|----------|----------|--------------|
| **🐍 Python** | API-based, Research | Academic, Job, Real Estate, General | Rich ecosystem, ML integration |
| **🟨 JavaScript** | Dynamic content, Anti-bot | E-commerce, Social Media | Puppeteer, Browser automation |
| **🔵 Go** | High concurrency | Forum Scraper | Excellent concurrency, Fast |
| **🦀 Rust** | High performance | Documentation Scraper | Memory safety, Speed |

## 📋 Available Scrapers

### JavaScript Scrapers (Node.js + Puppeteer)
- **E-commerce Scraper** (`ecommerce_scraper.js`)
  - Platforms: Shopify, WooCommerce, Magento, Generic
  - Features: Product details, pricing, availability
  - Anti-bot evasion with stealth plugin

- **Social Media Scraper** (`social_media_scraper.js`)
  - Platforms: Twitter, Reddit, Facebook, Instagram
  - Features: Posts, engagement metrics, user interactions
  - JavaScript rendering for dynamic content

### Go Scrapers (High Concurrency)
- **Forum Scraper** (`forum_scraper`)
  - Platforms: phpBB, vBulletin, Discourse, Reddit, Generic
  - Features: Concurrent thread/post extraction
  - Optimized for high-throughput scraping

### Rust Scrapers (High Performance)
- **Documentation Scraper** (`target/release/documentation_scraper`)
  - Platforms: GitBook, ReadTheDocs, Swagger, Sphinx, Generic
  - Features: API documentation, code examples
  - Concurrent processing with semaphore control

### Python Scrapers (Existing)
- **Academic Scraper** - arXiv, PubMed, IEEE, ACM, Scholar
- **Job Scraper** - Indeed, LinkedIn, Glassdoor
- **Real Estate Scraper** - Zillow, Realtor, Trulia
- **General Scraper** - Rabbithole reasoning
- **ArchWiki Flatpak Scraper** - Specialized knowledge extraction
- **Sitemap Scraper** - Systematic crawling

## 🛠️ Setup Instructions

### 1. JavaScript Scrapers (Node.js)
```bash
# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install dependencies in knowledge_scrapers directory
cd /home/adminx/Marina/knowledge_scrapers
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth
```

### 2. Go Scraper
```bash
# Build the forum scraper
cd /home/adminx/Marina/knowledge_scrapers
go build -o forum_scraper forum_scraper.go

# Make executable
chmod +x forum_scraper
```

### 3. Rust Scraper
```bash
# Build the documentation scraper
cd /home/adminx/Marina/knowledge_scrapers
cargo build --release

# Binary will be at: target/release/documentation_scraper
```

## 🎯 CLI Usage

### Check All Scrapers
```bash
# List all available scrapers with their types
python3 marina_cli.py scrape list

# Detailed status with runtime availability
python3 marina_cli.py scrape status
```

### Run Individual Scrapers

#### JavaScript E-commerce Scraper
```bash
python3 marina_cli.py scrape run ecommerce \
  --platform shopify \
  --url https://store.example.com \
  --max-items 20 \
  --delay 2.0
```

#### Go Forum Scraper
```bash
python3 marina_cli.py scrape run forum \
  --platform discourse \
  --url https://forum.example.com \
  --max-items 10 \
  --delay 1.5
```

#### Rust Documentation Scraper
```bash
python3 marina_cli.py scrape run documentation \
  --platform readthedocs \
  --url https://docs.python.org/ \
  --max-items 30 \
  --delay 1.0
```

### Quick Scraping Commands
```bash
# Quick documentation scraping (uses Rust scraper)
python3 marina_cli.py scrape quick docs https://pytorch.org/docs/ --pages 25

# Academic search (uses Python scraper)
python3 marina_cli.py scrape quick academic "machine learning" --papers 10

# Job search (uses Python scraper)
python3 marina_cli.py scrape quick jobs "python developer" --jobs 15
```

## 🎬 Campaign Mode

### Demo Campaign
```bash
# Run sample multi-language campaign
python3 marina_cli.py scrape campaign demo_campaign --demo
```

### Custom Multi-Language Campaign
Create a configuration file:
```json
{
  "description": "Multi-language scraper campaign",
  "jobs": [
    {
      "scraper": "documentation",
      "platform": "readthedocs", 
      "url": "https://docs.python.org/",
      "parameters": {"max_pages": 20},
      "priority": 1
    },
    {
      "scraper": "forum",
      "platform": "discourse",
      "url": "https://forum.example.com/",
      "parameters": {"max_threads": 10, "max_posts_per_thread": 25},
      "priority": 2
    },
    {
      "scraper": "ecommerce",
      "platform": "shopify",
      "url": "https://store.example.com/",
      "parameters": {"max_pages": 15},
      "priority": 3
    }
  ]
}
```

Run the campaign:
```bash
python3 marina_cli.py scrape campaign multi_lang_demo \
  --config multi_lang_config.json \
  --workers 3
```

## 🔧 Technical Implementation

### Enhanced Scraper Registry
The new `scraper_registry_v2.py` supports:
- **Multi-language scraper detection**
- **Runtime dependency checking** (Node.js, Go, Rust binaries)
- **External executable wrapper** for non-Python scrapers
- **Unified job execution interface**
- **Result parsing and aggregation**

### External Scraper Wrapper
- Executes external binaries with proper argument passing
- Handles JSON output parsing
- Manages timeouts and error handling
- Provides unified interface for all scraper types

### Fallback Mechanism
- Automatically falls back to standard registry if enhanced version unavailable
- Graceful degradation when external scrapers not built
- Clear status reporting for missing dependencies

## 📊 Performance Characteristics

| Scraper Type | Concurrency | Memory Usage | Speed | Best For |
|--------------|-------------|--------------|-------|----------|
| **JavaScript** | Medium | High | Medium | Dynamic content, Anti-bot |
| **Go** | Very High | Low | High | High-volume concurrent |
| **Rust** | High | Very Low | Very High | Performance-critical |
| **Python** | Low-Medium | Medium | Medium | Complex logic, APIs |

## 🧪 Testing

Run the comprehensive integration test:
```bash
python3 test_enhanced_scrapers.py
```

This will:
- Test scraper registry functionality
- Check availability of all scraper types
- Demonstrate scraper instantiation
- Show CLI usage examples
- Create sample configuration files

## 🔗 Integration with Marina

All scraped data automatically integrates with Marina's knowledge base:
- **Corpus Building**: Results added to neocorpus
- **Quality Scoring**: Content relevance assessment
- **LLM Training**: Improved response accuracy
- **Context System**: Enhanced Marina awareness

## 📈 Future Enhancements

- **WebAssembly (WASM)** scrapers for browser-based execution
- **Distributed scraping** across multiple machines
- **Real-time streaming** scrapers
- **Machine learning** content classification
- **Advanced anti-detection** techniques

## 🚨 Best Practices

1. **Start Small**: Test with `--max-items 5` first
2. **Respect Rate Limits**: Use appropriate `--delay` values
3. **Monitor Resources**: Different languages have different resource profiles
4. **Use Campaigns**: Coordinate multiple scrapers efficiently
5. **Check Dependencies**: Ensure runtimes are available before use

## 🔍 Troubleshooting

### Common Issues
1. **Node.js not found**: Install Node.js and npm
2. **Go binary missing**: Run `go build` in knowledge_scrapers directory  
3. **Rust binary missing**: Run `cargo build --release`
4. **Permission denied**: Check executable permissions on binaries
5. **Import errors**: Ensure Python path includes knowledge_scrapers

### Debug Commands
```bash
# Check Node.js availability
which node && node --version

# Check binary permissions
ls -la /home/adminx/Marina/knowledge_scrapers/forum_scraper
ls -la /home/adminx/Marina/knowledge_scrapers/target/release/

# Test registry import
python3 -c "from knowledge_scrapers.scraper_registry_v2 import ScraperRegistry; print('✅ Import successful')"
```

---

This multi-language approach provides Marina with the most suitable tool for each scraping challenge, combining the strengths of different programming languages for optimal performance and capabilities.
