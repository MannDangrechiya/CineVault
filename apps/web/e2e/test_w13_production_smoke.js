const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runW13ProductionSmokeSuite() {
  const results = {
    suite: 'CineVault OS — Production Release Smoke Suite (Phase W13)',
    timestamp: new Date().toISOString(),
    passed: [],
    failed: [],
  };

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    acceptDownloads: true,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(35000);
  page.setDefaultNavigationTimeout(35000);

  const baseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';
  console.log(`[W13 SMOKE] Target Base URL: ${baseUrl}`);

  try {
    // 1. Homepage & Public Catalog Smoke
    console.log('--- 1. Public Homepage & Navigation ---');
    await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    const homeTitle = await page.title();
    console.log(`  -> Homepage Title: ${homeTitle}`);
    results.passed.push('homepage_loaded');

    // 2. Movies Catalog
    console.log('--- 2. Movies Catalog ---');
    await page.goto(`${baseUrl}/movies`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('movies_catalog_loaded');

    // 3. Series Catalog
    console.log('--- 3. Series Catalog ---');
    await page.goto(`${baseUrl}/series`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('series_catalog_loaded');

    // 4. Search Page
    console.log('--- 4. Search & Discovery ---');
    await page.goto(`${baseUrl}/search?q=Inception`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('search_page_loaded');

    // 5. Authentication (Dev User Session)
    console.log('--- 5. User Authentication ---');
    await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForTimeout(1000);
    const devLoginBtn = page.locator('button:has-text("Sign In as Dev User")');
    if (await devLoginBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await devLoginBtn.click();
      await page.waitForURL('**/dashboard', { timeout: 35000, waitUntil: 'domcontentloaded' });
      results.passed.push('auth_login_successful');
      console.log('  -> Dev User logged in successfully');
    } else {
      results.passed.push('login_page_loaded');
    }

    // 6. User Dashboard
    console.log('--- 6. Personal Vault Dashboard ---');
    await page.goto(`${baseUrl}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('dashboard_loaded');

    // 7. Library Page
    console.log('--- 7. Library Page ---');
    await page.goto(`${baseUrl}/library`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('library_loaded');

    // 8. Watchlist Page
    console.log('--- 8. Watchlist Page ---');
    await page.goto(`${baseUrl}/watchlist`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('watchlist_loaded');

    // 9. History Page
    console.log('--- 9. History Page ---');
    await page.goto(`${baseUrl}/history`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('history_loaded');

    // 10. Collections Page
    console.log('--- 10. Collections Hub ---');
    await page.goto(`${baseUrl}/collections`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('collections_loaded');

    // 11. Social Hub
    console.log('--- 11. Social Hub ---');
    await page.goto(`${baseUrl}/social`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('social_hub_loaded');

    // 12. Oracle AI Assistant
    console.log('--- 12. Oracle AI Assistant ---');
    await page.goto(`${baseUrl}/oracle`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('oracle_page_loaded');

    // 13. Import / Export Hub
    console.log('--- 13. Import Wizard & Data Portability ---');
    await page.goto(`${baseUrl}/import`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('import_wizard_loaded');

    // 14. Settings Page
    console.log('--- 14. Settings & Account Hub ---');
    await page.goto(`${baseUrl}/settings`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('settings_loaded');

    // 15. Responsive Viewport Check (Mobile 375px)
    console.log('--- 15. Responsive Mobile Layout (375px) ---');
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${baseUrl}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForSelector('main', { timeout: 15000 });
    results.passed.push('mobile_responsive_verified');

    console.log('\n======================================================');
    console.log(`[W13 SMOKE PASSED] ${results.passed.length} tests passed.`);
    console.log('======================================================\n');
  } catch (error) {
    console.error('[W13 SMOKE FAILED]:', error);
    results.failed.push({ error: error.message });
  } finally {
    await browser.close();
    const outputPath = path.join(__dirname, 'results_w13_smoke.json');
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  }
}

runW13ProductionSmokeSuite();
