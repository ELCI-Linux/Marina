#!/usr/bin/env node
/**
 * E-commerce Product Scraper - JavaScript/Node.js Implementation
 * 
 * Optimized for anti-bot evasion and dynamic content handling.
 * Features:
 * - Advanced anti-detection measures
 * - Dynamic content loading support
 * - Browser automation with stealth
 * - Product data extraction and analysis
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;
const path = require('path');

// Enable stealth plugin
puppeteer.use(StealthPlugin());

class ProductInfo {
    constructor(data) {
        this.url = data.url;
        this.title = data.title;
        this.price = data.price;
        this.originalPrice = data.originalPrice;
        this.discount = data.discount;
        this.description = data.description;
        this.availability = data.availability;
        this.rating = data.rating;
        this.reviewCount = data.reviewCount;
        this.images = data.images || [];
        this.features = data.features || [];
        this.category = data.category;
        this.brand = data.brand;
        this.sku = data.sku;
        this.scraped_at = new Date().toISOString();
    }
}

class EcommerceScraperJS {
    constructor(rootUrl, options = {}) {
        this.rootUrl = rootUrl;
        this.delay = options.delay_between_requests || 1500;
        this.headless = options.headless !== false;
        this.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36';
        this.visitedUrls = new Set();
        
        // Advanced anti-detection settings
        this.puppeteerOptions = {
            headless: this.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images', // For performance
            ],
            ignoreDefaultArgs: ['--enable-automation'],
            ignoreHTTPSErrors: true
        };

        // Platform-specific configurations for major e-commerce sites
        this.platformConfigs = {
            amazon: {
                selectors: {
                    product: '[data-component-type="s-search-result"]',
                    title: 'h2 a span, [data-cy="title-recipe-title"]',
                    price: '.a-price-whole, .a-offscreen',
                    originalPrice: '.a-price.a-text-price .a-offscreen',
                    rating: '.a-icon-alt',
                    reviewCount: 'a .a-size-base',
                    image: '.s-image',
                    availability: '.a-size-base-plus',
                    description: '#feature-bullets ul'
                },
                antiBot: {
                    waitSelectors: ['[data-component-type="s-search-result"]'],
                    avoidSelectors: ['.captcha', '#captchacharacters'],
                    scrollBehavior: 'slow'
                }
            },
            ebay: {
                selectors: {
                    product: '.s-item',
                    title: '.s-item__title',
                    price: '.s-item__price',
                    originalPrice: '.s-item__detail--original',
                    rating: '.reviews .stars',
                    reviewCount: '.reviews .review-count',
                    image: '.s-item__image img',
                    availability: '.s-item__availability',
                    description: '.s-item__subtitle'
                },
                antiBot: {
                    waitSelectors: ['.s-item'],
                    avoidSelectors: ['.captcha'],
                    scrollBehavior: 'medium'
                }
            },
            shopify: {
                selectors: {
                    product: '.product-item, .grid-item',
                    title: '.product-title, h3',
                    price: '.price, .money',
                    originalPrice: '.compare-at-price',
                    rating: '.rating, .stars',
                    reviewCount: '.review-count',
                    image: '.product-image img',
                    availability: '.availability',
                    description: '.product-description'
                },
                antiBot: {
                    waitSelectors: ['.product-item', '.grid-item'],
                    avoidSelectors: [],
                    scrollBehavior: 'fast'
                }
            },
            generic: {
                selectors: {
                    product: '.product, .item, [data-product]',
                    title: '.title, .name, h2, h3',
                    price: '.price, .cost, .amount',
                    originalPrice: '.original-price, .was-price',
                    rating: '.rating, .stars, .score',
                    reviewCount: '.reviews, .review-count',
                    image: '.image img, .photo img',
                    availability: '.availability, .stock',
                    description: '.description, .details'
                },
                antiBot: {
                    waitSelectors: ['.product', '.item'],
                    avoidSelectors: ['.captcha', '.robot-check'],
                    scrollBehavior: 'medium'
                }
            }
        };
    }

    async initializeBrowser() {
        console.log('🚀 Initializing stealth browser for e-commerce scraping...');
        
        this.browser = await puppeteer.launch(this.puppeteerOptions);
        this.page = await this.browser.newPage();
        
        // Advanced anti-detection measures
        await this.page.setUserAgent(this.userAgent);
        await this.page.setViewport({ 
            width: 1366 + Math.floor(Math.random() * 100), 
            height: 768 + Math.floor(Math.random() * 100) 
        });
        
        // Disable images for performance
        await this.page.setRequestInterception(true);
        this.page.on('request', (req) => {
            const resourceType = req.resourceType();
            if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
                req.abort();
            } else {
                req.continue();
            }
        });

        // Remove webdriver traces
        await this.page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock languages and plugins
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        });
        
        console.log('✅ Stealth browser initialized successfully');
    }

    detectPlatform(url) {
        const domain = new URL(url).hostname.toLowerCase();
        
        if (domain.includes('amazon')) return 'amazon';
        if (domain.includes('ebay')) return 'ebay';
        if (domain.includes('shopify') || domain.includes('myshopify')) return 'shopify';
        
        return 'generic';
    }

    async randomDelay(min = 1000, max = 3000) {
        const delay = Math.random() * (max - min) + min;
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    async humanizedScroll(target = null) {
        await this.page.evaluate((target) => {
            const scrollHeight = target || document.body.scrollHeight;
            const steps = 5 + Math.floor(Math.random() * 10);
            const stepSize = scrollHeight / steps;
            
            let currentPosition = 0;
            
            const scrollStep = () => {
                if (currentPosition < scrollHeight) {
                    currentPosition += stepSize + Math.random() * 100;
                    window.scrollTo(0, currentPosition);
                    setTimeout(scrollStep, 100 + Math.random() * 200);
                }
            };
            
            scrollStep();
        }, target);
        
        await this.randomDelay(2000, 4000);
    }

    async extractText(element, selector) {
        try {
            const targetElement = await element.$(selector);
            return targetElement ? await targetElement.evaluate(el => el.textContent.trim()) : null;
        } catch (error) {
            return null;
        }
    }

    async extractAttribute(element, selector, attribute) {
        try {
            const targetElement = await element.$(selector);
            return targetElement ? await targetElement.evaluate((el, attr) => el.getAttribute(attr), attribute) : null;
        } catch (error) {
            return null;
        }
    }

    extractPrice(priceText) {
        if (!priceText) return null;
        
        // Remove currency symbols and extract numbers
        const cleanPrice = priceText.replace(/[^\d.,]/g, '');
        const price = parseFloat(cleanPrice.replace(',', ''));
        
        return isNaN(price) ? null : price;
    }

    extractRating(ratingText) {
        if (!ratingText) return null;
        
        // Extract rating from various formats
        const ratingMatch = ratingText.match(/(\d+\.?\d*)\s*(?:out of|\/|\s)\s*[5510]?/i);
        if (ratingMatch) {
            return parseFloat(ratingMatch[1]);
        }
        
        // Count stars
        const starCount = (ratingText.match(/★/g) || []).length;
        return starCount > 0 ? starCount : null;
    }

    async scrapeProduct(productElement, config) {
        try {
            // Extract basic product information
            const title = await this.extractText(productElement, config.selectors.title);
            const priceText = await this.extractText(productElement, config.selectors.price);
            const originalPriceText = await this.extractText(productElement, config.selectors.originalPrice);
            const ratingText = await this.extractText(productElement, config.selectors.rating);
            const reviewCountText = await this.extractText(productElement, config.selectors.reviewCount);
            const availability = await this.extractText(productElement, config.selectors.availability);
            const description = await this.extractText(productElement, config.selectors.description);
            
            // Extract product URL
            const linkElement = await productElement.$('a');
            let productUrl = null;
            if (linkElement) {
                productUrl = await linkElement.evaluate(el => el.href);
                if (productUrl && !productUrl.startsWith('http')) {
                    productUrl = new URL(productUrl, this.rootUrl).href;
                }
            }
            
            // Extract image URL
            const imageUrl = await this.extractAttribute(productElement, config.selectors.image, 'src') ||
                            await this.extractAttribute(productElement, config.selectors.image, 'data-src');
            
            // Process extracted data
            const price = this.extractPrice(priceText);
            const originalPrice = this.extractPrice(originalPriceText);
            const rating = this.extractRating(ratingText);
            const reviewCount = reviewCountText ? parseInt(reviewCountText.replace(/\D/g, '')) : null;
            
            // Calculate discount if both prices available
            let discount = null;
            if (price && originalPrice && originalPrice > price) {
                discount = Math.round(((originalPrice - price) / originalPrice) * 100);
            }
            
            // Skip products without essential information
            if (!title || !price) {
                return null;
            }
            
            return new ProductInfo({
                url: productUrl || 'N/A',
                title,
                price,
                originalPrice,
                discount,
                description: description || 'No description available',
                availability: availability || 'Unknown',
                rating,
                reviewCount,
                images: imageUrl ? [imageUrl] : [],
                category: 'General', // Could be enhanced with category detection
                brand: null, // Could be enhanced with brand extraction
                sku: null
            });

        } catch (error) {
            console.error(`❌ Error scraping product: ${error.message}`);
            return null;
        }
    }

    async waitForProducts(config, timeout = 10000) {
        try {
            await this.page.waitForSelector(config.selectors.product, { timeout });
            return true;
        } catch (error) {
            console.warn(`⚠️ Products not found within ${timeout}ms`);
            return false;
        }
    }

    async checkForCaptcha(config) {
        for (const selector of config.antiBot.avoidSelectors) {
            const captchaElement = await this.page.$(selector);
            if (captchaElement) {
                console.warn('🚫 Captcha detected! Waiting before retry...');
                await this.randomDelay(10000, 20000);
                return true;
            }
        }
        return false;
    }

    async scrapeProductListing(listingUrl, maxProducts = 20) {
        if (!this.browser) {
            await this.initializeBrowser();
        }

        const products = [];
        
        try {
            console.log(`🛒 Scraping product listing: ${listingUrl}`);
            
            // Navigate to the listing page
            await this.page.goto(listingUrl, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            // Detect platform and get configuration
            const platform = this.detectPlatform(listingUrl);
            const config = this.platformConfigs[platform];
            console.log(`🎯 Detected platform: ${platform}`);
            
            // Check for captcha
            if (await this.checkForCaptcha(config)) {
                console.log('🔄 Retrying after captcha delay...');
                await this.page.reload({ waitUntil: 'networkidle0' });
            }
            
            // Wait for products to load
            const productsLoaded = await this.waitForProducts(config);
            if (!productsLoaded) {
                console.warn('⚠️ No products found on the page');
                return products;
            }

            // Scroll to load more products (for infinite scroll sites)
            await this.humanizedScroll();
            
            // Extract products
            const productElements = await this.page.$$(config.selectors.product);
            console.log(`📊 Found ${productElements.length} product elements`);

            for (let i = 0; i < Math.min(productElements.length, maxProducts); i++) {
                const product = await this.scrapeProduct(productElements[i], config);
                if (product) {
                    products.push(product);
                }
                
                // Random delay between products
                await this.randomDelay(500, 1500);
            }

            console.log(`✅ Successfully scraped ${products.length} products`);

        } catch (error) {
            console.error(`❌ Error scraping product listing: ${error.message}`);
        }

        return products;
    }

    async analyzeMarket(products) {
        if (products.length === 0) return {};

        const analysis = {
            total_products: products.length,
            price_analysis: {},
            rating_analysis: {},
            availability_analysis: {},
            discount_analysis: {}
        };

        // Price analysis
        const prices = products.filter(p => p.price).map(p => p.price);
        if (prices.length > 0) {
            analysis.price_analysis = {
                min_price: Math.min(...prices),
                max_price: Math.max(...prices),
                avg_price: prices.reduce((a, b) => a + b, 0) / prices.length,
                median_price: prices.sort((a, b) => a - b)[Math.floor(prices.length / 2)]
            };
        }

        // Rating analysis
        const ratings = products.filter(p => p.rating).map(p => p.rating);
        if (ratings.length > 0) {
            analysis.rating_analysis = {
                avg_rating: ratings.reduce((a, b) => a + b, 0) / ratings.length,
                min_rating: Math.min(...ratings),
                max_rating: Math.max(...ratings)
            };
        }

        // Availability analysis
        const availabilityStats = {};
        products.forEach(p => {
            const status = p.availability.toLowerCase();
            availabilityStats[status] = (availabilityStats[status] || 0) + 1;
        });
        analysis.availability_analysis = availabilityStats;

        // Discount analysis
        const discounts = products.filter(p => p.discount).map(p => p.discount);
        if (discounts.length > 0) {
            analysis.discount_analysis = {
                avg_discount: discounts.reduce((a, b) => a + b, 0) / discounts.length,
                max_discount: Math.max(...discounts),
                products_on_sale: discounts.length
            };
        }

        return analysis;
    }

    async saveResults(products, filename = null) {
        if (!filename) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            filename = `ecommerce_scrape_${timestamp}.json`;
        }

        const resultsDir = path.join(__dirname, 'scraping_results');
        
        try {
            await fs.mkdir(resultsDir, { recursive: true });
        } catch (error) {
            // Directory might already exist
        }

        const filepath = path.join(resultsDir, filename);
        
        // Generate market analysis
        const marketAnalysis = await this.analyzeMarket(products);
        
        const results = {
            total_products: products.length,
            market_analysis: marketAnalysis,
            scraped_at: new Date().toISOString(),
            products: products
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
    
    if (args.length < 2) {
        console.log('Usage: node ecommerce_scraper.js <listing_url> <max_products>');
        console.log('Example: node ecommerce_scraper.js https://www.amazon.com/s?k=laptops 20');
        process.exit(1);
    }

    const [listingUrl, maxProducts] = args;
    const scraper = new EcommerceScraperJS(listingUrl, { headless: true });

    try {
        const products = await scraper.scrapeProductListing(listingUrl, parseInt(maxProducts) || 20);
        await scraper.saveResults(products);
        
        console.log(`\n✅ E-commerce scraping completed successfully!`);
        console.log(`📊 Products scraped: ${products.length}`);
        
        if (products.length > 0) {
            const analysis = await scraper.analyzeMarket(products);
            console.log(`💰 Price range: $${analysis.price_analysis?.min_price} - $${analysis.price_analysis?.max_price}`);
            console.log(`⭐ Average rating: ${analysis.rating_analysis?.avg_rating?.toFixed(1) || 'N/A'}`);
        }
        
    } catch (error) {
        console.error(`❌ Scraping failed: ${error.message}`);
        process.exit(1);
    } finally {
        await scraper.close();
    }
}

// Export for use in other modules
module.exports = { EcommerceScraperJS, ProductInfo };

// Run CLI if this file is executed directly
if (require.main === module) {
    main();
}
