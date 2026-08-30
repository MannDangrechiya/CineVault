const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runW5CompletenessTests() {
  const results = {
    suite: 'Data Completeness & Ingestion Reliability (Phase W5)',
    passed: [],
    failed: [],
    logs: [],
  };

  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(`[Console Error] ${msg.text()}`);
    }
  });

  const failedRequests = [];
  page.on('response', response => {
    if (response.status() >= 400 && !response.url().includes('/api/auth/me')) {
      failedRequests.push(`[HTTP ${response.status()}] ${response.url()}`);
    }
  });

  try {
    // 1. Dev User Authentication
    console.log('--- Step 1: Dev User Login & Session Persistence ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.locator('button:has-text("Sign In as Dev User")').click();
    await page.waitForURL('**/dashboard', { timeout: 15000, waitUntil: 'domcontentloaded' });
    await page.waitForSelector('header:has-text("dev")', { timeout: 10000 });
    results.passed.push('dev_login_and_header_verified');
    console.log('✔ Dev user logged in successfully');

    // 2. Movies Catalog Navigation
    console.log('--- Step 2: Movies Catalog Exploration & Data Exposure ---');
    await page.goto('http://localhost:3000/movies', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    const moviesTitle = await page.locator('h1').innerText();
    console.log(`Movies header: ${moviesTitle}`);
    results.passed.push('movies_catalog_page_loaded');

    // 3. Series Catalog & Episodic Explorer
    console.log('--- Step 3: Series Catalog Navigation & Seasons Explorer ---');
    await page.goto('http://localhost:3000/series', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    results.passed.push('series_catalog_page_loaded');

    // Navigate to verified series with episodic tracking
    const seriesUrl = '/series/e898768a-a8c1-4534-82c6-8d7a1bacd341';
    await page.goto(`http://localhost:3000${seriesUrl}`, { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    const sTitle = await page.locator('h1').innerText();
    console.log(`Verified episodic series title: ${sTitle}`);

    const seasonsExplorer = page.locator('div:has-text("Seasons & Episodes")').first();
    await seasonsExplorer.waitFor({ timeout: 10000 });
    results.passed.push('episodic_series_seasons_explorer_verified');

    // 4. Watchlist & History Personal State Persistence
    console.log('--- Step 4: Personal Pages Integrity (Watchlist & History) ---');
    await page.goto('http://localhost:3000/watchlist', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    results.passed.push('watchlist_page_loaded');

    await page.goto('http://localhost:3000/history', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    results.passed.push('history_page_loaded');

    // 5. Oracle AI Discovery Interface
    console.log('--- Step 5: Oracle AI Interface ---');
    await page.goto('http://localhost:3000/oracle', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 10000 });
    results.passed.push('oracle_page_loaded');

    console.log('\n✅ All Phase W5 E2E checks passed successfully!');
  } catch (error) {
    console.error('❌ E2E Failure:', error);
    results.failed.push({ error: error.message, stack: error.stack });
    const screenshotPath = path.join(__dirname, 'screenshots', 'w5_failure.png');
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true });
  } finally {
    const resultsPath = path.join(__dirname, 'results_w5_completeness.json');
    fs.writeFileSync(resultsPath, JSON.stringify({ ...results, consoleErrors, failedRequests }, null, 2));
    await browser.close();
  }
}

runW5CompletenessTests().catch(console.error);
