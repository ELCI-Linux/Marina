package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
)

// ForumPost represents a forum post with extracted content
type ForumPost struct {
	URL           string    `json:"url"`
	ThreadTitle   string    `json:"thread_title"`
	Author        string    `json:"author"`
	Content       string    `json:"content"`
	PostNumber    int       `json:"post_number"`
	Timestamp     string    `json:"timestamp,omitempty"`
	LikesCount    *int      `json:"likes_count,omitempty"`
	RepliesCount  *int      `json:"replies_count,omitempty"`
	ForumCategory string    `json:"forum_category,omitempty"`
	ScrapedAt     time.Time `json:"scraped_at"`
}

// ForumThread represents a complete forum thread
type ForumThread struct {
	URL          string      `json:"url"`
	Title        string      `json:"title"`
	Category     string      `json:"category"`
	Author       string      `json:"author"`
	Posts        []ForumPost `json:"posts"`
	ViewsCount   *int        `json:"views_count,omitempty"`
	RepliesCount int         `json:"replies_count"`
	CreatedAt    string      `json:"created_at,omitempty"`
	LastPostAt   string      `json:"last_post_at,omitempty"`
	ScrapedAt    time.Time   `json:"scraped_at"`
}

// PlatformConfig holds platform-specific configuration
type PlatformConfig struct {
	ThreadSelector    string
	PostSelector      string
	ContentSelector   string
	AuthorSelector    string
	TimestampSelector string
}

// ForumScraperGo implements high-performance forum scraping with Go's concurrency
type ForumScraperGo struct {
	platform     string
	delay        time.Duration
	client       *http.Client
	visitedURLs  map[string]bool
	visitedMutex sync.RWMutex
	configs      map[string]PlatformConfig
}

// NewForumScraper creates a new forum scraper instance
func NewForumScraper(platform string, delaySeconds float64) *ForumScraperGo {
	configs := map[string]PlatformConfig{
		"phpbb": {
			ThreadSelector:    ".topictitle",
			PostSelector:      ".post",
			ContentSelector:   ".content",
			AuthorSelector:    ".username",
			TimestampSelector: ".author .responsive-hide",
		},
		"vbulletin": {
			ThreadSelector:    ".threadtitle",
			PostSelector:      "[id^=\"post_\"]",
			ContentSelector:   ".postcontent",
			AuthorSelector:    ".username_container",
			TimestampSelector: ".postdate",
		},
		"discourse": {
			ThreadSelector:    ".topic-title",
			PostSelector:      ".topic-post",
			ContentSelector:   ".cooked",
			AuthorSelector:    ".username",
			TimestampSelector: ".relative-date",
		},
		"reddit": {
			ThreadSelector:    "[data-testid=\"post-content\"]",
			PostSelector:      ".Comment",
			ContentSelector:   "[data-testid=\"comment\"]",
			AuthorSelector:    "[data-testid=\"comment_author_link\"]",
			TimestampSelector: "[data-testid=\"comment_timestamp\"]",
		},
		"generic": {
			ThreadSelector:    "h1, .thread-title, .topic-title",
			PostSelector:      ".post, .message, .comment",
			ContentSelector:   ".content, .message-content, .post-content",
			AuthorSelector:    ".author, .username, .user",
			TimestampSelector: ".timestamp, .date, .time",
		},
	}

	return &ForumScraperGo{
		platform:    strings.ToLower(platform),
		delay:       time.Duration(delaySeconds * float64(time.Second)),
		visitedURLs: make(map[string]bool),
		configs:     configs,
		client: &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

// extractNumber extracts numerical values from text using regex patterns
func (fs *ForumScraperGo) extractNumber(text string, keywords []string) *int {
	text = strings.ToLower(text)
	for _, keyword := range keywords {
		patterns := []string{
			fmt.Sprintf(`(\d+)\s*%s`, keyword),
			fmt.Sprintf(`%s:?\s*(\d+)`, keyword),
			fmt.Sprintf(`%s\s*\((\d+)\)`, keyword),
		}

		for _, pattern := range patterns {
			re := regexp.MustCompile(pattern)
			matches := re.FindStringSubmatch(text)
			if len(matches) > 1 {
				if num, err := strconv.Atoi(matches[1]); err == nil {
					return &num
				}
			}
		}
	}
	return nil
}

// extractThreadMetadata extracts thread-level metadata
func (fs *ForumScraperGo) extractThreadMetadata(doc *goquery.Document, url string) map[string]interface{} {
	metadata := make(map[string]interface{})

	// Extract thread title
	titleSelectors := []string{".thread-title", ".topic-title", "h1", ".topictitle"}
	for _, selector := range titleSelectors {
		if title := doc.Find(selector).First().Text(); title != "" {
			metadata["title"] = strings.TrimSpace(title)
			break
		}
	}

	// Extract category/forum name
	categorySelectors := []string{".breadcrumb a", ".forum-name", ".category-name"}
	for _, selector := range categorySelectors {
		if category := doc.Find(selector).First().Text(); category != "" {
			metadata["category"] = strings.TrimSpace(category)
			break
		}
	}

	// Extract view count
	pageText := doc.Text()
	viewPatterns := []string{`Views?:?\s*(\d+)`, `(\d+)\s*views?`}
	for _, pattern := range viewPatterns {
		re := regexp.MustCompile(`(?i)` + pattern)
		if matches := re.FindStringSubmatch(pageText); len(matches) > 1 {
			if views, err := strconv.Atoi(matches[1]); err == nil {
				metadata["views_count"] = views
				break
			}
		}
	}

	return metadata
}

// scrapePost extracts data from a single forum post element
func (fs *ForumScraperGo) scrapePost(selection *goquery.Selection, threadTitle, threadURL string, postNumber int) *ForumPost {
	config, exists := fs.configs[fs.platform]
	if !exists {
		config = fs.configs["generic"]
	}

	// Extract post content
	content := strings.TrimSpace(selection.Find(config.ContentSelector).Text())
	if len(content) < 10 {
		return nil // Skip very short posts
	}

	// Extract author
	author := strings.TrimSpace(selection.Find(config.AuthorSelector).Text())
	if author == "" {
		author = "Anonymous"
	}

	// Extract timestamp
	var timestamp string
	if timestampElem := selection.Find(config.TimestampSelector); timestampElem.Length() > 0 {
		if datetime, exists := timestampElem.Attr("datetime"); exists {
			timestamp = datetime
		} else {
			timestamp = strings.TrimSpace(timestampElem.Text())
		}
	}

	// Extract engagement metrics
	postText := selection.Text()
	likesCount := fs.extractNumber(postText, []string{"like", "upvote", "thumbs"})
	repliesCount := fs.extractNumber(postText, []string{"reply", "response"})

	// Extract forum category if available
	var forumCategory string
	if categoryElem := selection.Find(".category, .forum"); categoryElem.Length() > 0 {
		forumCategory = strings.TrimSpace(categoryElem.Text())
	}

	return &ForumPost{
		URL:           fmt.Sprintf("%s#post%d", threadURL, postNumber),
		ThreadTitle:   threadTitle,
		Author:        author,
		Content:       content,
		PostNumber:    postNumber,
		Timestamp:     timestamp,
		LikesCount:    likesCount,
		RepliesCount:  repliesCount,
		ForumCategory: forumCategory,
		ScrapedAt:     time.Now(),
	}
}

// scrapeThread scrapes a complete forum thread
func (fs *ForumScraperGo) scrapeThread(threadURL string, maxPosts int) (*ForumThread, error) {
	// Check if already visited
	fs.visitedMutex.RLock()
	if fs.visitedURLs[threadURL] {
		fs.visitedMutex.RUnlock()
		return nil, fmt.Errorf("thread already visited")
	}
	fs.visitedMutex.RUnlock()

	// Mark as visited
	fs.visitedMutex.Lock()
	fs.visitedURLs[threadURL] = true
	fs.visitedMutex.Unlock()

	fmt.Printf("🔍 Scraping forum thread: %s\n", threadURL)

	// Rate limiting
	time.Sleep(fs.delay)

	// Fetch the page
	req, err := http.NewRequest("GET", threadURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Marina-ForumScraper/2.0 (Educational Research)")

	resp, err := fs.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	// Parse the HTML
	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	// Extract thread metadata
	metadata := fs.extractThreadMetadata(doc, threadURL)
	threadTitle, _ := metadata["title"].(string)
	if threadTitle == "" {
		threadTitle = "Unknown Thread"
	}

	// Extract posts using goroutines for concurrent processing
	config, exists := fs.configs[fs.platform]
	if !exists {
		config = fs.configs["generic"]
	}

	postElements := doc.Find(config.PostSelector)
	posts := make([]*ForumPost, 0, maxPosts)
	postsChan := make(chan *ForumPost, maxPosts)
	var wg sync.WaitGroup

	// Limit concurrent goroutines
	semaphore := make(chan struct{}, 10)

	postElements.Each(func(i int, s *goquery.Selection) {
		if i >= maxPosts {
			return
		}

		wg.Add(1)
		go func(index int, selection *goquery.Selection) {
			defer wg.Done()
			semaphore <- struct{}{} // Acquire semaphore
			defer func() { <-semaphore }() // Release semaphore

			if post := fs.scrapePost(selection, threadTitle, threadURL, index+1); post != nil {
				postsChan <- post
			}
		}(i, s)
	})

	// Close channel when all goroutines complete
	go func() {
		wg.Wait()
		close(postsChan)
	}()

	// Collect posts
	for post := range postsChan {
		posts = append(posts, post)
	}

	if len(posts) == 0 {
		return nil, fmt.Errorf("no posts found in thread")
	}

	// Build thread object
	thread := &ForumThread{
		URL:          threadURL,
		Title:        threadTitle,
		Category:     metadata["category"].(string),
		Author:       posts[0].Author,
		Posts:        make([]ForumPost, len(posts)),
		RepliesCount: len(posts) - 1,
		ScrapedAt:    time.Now(),
	}

	// Convert post pointers to values
	for i, post := range posts {
		thread.Posts[i] = *post
	}

	// Set optional fields
	if viewsCount, ok := metadata["views_count"].(int); ok {
		thread.ViewsCount = &viewsCount
	}
	if len(posts) > 0 {
		thread.CreatedAt = posts[0].Timestamp
		thread.LastPostAt = posts[len(posts)-1].Timestamp
	}

	fmt.Printf("✅ Scraped thread with %d posts\n", len(posts))
	return thread, nil
}

// discoverThreads discovers thread URLs from a forum index or category page
func (fs *ForumScraperGo) discoverThreads(forumURL string, maxThreads int) ([]string, error) {
	fmt.Printf("🔍 Discovering threads from: %s\n", forumURL)

	req, err := http.NewRequest("GET", forumURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Marina-ForumScraper/2.0 (Educational Research)")

	resp, err := fs.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var threadURLs []string
	selectors := []string{
		"a[href*=\"/thread/\"]",
		"a[href*=\"/topic/\"]",
		"a[href*=\"/t/\"]",
		"a[href*=\"/viewtopic.php\"]",
		".threadtitle a",
		".topictitle",
	}

	for _, selector := range selectors {
		doc.Find(selector).Each(func(i int, s *goquery.Selection) {
			if len(threadURLs) >= maxThreads {
				return
			}

			if href, exists := s.Attr("href"); exists {
				// Convert relative URLs to absolute
				if strings.HasPrefix(href, "/") {
					href = strings.TrimSuffix(forumURL, "/") + href
				} else if !strings.HasPrefix(href, "http") {
					href = strings.TrimSuffix(forumURL, "/") + "/" + href
				}
				threadURLs = append(threadURLs, href)
			}
		})

		if len(threadURLs) > 0 {
			break // Found threads with this selector
		}
	}

	// Remove duplicates
	seen := make(map[string]bool)
	unique := make([]string, 0, len(threadURLs))
	for _, url := range threadURLs {
		if !seen[url] {
			seen[url] = true
			unique = append(unique, url)
		}
	}

	if len(unique) > maxThreads {
		unique = unique[:maxThreads]
	}

	fmt.Printf("📊 Discovered %d thread URLs\n", len(unique))
	return unique, nil
}

// scrapeForum scrapes multiple threads from a forum with concurrent processing
func (fs *ForumScraperGo) scrapeForum(forumURL string, maxThreads, maxPostsPerThread int) ([]*ForumThread, error) {
	fmt.Printf("🚀 Starting forum scraping from: %s\n", forumURL)

	// Discover thread URLs
	threadURLs, err := fs.discoverThreads(forumURL, maxThreads)
	if err != nil {
		return nil, err
	}

	// Scrape threads concurrently
	threads := make([]*ForumThread, 0, len(threadURLs))
	threadsChan := make(chan *ForumThread, len(threadURLs))
	var wg sync.WaitGroup

	// Limit concurrent threads to avoid overwhelming the server
	semaphore := make(chan struct{}, 5)

	for _, url := range threadURLs {
		wg.Add(1)
		go func(threadURL string) {
			defer wg.Done()
			semaphore <- struct{}{} // Acquire semaphore
			defer func() { <-semaphore }() // Release semaphore

			if thread, err := fs.scrapeThread(threadURL, maxPostsPerThread); err == nil {
				threadsChan <- thread
			} else {
				fmt.Printf("❌ Failed to scrape thread %s: %v\n", threadURL, err)
			}
		}(url)
	}

	// Close channel when all goroutines complete
	go func() {
		wg.Wait()
		close(threadsChan)
	}()

	// Collect threads
	for thread := range threadsChan {
		threads = append(threads, thread)
	}

	fmt.Printf("✅ Scraped %d threads from forum\n", len(threads))
	return threads, nil
}

// saveResults saves scraped forum threads to JSON file
func (fs *ForumScraperGo) saveResults(threads []*ForumThread, filename string) error {
	if filename == "" {
		timestamp := time.Now().Format("20060102_150405")
		filename = fmt.Sprintf("forum_scrape_%s_%s.json", fs.platform, timestamp)
	}

	// Ensure results directory exists
	resultsDir := filepath.Join(".", "scraping_results")
	if err := os.MkdirAll(resultsDir, 0755); err != nil {
		return err
	}

	filepath := filepath.Join(resultsDir, filename)

	// Convert pointers to values for JSON serialization
	threadsData := make([]ForumThread, len(threads))
	for i, thread := range threads {
		threadsData[i] = *thread
	}

	totalPosts := 0
	for _, thread := range threadsData {
		totalPosts += len(thread.Posts)
	}

	results := map[string]interface{}{
		"forum_type":    fs.platform,
		"total_threads": len(threadsData),
		"total_posts":   totalPosts,
		"scraped_at":    time.Now().Format(time.RFC3339),
		"threads":       threadsData,
	}

	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		return err
	}

	if err := ioutil.WriteFile(filepath, data, 0644); err != nil {
		return err
	}

	fmt.Printf("💾 Results saved to: %s\n", filepath)
	return nil
}

// CLI interface
func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: go run forum_scraper.go <platform> <forum_url> <max_threads> [max_posts_per_thread]")
		fmt.Println("Example: go run forum_scraper.go phpbb https://forum.example.com/ 10 25")
		os.Exit(1)
	}

	platform := os.Args[1]
	forumURL := os.Args[2]
	maxThreads, err := strconv.Atoi(os.Args[3])
	if err != nil {
		log.Fatal("Invalid max_threads value")
	}

	maxPostsPerThread := 25
	if len(os.Args) > 4 {
		if val, err := strconv.Atoi(os.Args[4]); err == nil {
			maxPostsPerThread = val
		}
	}

	// Create scraper
	scraper := NewForumScraper(platform, 1.5) // 1.5 second delay

	// Scrape forum
	threads, err := scraper.scrapeForum(forumURL, maxThreads, maxPostsPerThread)
	if err != nil {
		log.Fatalf("❌ Scraping failed: %v", err)
	}

	// Save results
	if err := scraper.saveResults(threads, ""); err != nil {
		log.Fatalf("❌ Failed to save results: %v", err)
	}

	fmt.Printf("\n✅ Forum scraping completed successfully!\n")
	fmt.Printf("📊 Threads scraped: %d\n", len(threads))

	totalPosts := 0
	for _, thread := range threads {
		totalPosts += len(thread.Posts)
	}
	fmt.Printf("📊 Total posts: %d\n", totalPosts)
}
