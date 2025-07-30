# Marina Knowledge Scrapers

Marina's knowledge scraping system uses **rabbithole reasoning** to intelligently crawl and extract knowledge from authoritative sources like ArchWiki. This system enhances Marina's knowledge base with domain-specific information and improves response quality.

## 🧠 Rabbithole Reasoning

**Rabbithole reasoning** is Marina's approach to deep knowledge acquisition through recursive exploration:

1. **Seed Topics**: Start with predefined relevant topics (e.g., "flatpak", "sandboxing", "container runtime")
2. **Intelligent Following**: Follow links that are contextually relevant to the seed topics
3. **Relevance Scoring**: Score each page based on keyword density, topic relevance, and content quality
4. **Depth Control**: Recursively explore related pages up to a maximum depth
5. **Knowledge Graph**: Build a comprehensive knowledge graph of interconnected concepts

## 🏗️ Architecture

```
Marina Knowledge Scraping System
├── RabbitholeReasoner          # Core reasoning engine
│   ├── Relevance Scoring       # Content relevance calculation
│   ├── Topic Extraction        # Extract technical concepts
│   ├── Link Analysis           # Find related content
│   └── Knowledge Graph         # Build interconnected nodes
├── ArchWikiFlatpakScraper      # Specialized Flatpak scraper
│   ├── Entry Points            # Curated starting URLs
│   ├── Content Processing      # Clean and structure content
│   └── Corpus Integration      # Add to Marina's knowledge base
└── Corpus Integration
    ├── NeocorpusBuilder        # Build knowledge corpus
    ├── Quality Metrics         # Assess content quality
    └── Feedback Integration    # Learn from user feedback
```

## 🚀 Usage

### Marina CLI Commands

```bash
# Scrape ArchWiki for comprehensive Flatpak knowledge
python3 marina_cli.py scrape archwiki-flatpak --max-depth 3 --delay 2.0

# General topic scraping from ArchWiki
python3 marina_cli.py scrape general "container runtime" --source archwiki --max-depth 2

# View available scraping options
python3 marina_cli.py scrape --help
```

### Programmatic Usage

```python
from knowledge_scrapers.archwiki_flatpak_scraper import ArchWikiFlatpakScraper

# Initialize scraper
scraper = ArchWikiFlatpakScraper()

# Perform comprehensive scraping
results = scraper.scrape_comprehensive_knowledge()

print(f"Scraped {results['total_pages_scraped']} pages")
print(f"Average relevance: {results['summary']['average_relevance']:.2f}/10.0")
```

## 🎯 Specialized Scrapers

### ArchWiki Flatpak Scraper

Specialized scraper for comprehensive Flatpak and application sandboxing knowledge:

**Entry Points:**
- `https://wiki.archlinux.org/title/Flatpak`
- `https://wiki.archlinux.org/title/Bubblewrap`
- `https://wiki.archlinux.org/title/Sandboxing`
- `https://wiki.archlinux.org/title/Application_sandboxing`
- `https://wiki.archlinux.org/title/Package_management`

**Key Features:**
- **Smart Link Following**: Only follows links relevant to containerization and sandboxing
- **Content Quality Scoring**: Evaluates technical depth and relevance
- **Topic Extraction**: Identifies technical terms, commands, and concepts
- **Deduplication**: Avoids scraping duplicate content

**Relevance Keywords:**
- **High Priority**: flatpak, flathub, sandbox, runtime, portal, permissions
- **Medium Priority**: package, application, install, distribution, container
- **Low Priority**: software, linux, system, user, security

## 📊 Knowledge Node Structure

Each scraped page becomes a `KnowledgeNode` with:

```python
@dataclass
class KnowledgeNode:
    url: str                    # Source URL
    title: str                  # Page title
    content: str                # Cleaned text content
    topics: List[str]           # Extracted topics/concepts
    related_links: List[str]    # Relevant related links
    depth: int                  # Scraping depth level
    relevance_score: float      # 0-10 relevance score
    scraped_at: datetime        # Timestamp
```

## 🎛️ Configuration

### Scraper Settings

- **Max Depth**: Maximum recursive depth (default: 3)
- **Request Delay**: Delay between requests in seconds (default: 1.5)
- **Quality Thresholds**: Minimum content length, relevance scores
- **Keyword Weights**: Relevance scoring weights for different keyword types

### Rate Limiting

Marina respects website resources:
- Configurable delay between requests
- User-Agent identification as educational tool
- Graceful error handling
- Timeout protection

## 📈 Integration with Marina

### Corpus Building

Scraped knowledge automatically integrates with Marina's corpus:

1. **Quality Assessment**: Content quality scoring and filtering
2. **Corpus Entry Creation**: Convert knowledge nodes to corpus format
3. **Storage**: Save to Marina's neocorpus directory
4. **Indexing**: Update corpus index for efficient retrieval

### Feedback Integration

Marina learns from user feedback:
- Low-scoring responses trigger targeted scraping
- User comments identify knowledge gaps
- Feedback analysis guides future scraping priorities

### LLM Enhancement

Scraped knowledge improves Marina's responses:
- Domain-specific terminology
- Technical accuracy
- Comprehensive coverage
- Up-to-date information

## 🔍 Quality Metrics

Marina tracks scraping quality:

```json
{
  "total_nodes": 12,
  "average_relevance": 5.23,
  "max_relevance": 8.56,
  "unique_topics": 151,
  "total_topics": 240,
  "high_relevance_pages": 6,
  "depth_distribution": {
    "0": 5,  // Entry points
    "1": 4,  // First level
    "2": 3   // Second level
  }
}
```

## 🆕 Modular Scraper Collection

Marina now includes a comprehensive collection of specialized scrapers designed for various web scraping situations. Each scraper uses a modular approach for easy extension and customization.

### 📋 Available Scrapers

#### 1. **E-commerce Product Scraper** (`ecommerce_scraper.py`)
Extracts product information from e-commerce websites.
- **Features**: Product details, pricing, availability, descriptions
- **Usage**: `scraper = EcommerceScraper("https://example-store.com")`
- **Output**: Product listings with structured metadata

#### 2. **Social Media Content Scraper** (`social_media_scraper.py`)
Extracts posts and content from social media platforms.
- **Platforms**: Twitter, Reddit, Facebook
- **Features**: Posts, engagement metrics, hashtags, user interactions
- **Usage**: `scraper = SocialMediaScraper("twitter")`
- **Output**: Social media posts with sentiment analysis

#### 3. **Forum Discussion Scraper** (`forum_scraper.py`)
Extracts discussions and posts from forum platforms.
- **Platforms**: phpBB, vBulletin, Discourse, Reddit, Generic
- **Features**: Thread extraction, post analysis, user interactions
- **Usage**: `scraper = ForumScraper("phpbb")`
- **Output**: Complete forum threads with metadata

#### 4. **Academic Paper Scraper** (`academic_scraper.py`)
Extracts academic papers and research content from repositories.
- **Platforms**: arXiv, PubMed, IEEE Xplore, ACM Digital Library, Google Scholar
- **Features**: Paper metadata, abstracts, citations, research field classification
- **Usage**: `scraper = AcademicScraper("arxiv")`
- **Output**: Academic papers with research analysis

#### 5. **Job Listings Scraper** (`job_scraper.py`)
Extracts job listings from career websites.
- **Platforms**: Indeed, LinkedIn, Glassdoor
- **Features**: Job details, requirements, company info, industry categorization
- **Usage**: `scraper = JobScraper("indeed")`
- **Output**: Job listings with market analysis

#### 6. **Real Estate Scraper** (`real_estate_scraper.py`)
Extracts property listings from real estate websites.
- **Platforms**: Zillow, Realtor.com, Trulia
- **Features**: Property details, pricing, location, market analysis
- **Usage**: `scraper = RealEstateScraper("zillow")`
- **Output**: Property listings with market insights

#### 7. **Documentation Scraper** (`documentation_scraper.py`)
Extracts technical documentation and API references.
- **Platforms**: GitBook, ReadTheDocs, Swagger, Sphinx, Generic
- **Features**: API endpoints, code examples, hierarchical content organization
- **Usage**: `scraper = DocumentationScraper("readthedocs")`
- **Output**: Structured documentation with code analysis

#### 8. **General Web Scraper** (`general_scraper.py`)
General-purpose scraper using rabbithole reasoning.
- **Features**: Universal compatibility, advanced relevance scoring, topic extraction
- **Usage**: `scraper = GeneralScraper("https://example.com")`
- **Output**: Intelligently filtered web content

### 🎯 Scraper Registry System

The **Scraper Registry** (`scraper_registry.py`) provides centralized management:

```python
from knowledge_scrapers.scraper_registry import ScraperRegistry

# Initialize registry
registry = ScraperRegistry()

# List available scrapers
scrapers = registry.list_scrapers()

# Create scraping jobs
jobs = [
    ScrapingJob('academic', 'arxiv', '', {'search_query': 'machine learning'}),
    ScrapingJob('job', 'indeed', 'https://indeed.com/jobs?q=python', {'max_jobs': 10})
]

# Run coordinated campaign
results = registry.create_scraping_campaign("research_campaign", jobs)
```

### 🔧 Unified Features

All scrapers share common capabilities:
- **Rate Limiting**: Respectful scraping with configurable delays
- **Error Handling**: Graceful failure recovery
- **Result Storage**: Automatic JSON output with metadata
- **Modular Design**: Easy extension for new platforms
- **Ethical Scraping**: Proper User-Agent and robots.txt respect

## 📁 File Structure

```
knowledge_scrapers/
├── README.md                           # This file
├── general_scraper.py                  # NEW: Universal news scraper
├── usage_examples.py                   # NEW: Usage examples
├── archwiki_flatpak_scraper.py        # Specialized Flatpak scraper
├── scraping_results/                  # Scraping result logs
│   ├── news_scrape_*.json             # NEW: General scraper results
│   └── archwiki_flatpak_scrape_*.json # ArchWiki scraper results
└── __init__.py

feedback/neocorpus/                     # Generated corpus entries
├── entry_news_*.json                  # NEW: News scraper entries
├── entry_archwiki_flatpak_*.json      # ArchWiki scraper entries
├── corpus_metadata.json               # Corpus metadata
└── corpus_index.json                  # Entry index
```

## 🎬 Demo

Run the comprehensive demo to see the full workflow:

```bash
python3 demo_archwiki_scraper.py
```

This demonstrates:
1. Knowledge scraping with rabbithole reasoning
2. Corpus building and integration
3. LLM response improvement
4. Feedback collection and analysis

## 🛡️ Ethics and Best Practices

- **Respectful Scraping**: Rate limiting and proper User-Agent
- **Educational Purpose**: Clear identification as educational tool
- **No Overloading**: Reasonable delays between requests
- **Quality Focus**: Prioritize authoritative sources like ArchWiki
- **Transparency**: Open about scraping activities

## 🔮 Future Enhancements

- **Multi-Source Integration**: Wikipedia, GitHub, documentation sites
- **Specialized Scrapers**: Different domains (security, development, etc.)
- **Dynamic Prioritization**: User query patterns drive scraping focus
- **Knowledge Graph Visualization**: Visual representation of learned concepts
- **Automated Updates**: Periodic re-scraping for updated information

## 📚 External Context Used

<citations>
  <document>
      <document_type>WEB_PAGE</document_type>
      <document_id>https://wiki.archlinux.org/title/Main_page</document_id>
  </document>
</citations>

This system leverages the comprehensive ArchWiki documentation to enhance Marina's knowledge base, particularly around Flatpaks, application sandboxing, and Linux system administration topics.
