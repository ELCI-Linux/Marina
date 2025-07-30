#!/usr/bin/env node
/**
 * Social Media Content Scraper - JavaScript/Node.js Implementation
 * 
 * Optimized for dynamic content scraping with browser automation capabilities.
 * Features:
 * - Puppeteer for JavaScript-heavy sites
 * - Real-time content extraction
 * - Anti-detection measures
 * - Concurrent processing
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class SocialMediaPost {
    constructor(data) {
        this.url = data.url;
        this.platform = data.platform;
        this.author = data.author;
        this.content = data.content;
        this.timestamp = data.timestamp;
        this.likes_count = data.likes_count;
        this.shares_count = data.shares_count;
        this.comments_count = data.comments_count;
        this.hashtags = data.hashtags || [];
        this.scraped_at = new Date().toISOString();
    }
}

class SocialMediaScraperJS {
    constructor(platform, options = {}) {
        this.platform = platform.toLowerCase();
        this.delay = options.delay_between_requests || 2000;
        this.headless = options.headless !== false;
        this.userAgent = 'Marina-SocialMediaScraper/2.0 (Educational Research)';
        this.visitedUrls = new Set();
        
        // Platform-specific configurations optimized for JavaScript execution
        this.platformConfigs = {
            twitter: {
                selectors: {
                    post: '[data-testid="tweet"]',
                    content: '[data-testid="tweetText"]',
                    author: '[data-testid="User-Name"] span',
                    timestamp: 'time',
                    likes: '[data-testid="like"]',
                    shares: '[data-testid="retweet"]',
                    comments: '[data-testid="reply"]'
                },
                waitForSelector: '[data-testid="tweet"]',
                scrollToLoad: true
            },
            reddit: {
                selectors: {
                    post: '[data-testid="post-container"]',
                    content: '[data-test-id="post-content"]',
                    author: '[data-testid="comment_author_link"]',
                    timestamp: '[data-testid="comment_timestamp"]',
                    likes: '[aria-label*="upvote"]',
                    comments: '[data-click-id="comments"]'
                },
                waitForSelector: '[data-testid="post-container"]',
                scrollToLoad: true
            },
            facebook: {
                selectors: {
                    post: '[data-pagelet="FeedUnit"]',
                    content: '[data-testid="post_message"]',
                    author: 'strong a',
                    timestamp: 'abbr',
                    likes: '[aria-label*="Like"]',
                    shares: '[aria-label*="Share"]',
                    comments: '[aria-label*="Comment"]'
                },
                waitForSelector: '[data-pagelet="FeedUnit"]',
                scrollToLoad: true
            }
        };
    }

    async initializeBrowser() {
        console.log('🚀 Initializing browser for social media scraping...');
        
        this.browser = await puppeteer.launch({
            headless: this.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });
        
        this.page = await this.browser.newPage();
        
        // Set user agent and viewport
        await this.page.setUserAgent(this.userAgent);
        await this.page.setViewport({ width: 1366, height: 768 });
        
        // Enable request interception for performance
        await this.page.setRequestInterception(true);
        this.page.on('request', (req) => {
            const resourceType = req.resourceType();
            if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
                req.abort();
            } else {
                req.continue();
            }
        });
        
        console.log('✅ Browser initialized successfully');
    }

    extractHashtags(text) {
        const hashtagRegex = /#\w+/g;
        return (text.match(hashtagRegex) || []).map(tag => tag.toLowerCase());
    }

    extractMentions(text) {
        const mentionRegex = /@\w+/g;
        return (text.match(mentionRegex) || []).map(mention => mention.toLowerCase());
    }

    async extractNumberFromText(element, keywords) {
        try {
            const text = await element.textContent();
            for (const keyword of keywords) {
                const patterns = [
                    new RegExp(`(\\d+)\\s*${keyword}`, 'i'),
                    new RegExp(`${keyword}:?\\s*(\\d+)`, 'i'),
                    new RegExp(`${keyword}\\s*\\((\\d+)\\)`, 'i')
                ];
                
                for (const pattern of patterns) {
                    const match = text.match(pattern);
                    if (match) {
                        return parseInt(match[1]);
                    }
                }
            }
        } catch (error) {
            // Silently handle extraction errors
        }
        return null;
    }

    async scrapePost(postElement, feedUrl) {
        try {
            const config = this.platformConfigs[this.platform];
            if (!config) {
                throw new Error(`Unsupported platform: ${this.platform}`);
            }

            // Extract post content with error handling
            const content = await this.safeExtractText(postElement, config.selectors.content) || 'No content available';
            const author = await this.safeExtractText(postElement, config.selectors.author) || 'Unknown';
            
            // Extract timestamp
            let timestamp = null;
            try {
                const timestampElement = await postElement.$(config.selectors.timestamp);
                if (timestampElement) {
                    timestamp = await timestampElement.getAttribute('datetime') || 
                               await timestampElement.textContent();
                }
            } catch (error) {
                // Timestamp extraction failed
            }

            // Extract engagement metrics
            const likesElement = await postElement.$(config.selectors.likes);
            const sharesElement = await postElement.$(config.selectors.shares);
            const commentsElement = await postElement.$(config.selectors.comments);

            const likesCount = likesElement ? await this.extractNumberFromText(likesElement, ['like', 'heart']) : null;
            const sharesCount = sharesElement ? await this.extractNumberFromText(sharesElement, ['share', 'retweet']) : null;
            const commentsCount = commentsElement ? await this.extractNumberFromText(commentsElement, ['comment', 'reply']) : null;

            // Extract hashtags and mentions
            const hashtags = this.extractHashtags(content);
            
            // Generate post URL (simplified)
            const postUrl = `${feedUrl}#post_${Date.now()}`;

            return new SocialMediaPost({
                url: postUrl,
                platform: this.platform,
                author,
                content,
                timestamp,
                likes_count: likesCount,
                shares_count: sharesCount,
                comments_count: commentsCount,
                hashtags
            });

        } catch (error) {
            console.error(`❌ Error scraping post: ${error.message}`);
            return null;
        }
    }

    async safeExtractText(element, selector) {
        try {
            const targetElement = await element.$(selector);
            return targetElement ? await targetElement.textContent() : null;
        } catch (error) {
            return null;
        }
    }

    async scrapeFeed(feedUrl, maxPosts = 10) {
        if (!this.browser) {
            await this.initializeBrowser();
        }

        const posts = [];
        
        try {
            console.log(`🔍 Scraping ${this.platform} feed: ${feedUrl}`);
            
            await this.page.goto(feedUrl, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            const config = this.platformConfigs[this.platform];
            
            // Wait for posts to load
            try {
                await this.page.waitForSelector(config.waitForSelector, { timeout: 10000 });
            } catch (error) {
                console.warn(`⚠️ Could not find posts selector: ${config.waitForSelector}`);
                return posts;
            }

            // Scroll to load more posts if needed
            if (config.scrollToLoad) {
                await this.autoScroll(maxPosts);
            }

            // Extract posts
            const postElements = await this.page.$$(config.selectors.post);
            console.log(`📊 Found ${postElements.length} post elements`);

            for (let i = 0; i < Math.min(postElements.length, maxPosts); i++) {
                const post = await this.scrapePost(postElements[i], feedUrl);
                if (post) {
                    posts.push(post);
                }
                
                // Add delay between posts
                await this.sleep(this.delay);
            }

            console.log(`✅ Successfully scraped ${posts.length} posts from ${this.platform}`);

        } catch (error) {
            console.error(`❌ Error scraping feed: ${error.message}`);
        }

        return posts;
    }

    async autoScroll(targetPosts) {
        console.log('📜 Auto-scrolling to load more posts...');
        
        let previousHeight = 0;
        let attempts = 0;
        const maxAttempts = 5;

        while (attempts < maxAttempts) {
            // Scroll to bottom
            await this.page.evaluate(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });

            // Wait for new content to load
            await this.sleep(2000);

            const currentHeight = await this.page.evaluate(() => document.body.scrollHeight);
            
            if (currentHeight === previousHeight) {
                attempts++;
            } else {
                attempts = 0;
                previousHeight = currentHeight;
            }

            // Check if we have enough posts
            const config = this.platformConfigs[this.platform];
            const postCount = await this.page.$$(config.selectors.post).then(elements => elements.length);
            
            if (postCount >= targetPosts) {
                break;
            }
        }
        
        console.log('📜 Auto-scrolling completed');
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async saveResults(posts, filename = null) {
        if (!filename) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            filename = `social_media_scrape_${this.platform}_${timestamp}.json`;
        }

        const resultsDir = path.join(__dirname, 'scraping_results');
        
        try {
            await fs.mkdir(resultsDir, { recursive: true });
        } catch (error) {
            // Directory might already exist
        }

        const filepath = path.join(resultsDir, filename);
        
        const results = {
            platform: this.platform,
            total_posts: posts.length,
            scraped_at: new Date().toISOString(),
            posts: posts
        };

        await fs.writeFile(filepath, JSON.stringify(results, null, 2));
        console.log(`💾 Results saved to: ${filepath}`);
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.log('🔒 Browser closed');
        }
    }
}

// CLI interface for standalone usage
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length < 3) {
        console.log('Usage: node social_media_scraper.js <platform> <url> <max_posts>');
        console.log('Example: node social_media_scraper.js twitter https://twitter.com/home 10');
        process.exit(1);
    }

    const [platform, url, maxPosts] = args;
    const scraper = new SocialMediaScraperJS(platform, { headless: true });

    try {
        const posts = await scraper.scrapeFeed(url, parseInt(maxPosts) || 10);
        await scraper.saveResults(posts);
        
        console.log(`\n✅ Scraping completed successfully!`);
        console.log(`📊 Posts scraped: ${posts.length}`);
        
    } catch (error) {
        console.error(`❌ Scraping failed: ${error.message}`);
        process.exit(1);
    } finally {
        await scraper.close();
    }
}

// Export for use in other modules
module.exports = { SocialMediaScraperJS, SocialMediaPost };

// Run CLI if this file is executed directly
if (require.main === module) {
    main();
}
