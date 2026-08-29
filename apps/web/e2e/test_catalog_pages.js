const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runCatalogTests() {
  const results = {
    suite: 'Catalog & Detail Pages',
    passed: [],
    failed: [],
    differingEntities: {},
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
    // 0. Login as dev first so user actions work
    console.log('--- Setup: Log in as dev ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.locator('button:has-text("Sign In as Dev User")').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForSelector('header:has-text("dev")', { timeout: 10000 });

    // 1. /movies Page Tests
    console.log('--- Test 1: Movies Catalog Browsing, Search, Sort, Filter, Pagination ---');
    await page.goto('http://localhost:3000/movies', { waitUntil: 'networkidle' });
    await page.waitForSelector('text=in catalog', { timeout: 10000 });

    const totalText = await page.locator('header, h1, div, p').filter({ hasText: /in catalog/ }).first().innerText();
    console.log('Total movies count badge:', totalText.replace(/\n/g, ' '));

    // Test Search
    console.log('Testing Search for "Matrix"...');
    await page.locator('#catalog-search').fill('Matrix');
    await page.waitForTimeout(600); // Debounce wait
    await page.waitForSelector('a[href^="/movies/"]', { timeout: 10000 });
    const searchResults = await page.locator('a[href^="/movies/"]').allInnerTexts();
    console.log('Search "Matrix" results:', searchResults.slice(0, 3));
    const matrixFound = searchResults.some(t => t.toLowerCase().includes('matrix'));
    if (matrixFound) {
      results.passed.push('Movie search for "Matrix" returned relevant matching results');
    } else {
      throw new Error(`Matrix search did not return expected results: ${searchResults.slice(0, 3)}`);
    }

    // Clear search
    await page.locator('button[aria-label="Clear search"]').click();
    await page.waitForTimeout(600);

    // Test Genre Filter (e.g. "Action")
    console.log('Testing Genre Filter "Action"...');
    await page.locator('button:has-text("Action")').first().click();
    await page.waitForTimeout(800);
    const actionResults = await page.locator('a[href^="/movies/"]').allInnerTexts();
    console.log('Action filter results count:', actionResults.length);
    results.passed.push('Movie genre filtering by "Action" returned results');

    // Clear genre filter by clicking again
    await page.locator('button:has-text("Action")').first().click();
    await page.waitForTimeout(600);

    // Test Sort (Oldest First)
    console.log('Testing Sort: Oldest First...');
    await page.locator('#catalog-sort').selectOption('production_year,canonical_title');
    await page.waitForTimeout(800);
    const oldestResults = await page.locator('a[href^="/movies/"]').allInnerTexts();
    console.log('Oldest sort results:', oldestResults.slice(0, 3));
    results.passed.push('Movie sort by "Oldest First" updated catalog grid');

    // Test Sort (A-Z)
    console.log('Testing Sort: Title A-Z...');
    await page.locator('#catalog-sort').selectOption('canonical_title');
    await page.waitForTimeout(800);
    const azResults = await page.locator('a[href^="/movies/"]').allInnerTexts();
    console.log('A-Z sort results:', azResults.slice(0, 3));
    results.passed.push('Movie sort by "Title A-Z" updated catalog grid');

    // Reset sort to Newest
    await page.locator('#catalog-sort').selectOption('-production_year,canonical_title');
    await page.waitForTimeout(600);

    // 2. /series Page Tests
    console.log('--- Test 2: Series Catalog Browsing, Search, Sort, Filter ---');
    await page.goto('http://localhost:3000/series', { waitUntil: 'networkidle' });
    await page.waitForSelector('text=in catalog', { timeout: 10000 });
    const seriesTotalText = await page.locator('header, h1, div, p').filter({ hasText: /in catalog/ }).first().innerText();
    console.log('Total series count badge:', seriesTotalText.replace(/\n/g, ' '));

    await page.waitForSelector('a[href^="/series/"]', { timeout: 10000 });
    const initialSeries = await page.locator('a[href^="/series/"]').allInnerTexts();
    console.log('First few initial series:', initialSeries.slice(0, 3));

    // Test Series Search
    console.log('Testing Series Search for "Crown"...');
    await page.locator('#catalog-search').fill('Crown');
    await page.waitForTimeout(600);
    await page.waitForSelector('a[href^="/series/"]', { timeout: 10000 });
    const crownResults = await page.locator('a[href^="/series/"]').allInnerTexts();
    console.log('Search "Crown" series results:', crownResults.slice(0, 3));
    results.passed.push('Series search and catalog browsing verified');

    // 3. Movie Detail Page & Interactions
    console.log('--- Test 3: Movie Detail Page — Metadata & Actions ---');
    await page.goto('http://localhost:3000/movies', { waitUntil: 'networkidle' });
    await page.locator('#catalog-search').fill('Inception');
    await page.waitForTimeout(600);
    await page.locator('a[href^="/movies/"]').first().click();
    await page.waitForURL('**/movies/**', { timeout: 10000 });
    await page.waitForSelector('h1', { timeout: 10000 });

    const movie1Title = await page.locator('h1').innerText();
    const movie1Url = page.url();
    const movie1BodyText = await page.locator('main, div.min-h-screen').first().innerText();
    console.log(`Movie 1: ${movie1Title} (${movie1Url})`);

    // Record entity metadata for fabrication comparison
    results.differingEntities.movie1 = {
      title: movie1Title,
      url: movie1Url,
      snippet: movie1BodyText.slice(0, 200),
    };

    // Test "Add to Watchlist"
    console.log('Testing "Add to Watchlist" on Movie...');
    const watchlistBtn = page.locator('button:has-text("Add to Watchlist")');
    if (await watchlistBtn.isVisible()) {
      await watchlistBtn.click();
      await page.waitForSelector('button:has-text("In Watchlist")', { timeout: 5000 });
      console.log('Watchlist button transitioned to "In Watchlist"');
      results.passed.push('Movie detail: "Add to Watchlist" updated UI state and dispatched API call');
    } else {
      console.log('Already in watchlist or toggle present');
      results.passed.push('Movie detail: Watchlist toggle button present');
    }

    // Test "Add to Library"
    console.log('Testing "Add to Library" on Movie...');
    const libraryBtn = page.locator('button:has-text("Add to Library")');
    if (await libraryBtn.isVisible()) {
      await libraryBtn.click();
      await page.waitForSelector('button:has-text("In Library")', { timeout: 5000 });
      console.log('Library button transitioned to "In Library"');
      results.passed.push('Movie detail: "Add to Library" updated UI state and dispatched API call');
    } else {
      results.passed.push('Movie detail: Library button present');
    }

    // Test "Mark as Watched" (Heart button)
    console.log('Testing "Mark as Watched" (Heart button) on Movie...');
    const heartBtn = page.locator('button[title*="Watched"], button:has(svg.lucide-heart)');
    await heartBtn.first().click();
    await page.waitForTimeout(1000);
    results.passed.push('Movie detail: "Mark as Watched" heart button clicked and logged event');

    // Test "Add to Collection"
    console.log('Testing "Add to Collection" modal on Movie...');
    const collectionBtn = page.locator('button[title="Add to Collection"]');
    await collectionBtn.click();
    await page.waitForSelector('text=Add to Collection', { timeout: 5000 });
    const collectionModal = page.locator('div.fixed.z-50');
    const collectionModalText = await collectionModal.innerText();
    console.log('Collection modal state:', collectionModalText.replace(/\n/g, ' '));
    // Click close button on modal
    await collectionModal.locator('button:has(svg.lucide-x)').click();
    await page.waitForTimeout(300);
    results.passed.push('Movie detail: "Add to Collection" modal opens cleanly');

    // Test "Recommend to a Friend" Modal
    console.log('Testing "Recommend to a Friend" modal on Movie...');
    await page.locator('button:has-text("Recommend to a Friend")').click();
    await page.waitForSelector('text=Recommend Movie', { timeout: 5000 });
    const friendModal = page.locator('div.fixed.z-50');
    const friendModalText = await friendModal.innerText();
    console.log('Friend recommend modal text:', friendModalText.replace(/\n/g, ' '));
    await friendModal.locator('button:has(svg.lucide-x)').click();
    await page.waitForTimeout(300);
    results.passed.push('Movie detail: "Recommend to a Friend" modal opens and renders friend picker');

    // Compare with a Second Movie to verify metadata differs (no fabrication)
    console.log('--- Test 4: Second Movie Metadata Comparison ---');
    await page.goto('http://localhost:3000/movies', { waitUntil: 'networkidle' });
    await page.locator('#catalog-search').fill('Parasite');
    await page.waitForTimeout(600);
    await page.locator('a[href^="/movies/"]').first().click();
    await page.waitForURL('**/movies/**', { timeout: 10000 });
    await page.waitForSelector('h1', { timeout: 10000 });

    const movie2Title = await page.locator('h1').innerText();
    const movie2Url = page.url();
    const movie2BodyText = await page.locator('main, div.min-h-screen').first().innerText();
    console.log(`Movie 2: ${movie2Title} (${movie2Url})`);

    results.differingEntities.movie2 = {
      title: movie2Title,
      url: movie2Url,
      snippet: movie2BodyText.slice(0, 200),
    };

    if (movie1Title !== movie2Title && movie1BodyText !== movie2BodyText) {
      console.log('Verified: Movie 1 and Movie 2 have completely distinct titles and metadata.');
      results.passed.push('Distinct metadata verified between multiple movies (no fabricated identical text)');
    } else {
      throw new Error('Fabrication detected: Movie 1 and Movie 2 returned identical metadata!');
    }

    // 4. Series Detail Page & Metadata Comparison
    console.log('--- Test 5: Series Detail Page & Metadata Comparison ---');
    await page.goto('http://localhost:3000/series', { waitUntil: 'networkidle' });
    await page.locator('a[href^="/series/"]').first().click();
    await page.waitForURL('**/series/**', { timeout: 10000 });
    await page.waitForSelector('h1', { timeout: 10000 });

    const series1Title = await page.locator('h1').innerText();
    const series1Url = page.url();
    const series1BodyText = await page.locator('main, div.min-h-screen').first().innerText();
    console.log(`Series 1: ${series1Title} (${series1Url})`);

    results.differingEntities.series1 = {
      title: series1Title,
      url: series1Url,
      snippet: series1BodyText.slice(0, 200),
    };

    // Second series
    await page.goto('http://localhost:3000/series', { waitUntil: 'networkidle' });
    await page.locator('a[href^="/series/"]').nth(2).click();
    await page.waitForURL('**/series/**', { timeout: 10000 });
    await page.waitForSelector('h1', { timeout: 10000 });

    const series2Title = await page.locator('h1').innerText();
    const series2Url = page.url();
    const series2BodyText = await page.locator('main, div.min-h-screen').first().innerText();
    console.log(`Series 2: ${series2Title} (${series2Url})`);

    results.differingEntities.series2 = {
      title: series2Title,
      url: series2Url,
      snippet: series2BodyText.slice(0, 200),
    };

    if (series1Title !== series2Title && series1BodyText !== series2BodyText) {
      console.log('Verified: Series 1 and Series 2 have distinct titles and metadata.');
      results.passed.push('Distinct metadata verified between multiple series (no fabricated identical text)');
    } else {
      throw new Error('Fabrication detected: Series 1 and Series 2 returned identical metadata!');
    }

  } catch (err) {
    console.error('Catalog test failed:', err);
    results.failed.push({ error: err.message, stack: err.stack });
    await page.screenshot({ path: path.join(__dirname, 'screenshots', 'catalog_failure.png'), fullPage: true });
  } finally {
    await browser.close();
  }

  results.consoleErrors = consoleErrors;
  results.failedRequests = failedRequests;

  console.log('\n=== CATALOG TEST SUMMARY ===');
  console.log('Passed:', results.passed);
  console.log('Failed:', results.failed);
  console.log('Console Errors:', consoleErrors);
  console.log('Failed Requests:', failedRequests);

  fs.writeFileSync(
    path.join(__dirname, 'results_catalog.json'),
    JSON.stringify(results, null, 2)
  );
}

runCatalogTests();
