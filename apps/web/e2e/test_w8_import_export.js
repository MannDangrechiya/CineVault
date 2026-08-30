const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runW8ImportExportE2ETests() {
  const results = {
    suite: 'Import / Export & Personal Data Portability (Phase W8)',
    passed: [],
    failed: [],
    logs: [],
  };

  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const context = await browser.newContext({ acceptDownloads: true });
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
    // 1. Dev User Login & Session Persistence
    console.log('--- Step 1: Dev User Authentication ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.locator('button:has-text("Sign In as Dev User")').click();
    await page.waitForURL('**/dashboard', { timeout: 20000 });
    await page.waitForSelector('header', { timeout: 15000 });
    results.passed.push('dev_user_logged_in_and_dashboard_loaded');
    console.log('✔ Dev user authenticated');

    // 2. Navigate to Import Hub (/import)
    console.log('--- Step 2: Navigate to Import Wizard Hub ---');
    await page.goto('http://localhost:3000/import', { waitUntil: 'networkidle' });
    await page.waitForSelector('h1', { timeout: 15000 });
    const importH1 = await page.locator('h1').innerText();
    console.log(`Import Page Header: ${importH1}`);
    results.passed.push('import_page_loaded_successfully');

    // 3. Load Sample CSV Template & Parse Records
    console.log('--- Step 3: Load Template & Parse Structured Records ---');
    const loadCsvBtn = page.locator('button:has-text("Letterboxd CSV")');
    await loadCsvBtn.waitFor({ state: 'visible', timeout: 10000 });
    await loadCsvBtn.click();
    await page.waitForTimeout(400);

    const parseBtn = page.locator('button:has-text("Parse & Preview Matches")');
    await parseBtn.waitFor({ state: 'visible', timeout: 10000 });
    await parseBtn.click();
    console.log('✔ Clicked Parse & Preview Matches');

    // Wait for Step 2 (Preview & Disambiguation) to render
    await page.waitForSelector('text=Conflict Resolution Strategy', { timeout: 25000 });
    results.passed.push('step_2_preview_and_validation_rendered');
    console.log('✔ Step 2 Preview & Validation Summary rendered');

    // 4. Conflict Resolution Strategy Selector Buttons
    console.log('--- Step 4: Conflict Strategy Selection ---');
    const overwriteBtn = page.locator('button:has-text("Overwrite with Imported")');
    await overwriteBtn.waitFor({ state: 'visible', timeout: 10000 });
    await overwriteBtn.click();
    await page.waitForTimeout(300);
    results.passed.push('conflict_strategy_overwrite_selected');

    const keepExistingBtn = page.locator('button:has-text("Keep Existing Vault Data")');
    await keepExistingBtn.waitFor({ state: 'visible', timeout: 10000 });
    await keepExistingBtn.click();
    await page.waitForTimeout(300);
    results.passed.push('conflict_strategy_keep_existing_selected');
    console.log('✔ Conflict strategies selectable');

    // 5. Ingest & Apply Records into Vault
    console.log('--- Step 5: Ingest & Apply Records ---');
    const applyBtn = page.locator('button:has-text("Confirm & Ingest to Vault")');
    await applyBtn.waitFor({ state: 'visible', timeout: 10000 });
    await applyBtn.click();
    console.log('✔ Clicked Confirm & Ingest to Vault');

    // Wait for Step 3 (Ingest Complete Summary)
    await page.waitForSelector('text=Library Migration Successful!', { timeout: 25000 });
    results.passed.push('step_3_import_ingestion_complete');
    console.log('✔ Step 3 Import Complete Summary rendered');

    // 6. Settings Page Export Hub Verification (/settings)
    console.log('--- Step 6: Settings Data Export Verification ---');
    await page.goto('http://localhost:3000/settings', { waitUntil: 'networkidle' });
    await page.waitForSelector('text=Personal Data Portability & Export', { timeout: 15000 });
    results.passed.push('settings_export_hub_visible');
    console.log('✔ Personal Data Export section verified');

    // Check presence of the 4 export format download buttons
    const jsonBtn = page.locator('button:has-text("JSON v2.0")');
    const csvBtn = page.locator('button:has-text("CSV ZIP")');
    const xlsxBtn = page.locator('button:has-text("Excel (.xlsx)")');
    const mdBtn = page.locator('button:has-text("Markdown (.md)")');

    await jsonBtn.waitFor({ state: 'visible', timeout: 5000 });
    await csvBtn.waitFor({ state: 'visible', timeout: 5000 });
    await xlsxBtn.waitFor({ state: 'visible', timeout: 5000 });
    await mdBtn.waitFor({ state: 'visible', timeout: 5000 });
    results.passed.push('all_4_export_format_buttons_present');
    console.log('✔ All 4 export format buttons present');

    // Capture screenshot
    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
    const screenshotPath = path.join(screenshotDir, 'w8_import_export_hub.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`✔ Saved screenshot to ${screenshotPath}`);

  } catch (err) {
    console.error('Test run error:', err);
    results.failed.push({ error: err.message, stack: err.stack });
  } finally {
    await browser.close();
  }

  const resultsPath = path.join(__dirname, 'results_w8_import_export.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  console.log(`\n=== W8 E2E Test Results ===`);
  console.log(`Passed (${results.passed.length}):`, results.passed);
  console.log(`Failed (${results.failed.length}):`, results.failed);
  if (consoleErrors.length > 0) {
    console.log(`Console Errors (${consoleErrors.length}):`, consoleErrors.slice(0, 5));
  }
}

runW8ImportExportE2ETests().catch(console.error);
