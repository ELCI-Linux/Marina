use reqwest::Client;
use scraper::{Html, Selector, ElementRef};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::time::sleep;
use url::Url;
use regex::Regex;
use futures::future::join_all;
use tokio::fs;
use std::sync::Arc;
use tokio::sync::Semaphore;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeExample {
    language: String,
    code: String,
    description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiParameter {
    name: String,
    param_type: String,
    description: String,
    required: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiEndpoint {
    method: String,
    path: String,
    description: String,
    parameters: Vec<ApiParameter>,
    response_format: Option<String>,
    code_examples: Vec<CodeExample>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentationPage {
    url: String,
    title: String,
    content: String,
    section: Option<String>,
    subsection: Option<String>,
    api_endpoints: Vec<ApiEndpoint>,
    code_examples: Vec<CodeExample>,
    last_updated: Option<String>,
    tags: Vec<String>,
    scraped_at: String,
}

#[derive(Debug, Clone)]
pub struct PlatformConfig {
    content_selector: &'static str,
    title_selector: &'static str,
    code_selector: &'static str,
    navigation_selector: &'static str,
    api_selector: Option<&'static str>,
}

pub struct DocumentationScraperRust {
    platform: String,
    delay: Duration,
    client: Client,
    visited_urls: Arc<tokio::sync::Mutex<HashSet<String>>>,
    configs: HashMap<String, PlatformConfig>,
    max_concurrent: usize,
}

impl DocumentationScraperRust {
    pub fn new(platform: String, delay_seconds: f64, max_concurrent: usize) -> Self {
        let mut configs = HashMap::new();
        
        configs.insert("gitbook".to_string(), PlatformConfig {
            content_selector: ".page-inner",
            title_selector: "h1",
            code_selector: "pre code",
            navigation_selector: ".summary a",
            api_selector: None,
        });
        
        configs.insert("readthedocs".to_string(), PlatformConfig {
            content_selector: "[role=\"main\"]",
            title_selector: "h1",
            code_selector: ".highlight pre",
            navigation_selector: ".toctree-l1 a",
            api_selector: None,
        });
        
        configs.insert("swagger".to_string(), PlatformConfig {
            content_selector: ".swagger-ui",
            title_selector: "h1",
            code_selector: ".example pre",
            navigation_selector: ".operations-tag a",
            api_selector: Some(".opblock"),
        });
        
        configs.insert("sphinx".to_string(), PlatformConfig {
            content_selector: ".body",
            title_selector: "h1",
            code_selector: ".highlight pre",
            navigation_selector: ".toctree-l1 a",
            api_selector: None,
        });
        
        configs.insert("generic".to_string(), PlatformConfig {
            content_selector: "main, .content, .documentation",
            title_selector: "h1",
            code_selector: "pre, code",
            navigation_selector: "nav a, .toc a",
            api_selector: None,
        });

        let client = Client::builder()
            .user_agent("Marina-DocumentationScraper/3.0 (Educational Research)")
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            platform: platform.to_lowercase(),
            delay: Duration::from_millis((delay_seconds * 1000.0) as u64),
            client,
            visited_urls: Arc::new(tokio::sync::Mutex::new(HashSet::new())),
            configs,
            max_concurrent,
        }
    }

    fn extract_code_examples(&self, document: &Html) -> Vec<CodeExample> {
        let config = self.configs.get(&self.platform)
            .unwrap_or_else(|| self.configs.get("generic").unwrap());
        
        let code_selector = Selector::parse(config.code_selector).unwrap();
        let mut examples = Vec::new();

        for element in document.select(&code_selector) {
            let code_content = element.text().collect::<Vec<_>>().join(" ").trim().to_string();
            
            // Skip very short code snippets
            if code_content.len() < 10 {
                continue;
            }

            // Detect programming language from class attributes
            let language = element
                .value()
                .classes()
                .find(|class| {
                    class.starts_with("language-") || 
                    ["python", "javascript", "java", "rust", "go", "cpp", "bash"].contains(class)
                })
                .map(|class| {
                    if class.starts_with("language-") {
                        class.strip_prefix("language-").unwrap_or("text")
                    } else {
                        class
                    }
                })
                .unwrap_or("text")
                .to_string();

            // Try to find description from preceding elements
            let description = if let Some(parent) = element.parent() {
                if let Some(prev_sibling) = parent.prev_sibling() {
                    if let Some(elem_ref) = ElementRef::wrap(prev_sibling) {
                        if elem_ref.value().name() == "p" {
                            let desc = elem_ref.text().collect::<Vec<_>>().join(" ").trim().to_string();
                            if !desc.is_empty() && desc.len() < 200 {
                                Some(desc)
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                } else {
                    None
                }
            } else {
                None
            };

            examples.push(CodeExample {
                language,
                code: code_content,
                description,
            });
        }

        examples
    }

    fn extract_api_endpoints(&self, document: &Html, base_url: &str) -> Vec<ApiEndpoint> {
        let config = self.configs.get(&self.platform)
            .unwrap_or_else(|| self.configs.get("generic").unwrap());
        
        let mut endpoints = Vec::new();

        if let Some(api_selector_str) = config.api_selector {
            if let Ok(api_selector) = Selector::parse(api_selector_str) {
                for element in document.select(&api_selector) {
                    if let Some(endpoint) = self.parse_api_endpoint(element) {
                        endpoints.push(endpoint);
                    }
                }
            }
        }

        endpoints
    }

    fn parse_api_endpoint(&self, element: ElementRef) -> Option<ApiEndpoint> {
        // Parse Swagger/OpenAPI endpoint blocks
        let method_selector = Selector::parse(".opblock-summary-method").ok()?;
        let path_selector = Selector::parse(".opblock-summary-path").ok()?;
        let desc_selector = Selector::parse(".opblock-description").ok()?;

        let method = element
            .select(&method_selector)
            .next()?
            .text()
            .collect::<String>()
            .trim()
            .to_uppercase();

        let path = element
            .select(&path_selector)
            .next()?
            .text()
            .collect::<String>()
            .trim()
            .to_string();

        let description = element
            .select(&desc_selector)
            .next()
            .map(|e| e.text().collect::<String>().trim().to_string())
            .unwrap_or_default();

        // Extract parameters (simplified)
        let mut parameters = Vec::new();
        let param_selector = Selector::parse(".parameters .parameter").ok()?;
        
        for param_elem in element.select(&param_selector) {
            if let Some(param) = self.parse_api_parameter(param_elem) {
                parameters.push(param);
            }
        }

        // Extract code examples for this endpoint
        let example_selector = Selector::parse(".example pre").ok()?;
        let mut code_examples = Vec::new();
        
        for example_elem in element.select(&example_selector) {
            let code = example_elem.text().collect::<String>().trim().to_string();
            if !code.is_empty() {
                code_examples.push(CodeExample {
                    language: "json".to_string(),
                    code,
                    description: Some("API response example".to_string()),
                });
            }
        }

        Some(ApiEndpoint {
            method,
            path,
            description,
            parameters,
            response_format: None,
            code_examples,
        })
    }

    fn parse_api_parameter(&self, element: ElementRef) -> Option<ApiParameter> {
        let name_selector = Selector::parse(".parameter-name").ok()?;
        let type_selector = Selector::parse(".parameter-type").ok()?;
        let desc_selector = Selector::parse(".parameter-description").ok()?;

        let name = element
            .select(&name_selector)
            .next()?
            .text()
            .collect::<String>()
            .trim()
            .to_string();

        let param_type = element
            .select(&type_selector)
            .next()
            .map(|e| e.text().collect::<String>().trim().to_string())
            .unwrap_or_else(|| "string".to_string());

        let description = element
            .select(&desc_selector)
            .next()
            .map(|e| e.text().collect::<String>().trim().to_string())
            .unwrap_or_default();

        Some(ApiParameter {
            name,
            param_type,
            description,
            required: false, // Could be enhanced to detect required parameters
        })
    }

    fn extract_section_info(&self, document: &Html, url: &str) -> (Option<String>, Option<String>) {
        // Try to extract from breadcrumbs
        if let Ok(breadcrumb_selector) = Selector::parse(".breadcrumb li, .breadcrumbs a") {
            let breadcrumbs: Vec<String> = document
                .select(&breadcrumb_selector)
                .map(|e| e.text().collect::<String>().trim().to_string())
                .filter(|s| !s.is_empty())
                .collect();

            if breadcrumbs.len() > 1 {
                let section = breadcrumbs.get(breadcrumbs.len() - 2).cloned();
                let subsection = if breadcrumbs.len() > 2 {
                    breadcrumbs.last().cloned()
                } else {
                    None
                };
                return (section, subsection);
            }
        }

        // Fallback: extract from URL structure
        if let Ok(parsed_url) = Url::parse(url) {
            let path_segments: Vec<&str> = parsed_url
                .path_segments()
                .map(|segments| segments.collect())
                .unwrap_or_default();

            if path_segments.len() > 1 {
                let section = path_segments.get(path_segments.len() - 2)
                    .map(|s| s.replace('-', " ").replace('_', " "))
                    .map(|s| capitalize_words(&s));
                    
                let subsection = if path_segments.len() > 2 {
                    path_segments.last()
                        .map(|s| s.replace('-', " ").replace('_', " "))
                        .map(|s| capitalize_words(&s))
                } else {
                    None
                };
                
                return (section, subsection);
            }
        }

        (None, None)
    }

    fn extract_tags(&self, title: &str, content: &str, section: Option<&str>) -> Vec<String> {
        let text = format!("{} {} {}", 
            title.to_lowercase(), 
            content.to_lowercase(), 
            section.unwrap_or("").to_lowercase()
        );

        let tag_patterns = vec![
            (r"\bapi\b|\bendpoint\b|\brest\b", "api"),
            (r"\btutorial\b|\bguide\b|\bwalkthrough\b", "tutorial"),
            (r"\breference\b|\bdocs\b|\bdocumentation\b", "reference"),
            (r"\binstall\b|\bsetup\b|\bconfiguration\b", "installation"),
            (r"\bauth\b|\blogin\b|\btoken\b|\bsecurity\b", "authentication"),
            (r"\bdatabase\b|\bsql\b|\bmongo\b|\bmysql\b", "database"),
            (r"\bfrontend\b|\bui\b|\bjavascript\b|\breact\b", "frontend"),
            (r"\bbackend\b|\bserver\b|\bnode\b|\bpython\b", "backend"),
            (r"\bmobile\b|\bios\b|\bandroid\b|\bapp\b", "mobile"),
            (r"\bdeploy\b|\bproduction\b|\bhosting\b", "deployment"),
        ];

        let mut tags = Vec::new();
        for (pattern, tag) in tag_patterns {
            let regex = Regex::new(pattern).unwrap();
            if regex.is_match(&text) {
                tags.push(tag.to_string());
            }
        }

        tags
    }

    pub async fn scrape_documentation_page(&self, url: String) -> Option<DocumentationPage> {
        {
            let visited = self.visited_urls.lock().await;
            if visited.contains(&url) {
                return None;
            }
        }

        {
            let mut visited = self.visited_urls.lock().await;
            visited.insert(url.clone());
        }

        println!("📚 Scraping documentation: {}", url);
        
        // Rate limiting
        sleep(self.delay).await;

        let response = match self.client.get(&url).send().await {
            Ok(resp) if resp.status().is_success() => resp,
            Ok(resp) => {
                println!("❌ Failed to fetch {}: HTTP {}", url, resp.status());
                return None;
            }
            Err(e) => {
                println!("❌ Error fetching {}: {}", url, e);
                return None;
            }
        };

        let html_content = match response.text().await {
            Ok(content) => content,
            Err(e) => {
                println!("❌ Error reading response for {}: {}", url, e);
                return None;
            }
        };

        let document = Html::parse_document(&html_content);
        let config = self.configs.get(&self.platform)
            .unwrap_or_else(|| self.configs.get("generic").unwrap());

        // Extract title
        let title_selector = Selector::parse(config.title_selector).ok()?;
        let title = document
            .select(&title_selector)
            .next()
            .map(|e| e.text().collect::<String>().trim().to_string())
            .unwrap_or_else(|| "Documentation Page".to_string());

        // Extract main content
        let content_selector = Selector::parse(config.content_selector).ok()?;
        let content = document
            .select(&content_selector)
            .next()
            .map(|e| e.text().collect::<Vec<_>>().join("\n").trim().to_string())
            .unwrap_or_default();

        // Skip pages with very little content
        if content.len() < 100 {
            println!("⚠️ Skipping page with minimal content: {}", url);
            return None;
        }

        // Extract section information
        let (section, subsection) = self.extract_section_info(&document, &url);

        // Extract code examples
        let code_examples = self.extract_code_examples(&document);

        // Extract API endpoints
        let api_endpoints = self.extract_api_endpoints(&document, &url);

        // Extract tags
        let tags = self.extract_tags(&title, &content, section.as_deref());

        // Get current timestamp
        let scraped_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let scraped_at_str = format!("{}", scraped_at);

        Some(DocumentationPage {
            url,
            title,
            content,
            section,
            subsection,
            api_endpoints,
            code_examples,
            last_updated: None, // Could be enhanced to extract last updated date
            tags,
            scraped_at: scraped_at_str,
        })
    }

    pub async fn discover_documentation_links(&self, base_url: String, max_pages: usize) -> Vec<String> {
        let response = match self.client.get(&base_url).send().await {
            Ok(resp) if resp.status().is_success() => resp,
            _ => return Vec::new(),
        };

        let html_content = match response.text().await {
            Ok(content) => content,
            Err(_) => return Vec::new(),
        };

        let document = Html::parse_document(&html_content);
        let config = self.configs.get(&self.platform)
            .unwrap_or_else(|| self.configs.get("generic").unwrap());

        let nav_selector = Selector::parse(config.navigation_selector).unwrap();
        let mut doc_links = Vec::new();

        for element in document.select(&nav_selector) {
            if doc_links.len() >= max_pages {
                break;
            }

            if let Some(href) = element.value().attr("href") {
                if let Ok(full_url) = Url::parse(&base_url).and_then(|base| base.join(href)) {
                    let url_str = full_url.to_string();
                    
                    // Filter to same domain only
                    if let (Ok(base_parsed), Ok(link_parsed)) = (Url::parse(&base_url), Url::parse(&url_str)) {
                        if base_parsed.host() == link_parsed.host() {
                            doc_links.push(url_str);
                        }
                    }
                }
            }
        }

        doc_links.into_iter().take(max_pages).collect()
    }

    pub async fn scrape_documentation_site(&self, base_url: String, max_pages: usize) -> Vec<DocumentationPage> {
        println!("📖 Starting documentation scraping from: {}", base_url);

        // Start with the base URL
        let mut doc_urls = vec![base_url.clone()];

        // Discover additional documentation pages
        let discovered_urls = self.discover_documentation_links(base_url, max_pages - 1).await;
        doc_urls.extend(discovered_urls);

        // Limit to max_pages
        doc_urls.truncate(max_pages);

        // Create semaphore for concurrency control
        let semaphore = Arc::new(Semaphore::new(self.max_concurrent));

        // Scrape pages concurrently
        let tasks: Vec<_> = doc_urls
            .into_iter()
            .map(|url| {
                let semaphore = semaphore.clone();
                let scraper = self;
                async move {
                    let _permit = semaphore.acquire().await.unwrap();
                    scraper.scrape_documentation_page(url).await
                }
            })
            .collect();

        let results = join_all(tasks).await;
        let scraped_pages: Vec<DocumentationPage> = results.into_iter().filter_map(|x| x).collect();

        println!("✅ Scraped {} documentation pages", scraped_pages.len());
        scraped_pages
    }

    pub async fn save_results(&self, pages: Vec<DocumentationPage>, filename: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
        let filename = filename.unwrap_or_else(|| {
            let timestamp = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs();
            format!("documentation_scrape_{}_{}.json", self.platform, timestamp)
        });

        let results_dir = "scraping_results";
        fs::create_dir_all(results_dir).await?;

        let filepath = format!("{}/{}", results_dir, filename);

        // Generate analysis
        let analysis = self.analyze_documentation(&pages);

        #[derive(Serialize)]
        struct Results {
            platform: String,
            total_pages: usize,
            analysis: HashMap<String, serde_json::Value>,
            scraped_at: String,
            pages: Vec<DocumentationPage>,
        }

        let scraped_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
            .to_string();

        let results = Results {
            platform: self.platform.clone(),
            total_pages: pages.len(),
            analysis,
            scraped_at,
            pages,
        };

        let json_content = serde_json::to_string_pretty(&results)?;
        fs::write(&filepath, json_content).await?;

        println!("💾 Results saved to: {}", filepath);
        Ok(())
    }

    fn analyze_documentation(&self, pages: &[DocumentationPage]) -> HashMap<String, serde_json::Value> {
        let mut analysis = HashMap::new();

        if pages.is_empty() {
            return analysis;
        }

        // Basic statistics
        analysis.insert("total_pages".to_string(), serde_json::Value::Number(pages.len().into()));

        // Section analysis
        let mut sections = HashMap::new();
        for page in pages {
            if let Some(section) = &page.section {
                *sections.entry(section.clone()).or_insert(0) += 1;
            }
        }
        analysis.insert("sections".to_string(), serde_json::to_value(sections).unwrap());

        // Tag analysis
        let mut tags = HashMap::new();
        for page in pages {
            for tag in &page.tags {
                *tags.entry(tag.clone()).or_insert(0) += 1;
            }
        }
        analysis.insert("tags".to_string(), serde_json::to_value(tags).unwrap());

        // Code examples analysis
        let total_code_examples: usize = pages.iter().map(|p| p.code_examples.len()).sum();
        analysis.insert("total_code_examples".to_string(), serde_json::Value::Number(total_code_examples.into()));

        let mut programming_languages = HashMap::new();
        for page in pages {
            for example in &page.code_examples {
                *programming_languages.entry(example.language.clone()).or_insert(0) += 1;
            }
        }
        analysis.insert("programming_languages".to_string(), serde_json::to_value(programming_languages).unwrap());

        // API endpoints analysis
        let total_api_endpoints: usize = pages.iter().map(|p| p.api_endpoints.len()).sum();
        analysis.insert("total_api_endpoints".to_string(), serde_json::Value::Number(total_api_endpoints.into()));

        // Content length analysis
        let content_lengths: Vec<usize> = pages.iter().map(|p| p.content.len()).collect();
        let avg_content_length = if !content_lengths.is_empty() {
            content_lengths.iter().sum::<usize>() / content_lengths.len()
        } else {
            0
        };
        analysis.insert("avg_content_length".to_string(), serde_json::Value::Number(avg_content_length.into()));

        analysis
    }
}

fn capitalize_words(s: &str) -> String {
    s.split_whitespace()
        .map(|word| {
            let mut chars = word.chars();
            match chars.next() {
                None => String::new(),
                Some(first) => first.to_uppercase().chain(chars.as_str().to_lowercase().chars()).collect(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 4 {
        println!("Usage: {} <platform> <base_url> <max_pages>", args[0]);
        println!("Example: {} readthedocs https://docs.python.org/ 20", args[0]);
        std::process::exit(1);
    }

    let platform = args[1].clone();
    let base_url = args[2].clone();
    let max_pages: usize = args[3].parse().unwrap_or(20);

    // Create scraper with high concurrency for performance
    let scraper = DocumentationScraperRust::new(platform, 1.0, 10);

    // Scrape documentation site
    let pages = scraper.scrape_documentation_site(base_url, max_pages).await;

    if !pages.is_empty() {
        // Save results
        scraper.save_results(pages.clone(), None).await?;
        
        println!("\n✅ Documentation scraping completed successfully!");
        println!("📊 Pages scraped: {}", pages.len());
        
        let total_code_examples: usize = pages.iter().map(|p| p.code_examples.len()).sum();
        let total_api_endpoints: usize = pages.iter().map(|p| p.api_endpoints.len()).sum();
        
        println!("💻 Code examples found: {}", total_code_examples);
        println!("🔗 API endpoints found: {}", total_api_endpoints);
    } else {
        println!("⚠️ No pages were successfully scraped");
    }

    Ok(())
}
