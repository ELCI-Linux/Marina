# Marina Enhanced Scraping Pipeline

## Overview

The Enhanced Scraping Pipeline integrates Marina's powerful 4-engine analysis system with automatic LLM revision capabilities. This creates a comprehensive workflow that not only scrapes web content but also analyzes it through multiple analytical lenses and uses the insights to continuously improve Marina's knowledge base.

## Architecture

### Phase 1: Enhanced Web Scraping
- Uses the existing `general_scraper.py` with rabbithole reasoning
- Intelligently navigates websites following relevant links
- Applies quality filtering based on configurable thresholds
- Extracts content with contextual metadata

### Phase 2: 4-Engine Analysis Pipeline
1. **Textual Analysis** (Saveless Ingest Engine)
   - Processes raw text content without persistent storage
   - Analyzes confidence scores and keyword extraction
   - Privacy-focused memory-only processing

2. **Semantic Analysis** (Knowledge Asymmetry Engine)
   - Detects knowledge gaps and imbalances
   - Analyzes topic distribution and relationships
   - Provides balance recommendations

3. **Contextual Analysis** (Token Minimization Engine)
   - Optimizes content for efficient processing
   - Reduces redundancy while preserving meaning
   - Estimates token savings and optimization techniques

4. **Inference Analysis** (Pattern Analysis Engine)
   - Detects patterns in content structure and topics
   - Analyzes temporal and keyword relationships
   - Assesses inference quality and pattern strength

### Phase 3: LLM Revision & Training
- Evaluates analysis quality to determine revision necessity
- Prepares training data from high-quality scraped content
- Triggers Marina's custom LLM training pipeline
- Creates topic-specific model improvements
- Tracks training metrics and model versioning

## CLI Integration

The enhanced pipeline is fully integrated into Marina's CLI system:

```bash
# Basic enhanced scraping
python marina_cli.py scrape enhanced https://example.com

# With custom keywords
python marina_cli.py scrape enhanced https://bbc.co.uk/news --keywords breaking news analysis

# Advanced configuration
python marina_cli.py scrape enhanced https://site.com \
  --max-depth 3 \
  --delay 2.0 \
  --quality-threshold 7.0 \
  --no-retrain
```

### CLI Options

- `url`: Target URL to scrape from
- `--keywords`: Focus keywords (default: auto-detect)
- `--max-depth`: Maximum crawling depth (default: 2)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--quality-threshold`: Quality score threshold (default: 5.0)
- `--auto-retrain`: Enable automatic LLM retraining (default: True)
- `--no-retrain`: Disable LLM retraining

## Configuration

### Pipeline Configuration Structure

```python
config = {
    "scraping": {
        "max_depth": 2,
        "delay_between_requests": 1.0,
        "quality_threshold": 5.0
    },
    "analysis": {
        "saveless_mode": True,
        "enable_asymmetry_detection": True,
        "token_optimization": True,
        "pattern_analysis": True
    },
    "llm_training": {
        "auto_retrain": True,
        "improvement_threshold": 0.05,
        "max_training_time": 3600,
        "base_model": "microsoft/DialoGPT-small"
    }
}
```

### Quality Thresholds
- **1-3**: Low quality content (basic info, short articles)
- **4-6**: Medium quality content (standard articles, moderate depth)
- **7-8**: High quality content (detailed analysis, expert content)
- **9-10**: Exceptional quality (comprehensive guides, research papers)

## Usage Examples

### Example 1: News Analysis
```bash
python marina_cli.py scrape enhanced https://bbc.co.uk/news \
  --keywords breaking politics economy \
  --quality-threshold 6.0
```

### Example 2: Technical Documentation
```bash
python marina_cli.py scrape enhanced https://docs.python.org \
  --max-depth 3 \
  --delay 0.5 \
  --keywords tutorial guide documentation
```

### Example 3: Research Without Retraining
```bash
python marina_cli.py scrape enhanced https://arxiv.org \
  --quality-threshold 8.0 \
  --no-retrain
```

## Output Structure

### Pipeline Results
```json
{
  "pipeline_start": "2024-01-01T12:00:00",
  "root_url": "https://example.com",
  "keywords": ["keyword1", "keyword2"],
  "scraping_results": {
    "total_pages_scraped": 25,
    "high_quality_nodes": [...],
    "summary": {
      "average_relevance": 7.2,
      "unique_topics": 15
    }
  },
  "analysis_results": {
    "quality_score": 0.85,
    "combined_insights": {
      "training_data_quality": "high",
      "optimization_recommendations": [...],
      "engines_successful": 4
    }
  },
  "llm_revision_results": {
    "model_path": "/path/to/new/model",
    "improvement_metrics": {...}
  },
  "pipeline_summary": {
    "execution_time": 245.3,
    "phases_completed": ["scraping", "analysis", "llm_revision"],
    "next_steps": [...]
  }
}
```

## Testing

### Quick Test
```bash
cd /home/adminx/Marina/knowledge_scrapers
python test_enhanced_pipeline.py
```

### Engine Availability Check
The test script will show which analysis engines are available:
```
🔍 Testing Analysis Engine Availability
   Saveless Ingest: ✅ Available
   Knowledge Asymmetry: ✅ Available  
   Token Minimization: ❌ Not Available
   Pattern Analysis: ✅ Available
   LLM Training: ✅ Available

Total: 4/5 engines available
```

## Performance Considerations

### Resource Usage
- **Memory**: 1-4GB depending on content volume and analysis depth
- **CPU**: Multi-threaded analysis engines can utilize multiple cores
- **Network**: Respectful crawling with configurable delays
- **Storage**: Results saved to `/home/adminx/Marina/knowledge_scrapers/enhanced_results/`

### Optimization Tips
1. **Start Small**: Begin with `--max-depth 1` for testing
2. **Quality Filtering**: Use higher thresholds (6-8) for focused analysis
3. **Selective Retraining**: Use `--no-retrain` for exploration phases
4. **Batch Processing**: Process related sites in sequence for topic coherence

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
[ERROR] Enhanced scraping pipeline failed: No module named 'learning.llm_builder'
```
**Solution**: Ensure all Marina modules are properly installed and paths are set.

#### 2. Network Timeouts
```bash
[ERROR] General web scraping failed: Connection timeout
```
**Solution**: Increase `--delay` parameter or check network connectivity.

#### 3. Low Quality Results
```bash
⚠️ Analysis quality too low for LLM revision
```
**Solution**: Lower `--quality-threshold` or target higher-quality content sources.

#### 4. LLM Training Failures
```bash
❌ LLM training failed: Insufficient training data
```
**Solution**: Scrape more content or lower quality thresholds to get more training data.

### Debug Mode
Enable detailed error reporting:
```python
# In enhanced_scraping_pipeline.py
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Distributed Processing**: Multi-node scraping and analysis
2. **Real-time Monitoring**: Live pipeline status dashboard  
3. **Custom Analysis Engines**: Plugin system for specialized analyzers
4. **Enhanced LLM Integration**: Support for larger models and fine-tuning
5. **Scheduled Scraping**: Automated periodic knowledge updates

### Integration Points
- **Feedback System**: Connect with Marina's feedback loop
- **Contextual Engine**: Integration with system context scanning
- **Voice Interface**: Voice-activated scraping commands
- **Model Regulator**: Automatic model selection and optimization

## Contributing

### Adding New Analysis Engines
1. Create engine class following the pattern in existing engines
2. Add availability check to `enhanced_scraping_pipeline.py`  
3. Implement data preparation method
4. Add engine runner method
5. Update combined insights logic

### Extending Scraping Capabilities
1. Modify `general_scraper.py` for new content types
2. Update data preparation methods in pipeline
3. Add new quality assessment criteria
4. Test with diverse content sources

## Security & Privacy

### Data Handling
- **Saveless Mode**: Content processed in memory only, not stored permanently
- **Privacy Respect**: Adheres to robots.txt and rate limiting
- **Content Filtering**: Removes sensitive information during processing
- **Secure Storage**: Results encrypted and access-controlled

### Network Behavior
- **Respectful Crawling**: Configurable delays between requests
- **User Agent**: Identifies as Marina research system
- **Robots.txt Compliance**: Respects site crawling preferences
- **Rate Limiting**: Prevents server overload

---

*This documentation covers Marina's Enhanced Scraping Pipeline v1.0. For updates and advanced configurations, consult the Marina development team.*
