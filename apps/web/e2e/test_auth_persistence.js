const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runAuthTests() {
  const results = {
    suite: 'Public & Auth',
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
    if (response.status() >= 400 && !response.url().includes('local-login') && !response.url().includes('/api/auth/me')) {
      failedRequests.push(`[HTTP ${response.status()}] ${response.url()}`);
    }
  });

  try {
    console.log('--- Test 1: Invalid Password Error ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    
    // Type bad credentials
    await page.locator('input[type="email"]').fill('dev@cinevault.local');
    await page.locator('input[type="password"]').fill('incorrect_password');
    await page.locator('button[type="submit"]').click();

    // Expect error message in UI
    await page.waitForSelector('text=Authentication Alert', { timeout: 5000 });
    const alertMsg = await page.getByText('Authentication Alert').isVisible();
    const alertBody = await page.getByText('Invalid email or password').isVisible();
    console.log('Found error alert in UI:', { alertMsg, alertBody });
    if (alertMsg && alertBody) {
      results.passed.push('Invalid password shows visible error alert in UI');
    } else {
      throw new Error('Authentication alert was not displayed properly');
    }

    console.log('--- Test 2: Valid Login as dev@cinevault.local ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    // Click Quick One-Click Dev Sign In
    await page.locator('button:has-text("Sign In as Dev User")').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    
    await page.waitForSelector('header:has-text("dev")', { timeout: 10000 });
    const devHeader = await page.locator('header').innerText();
    console.log('Logged in as dev, header verified:', devHeader.replace(/\n/g, ' '));
    results.passed.push('Login as dev@cinevault.local successful and header renders dev username');

    console.log('--- Test 3: Session Persistence on Reload ---');
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForURL('**/dashboard', { timeout: 5000 });
    await page.waitForSelector('header:has-text("dev")', { timeout: 10000 });
    const devHeaderAfterReload = await page.locator('header').innerText();
    console.log('Session persisted after reload, header:', devHeaderAfterReload.replace(/\n/g, ' '));
    results.passed.push('Session persistence verified on page reload');

    console.log('--- Test 4: Logout ---');
    await page.locator('button[title="Sign Out"]').click();
    await page.waitForURL('**/login**', { timeout: 10000 });
    console.log('Logged out successfully, landed on:', page.url());
    results.passed.push('Logout button cleanly terminates session and returns to /login');

    console.log('--- Test 5: Valid Login as curator@cinevault.local ---');
    await page.locator('button:has-text("Curator Profile")').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForSelector('header:has-text("curator")', { timeout: 10000 });
    const curatorHeader = await page.locator('header').innerText();
    console.log('Logged in as curator, header verified:', curatorHeader.replace(/\n/g, ' '));
    results.passed.push('Login as curator@cinevault.local successful and header renders curator username');

    console.log('--- Test 6: Curator Session Persistence ---');
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForURL('**/dashboard', { timeout: 5000 });
    await page.waitForSelector('header:has-text("curator")', { timeout: 10000 });
    const curatorHeaderReload = await page.locator('header').innerText();
    console.log('Curator session persisted after reload');
    results.passed.push('Curator session persistence verified on page reload');

  } catch (err) {
    console.error('Auth test failed:', err);
    results.failed.push({ error: err.message, stack: err.stack });
    await page.screenshot({ path: path.join(__dirname, 'screenshots', 'auth_failure.png'), fullPage: true });
  } finally {
    await browser.close();
  }

  results.consoleErrors = consoleErrors;
  results.failedRequests = failedRequests;

  console.log('\n=== AUTH TEST SUMMARY ===');
  console.log('Passed:', results.passed);
  console.log('Failed:', results.failed);
  console.log('Console Errors:', consoleErrors);
  console.log('Failed Requests:', failedRequests);

  fs.writeFileSync(
    path.join(__dirname, 'results_auth.json'),
    JSON.stringify(results, null, 2)
  );
}

runAuthTests();
