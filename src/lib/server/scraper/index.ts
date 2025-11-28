import * as cheerio from 'cheerio';
import getSupabase from '../db';
import { extractCasinoInfo, extractWithCustomPrompt } from '../ai/extractor';

interface ScrapeResult {
	success: boolean;
	html?: string;
	cleanedHtml?: string;
	error?: string;
}

/**
 * Fetch HTML using Puppeteer with stealth mode to bypass bot detection
 */
export async function scrapeUrl(url: string): Promise<ScrapeResult> {
	let browser = null;

	try {
		// Dynamic import for puppeteer-extra and stealth plugin
		const puppeteer = await import('puppeteer-extra').then(m => m.default);
		const StealthPlugin = await import('puppeteer-extra-plugin-stealth').then(m => m.default);

		// Add stealth plugin to avoid detection
		puppeteer.use(StealthPlugin());

		// Launch browser
		browser = await puppeteer.launch({
			headless: true,
			args: [
				'--no-sandbox',
				'--disable-setuid-sandbox',
				'--disable-dev-shm-usage',
				'--disable-accelerated-2d-canvas',
				'--disable-gpu',
				'--window-size=1920,1080'
			]
		});

		const page = await browser.newPage();

		// Set viewport and user agent
		await page.setViewport({ width: 1920, height: 1080 });
		await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

		// Set extra headers
		await page.setExtraHTTPHeaders({
			'Accept-Language': 'en-US,en;q=0.9',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
		});

		// Navigate to URL
		await page.goto(url, {
			waitUntil: 'networkidle2',
			timeout: 30000
		});

		// Wait a bit for any dynamic content
		await new Promise(resolve => setTimeout(resolve, 2000));

		// Get page content
		const html = await page.content();
		const cleanedHtml = cleanHtmlForAI(html);

		return {
			success: true,
			html,
			cleanedHtml
		};
	} catch (error) {
		return {
			success: false,
			error: error instanceof Error ? error.message : 'Unknown error'
		};
	} finally {
		if (browser) {
			await browser.close();
		}
	}
}

/**
 * Clean HTML by removing scripts, styles, and other non-content elements
 * Prepares text for GPT processing
 */
function cleanHtmlForAI(html: string): string {
	const $ = cheerio.load(html);

	// Remove non-content elements
	$('script').remove();
	$('style').remove();
	$('noscript').remove();
	$('svg').remove();
	$('iframe').remove();
	$('link').remove();
	$('meta').remove();

	// Remove common non-content elements
	$('header nav').remove();
	$('[class*="cookie"]').remove();
	$('[class*="popup"]').remove();
	$('[class*="modal"]').remove();
	$('[class*="advertisement"]').remove();
	$('[class*="ad-"]').remove();
	$('[class*="banner"]').remove();
	$('[id*="cookie"]').remove();
	$('[id*="popup"]').remove();

	// Get text content with some structure preserved
	const bodyText = $('body').text();

	// Clean up whitespace
	return bodyText
		.replace(/\s+/g, ' ')
		.replace(/\n\s*\n/g, '\n')
		.trim()
		.slice(0, 50000); // Limit to ~50k chars for GPT
}

export interface ScrapeCasinoOptions {
	casinoId: string;
	configId?: string;
	saveRawHtml?: boolean;
}

export interface ScrapeCasinoResult {
	success: boolean;
	dataId?: string;
	error?: string;
}

/**
 * Scrape a casino based on its configuration
 */
export async function scrapeCasino(options: ScrapeCasinoOptions): Promise<ScrapeCasinoResult> {
	const { casinoId, configId, saveRawHtml = true } = options;
	const supabase = getSupabase();

	// Get casino details
	const { data: casino, error: casinoError } = await supabase
		.from('casinos')
		.select('*')
		.eq('id', casinoId)
		.single();

	if (casinoError || !casino) {
		return { success: false, error: 'Casino not found' };
	}

	// Get scrape configs if any
	let configsQuery = supabase
		.from('scrape_configs')
		.select('*')
		.eq('casino_id', casinoId)
		.eq('is_active', true);

	if (configId) {
		configsQuery = configsQuery.eq('id', configId);
	}

	const { data: configs } = await configsQuery;

	if (!configs || configs.length === 0) {
		// Default: scrape the base URL
		return scrapeSinglePage(casino.id, casino.base_url, saveRawHtml);
	}

	// Scrape each configured page
	const results: ScrapeCasinoResult[] = [];
	for (const config of configs) {
		const result = await scrapeSinglePage(
			casino.id,
			config.page_url,
			saveRawHtml,
			config
		);
		results.push(result);
	}

	const successCount = results.filter((r) => r.success).length;
	return {
		success: successCount > 0,
		error: successCount === 0 ? 'All pages failed to scrape' : undefined
	};
}

interface ScrapeConfig {
	id: string;
	custom_prompt: string | null;
	extraction_type: string;
}

async function scrapeSinglePage(
	casinoId: string,
	pageUrl: string,
	saveRawHtml: boolean,
	config?: ScrapeConfig
): Promise<ScrapeCasinoResult> {
	const supabase = getSupabase();

	// Create pending record
	const { data: dataRecord, error: insertError } = await supabase
		.from('scraped_data')
		.insert({
			casino_id: casinoId,
			config_id: config?.id || null,
			source_url: pageUrl,
			status: 'processing'
		})
		.select()
		.single();

	if (insertError || !dataRecord) {
		return { success: false, error: 'Failed to create scrape record' };
	}

	try {
		// Fetch the page HTML using Puppeteer
		const scrapeResult = await scrapeUrl(pageUrl);

		if (!scrapeResult.success || !scrapeResult.cleanedHtml) {
			await supabase
				.from('scraped_data')
				.update({
					status: 'failed',
					error_message: scrapeResult.error || 'Failed to fetch page'
				})
				.eq('id', dataRecord.id);

			return { success: false, error: scrapeResult.error };
		}

		// Extract data using AI (GPT)
		let extractedData: Record<string, unknown>;
		if (config?.custom_prompt) {
			extractedData = await extractWithCustomPrompt(
				scrapeResult.cleanedHtml,
				pageUrl,
				config.custom_prompt
			);
		} else {
			extractedData = await extractCasinoInfo(scrapeResult.cleanedHtml, pageUrl);
		}

		// Update record with results
		await supabase
			.from('scraped_data')
			.update({
				raw_html: saveRawHtml ? scrapeResult.html : null,
				extracted_data: extractedData,
				status: 'completed',
				processed_at: new Date().toISOString()
			})
			.eq('id', dataRecord.id);

		return { success: true, dataId: dataRecord.id };
	} catch (error) {
		await supabase
			.from('scraped_data')
			.update({
				status: 'failed',
				error_message: error instanceof Error ? error.message : 'Unknown error'
			})
			.eq('id', dataRecord.id);

		return {
			success: false,
			error: error instanceof Error ? error.message : 'Unknown error'
		};
	}
}

/**
 * Scrape all active casinos
 */
export async function scrapeAllCasinos(): Promise<{
	total: number;
	success: number;
	failed: number;
}> {
	const supabase = getSupabase();

	const { data: casinos } = await supabase
		.from('casinos')
		.select('id')
		.eq('is_active', true);

	if (!casinos || casinos.length === 0) {
		return { total: 0, success: 0, failed: 0 };
	}

	let success = 0;
	let failed = 0;

	for (const casino of casinos) {
		const result = await scrapeCasino({ casinoId: casino.id });
		if (result.success) {
			success++;
		} else {
			failed++;
		}
	}

	return { total: casinos.length, success, failed };
}
