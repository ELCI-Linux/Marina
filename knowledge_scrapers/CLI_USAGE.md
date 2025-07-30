# Marina CLI - General Scraper Usage

The Marina CLI has been updated to use the new generalized natural language scraper for the `scrape general` command.

## Usage

```bash
python3 marina_cli.py scrape general <URL> [options]
```

## Arguments

- `url`: Root URL to start scraping from (required)

## Options

- `--keywords [KEYWORDS ...]`: Keywords to focus scraping on (optional, auto-detected if not provided)
- `--max-depth MAX_DEPTH`: Maximum crawling depth (default: 2)
- `--delay DELAY`: Delay between requests in seconds (default: 1.0)

## Examples

### Basic Usage
```bash
# Scrape BBC News with auto-detected keywords
python3 marina_cli.py scrape general https://bbc.co.uk/news
```

### With Custom Keywords
```bash
# Scrape with specific focus keywords
python3 marina_cli.py scrape general https://bbc.co.uk/news --keywords news breaking latest politics
```

### Custom Depth and Rate Limiting
```bash
# Deep scraping with careful rate limiting
python3 marina_cli.py scrape general https://bbc.co.uk/sport --keywords sport football cricket --max-depth 3 --delay 2.0
```

### Technology News Sites
```bash
# Scrape technology content
python3 marina_cli.py scrape general https://techcrunch.com --keywords technology startup AI artificial intelligence
```

### Academic or Research Sites
```bash
# Scrape research content
python3 marina_cli.py scrape general https://arxiv.org/list/cs.AI/recent --keywords machine learning research paper
```

## What the Scraper Does

1. **Intelligent Content Recognition**: Automatically identifies news articles, reports, and high-quality content
2. **Rabbithole Reasoning**: Follows relevant links based on content similarity and keyword matching
3. **Topic Extraction**: Uses NLP to identify key topics and themes from scraped content
4. **Quality Scoring**: Assigns relevance scores to prioritize high-quality content
5. **Corpus Integration**: Automatically adds scraped content to Marina's knowledge base
6. **Results Storage**: Saves comprehensive scraping results with metadata

## Output

The scraper provides detailed statistics:
- Total pages scraped
- Average relevance score (0-10.0)
- Unique topics discovered
- High-relevance pages count
- Depth distribution analysis

## Integration with Marina

All scraped content is automatically:
- Added to Marina's neocorpus (`/home/adminx/Marina/feedback/neocorpus/`)
- Assigned quality scores for prioritization
- Made available for LLM training and response improvement
- Indexed for efficient retrieval

## Respectful Scraping

The scraper includes:
- Configurable rate limiting between requests
- Proper User-Agent identification
- Graceful error handling
- Timeout protection
- Content quality filtering

## Best Practices

1. **Start with lower depths (1-2)** for initial exploration
2. **Use specific keywords** for focused scraping
3. **Increase delays for heavy scraping** to be respectful to target servers
4. **Monitor output** to ensure content quality meets expectations
5. **Use descriptive keywords** that match the content you're looking for

## Comparison with ArchWiki Scraper

| Feature | General Scraper | ArchWiki Scraper |
|---------|-----------------|------------------|
| **Scope** | Any website | ArchWiki only |
| **Keywords** | User-defined or auto-detected | Predefined (Flatpak-focused) |
| **Content Type** | News, articles, general web content | Technical documentation |
| **Flexibility** | High | Specialized |
| **Use Case** | General knowledge acquisition | Specific technical knowledge |

Both scrapers use Marina's rabbithole reasoning approach and integrate seamlessly with the corpus system.
