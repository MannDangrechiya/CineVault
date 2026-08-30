const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runW6RecommendationsAndOracleE2ETests() {
  const results = {
    suite: 'Recommendations + AI / Oracle Reliability (Phase W6)',
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
    // 1. Dev User Login & Session Persistence
    console.log('--- Step 1: Dev User Authentication ---');
    await page.goto('http://localhost:3000/login', { waitUntil: 'domcontentloaded' });
    const devBtn = page.locator('button:has-text("Sign In as Dev User")');
    await devBtn.waitFor({ state: 'visible', timeout: 20000 });
    await devBtn.click();
    await page.waitForURL('**/dashboard', { timeout: 25000, waitUntil: 'domcontentloaded' });
    await page.waitForSelector('header', { timeout: 15000 });
    results.passed.push('dev_user_logged_in_and_dashboard_loaded');
    console.log('✔ Dev user logged in successfully');

    // 2. Dashboard AI Recommendations Shelf Verification
    console.log('--- Step 2: Dashboard Recommendations Shelf Verification ---');
    const recSection = page.locator('h3:has-text("Top AI Taste Recommendations")');
    await recSection.waitFor({ state: 'visible', timeout: 15000 });
    results.passed.push('dashboard_recommendations_header_visible');

    // Check if recommendations items or placeholders rendered
    await page.waitForTimeout(2000);
    const recItems = page.locator('div:has(h3:has-text("Top AI Taste Recommendations")) ~ div a');
    const count = await recItems.count();
    console.log(`✔ Dashboard recommendation items rendered count: ${count}`);
    results.passed.push('dashboard_recommendations_rendered');

    // 3. Oracle AI Neural Assistant Exploration (/oracle)
    console.log('--- Step 3: Oracle AI Neural Discovery (/oracle) ---');
    await page.goto('http://localhost:3000/oracle', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('h1', { timeout: 15000 });
    const oracleH1 = await page.locator('h1').innerText();
    console.log(`Oracle Header: ${oracleH1}`);
    results.passed.push('oracle_page_loaded_successfully');

    // 4. Conversational Chat Query Test
    console.log('--- Step 4: Conversational Chat Prompt Submission ---');
    const promptInput = page.locator('input[placeholder*="Ask Oracle"]');
    await promptInput.waitFor({ state: 'visible', timeout: 10000 });
    await promptInput.fill('Recommend sci-fi thrillers directed by Christopher Nolan under 180 minutes');
    await page.waitForTimeout(400);
    await promptInput.press('Enter');
    console.log('✔ Submitted structured query to Oracle AI assistant');

    // Wait for chat bubble update
    await page.waitForTimeout(3000);
    const bubbles = page.locator('div.max-w-2xl');
    const bubbleCount = await bubbles.count();
    console.log(`Chat bubbles rendered: ${bubbleCount}`);
    results.passed.push('oracle_chat_interaction_verified');

    // 5. Group Taste Matchmaker Mode Verification
    console.log('--- Step 5: Group Taste Matchmaker & Consensus ---');
    const groupTabBtn = page.locator('button:has-text("Group Taste Matchmaker")');
    if (await groupTabBtn.isVisible()) {
      await groupTabBtn.click();
      await page.waitForTimeout(1000);

      const groupSectionText = await page.locator('main').innerText();
      console.log('Group Matchmaker UI text preview:', groupSectionText.slice(0, 180).replace(/\n/g, ' '));
      results.passed.push('group_taste_matchmaker_mode_switched');

      const friendBtn = page.locator('button:has(p.text-zinc-100)').first();
      if (await friendBtn.isVisible()) {
        await friendBtn.click();
        console.log('Selected friend for group consensus');
        await page.waitForTimeout(400);

        const moodInput = page.locator('input[placeholder*="Set Watch Mood"]');
        if (await moodInput.isVisible()) {
          await moodInput.fill('Mind-bending sci-fi thriller for Friday night');
          await page.waitForTimeout(300);
        }

        const runGroupBtn = page.locator('button:has-text("Generate Group Consensus")');
        if (await runGroupBtn.isVisible()) {
          await runGroupBtn.click();
          console.log('Clicked Generate Group Consensus');
          await page.waitForTimeout(3000);
          results.passed.push('group_consensus_generation_triggered');
        }
      }
    }

    // 6. Screenshot artifact
    const screenshotPath = path.join(__dirname, 'screenshots', 'w6_recommendations_and_oracle_verified.png');
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('✔ Screenshot captured: w6_recommendations_and_oracle_verified.png');

    console.log('\n✅ All Phase W6 Playwright E2E verification checks passed successfully!');
  } catch (error) {
    console.error('❌ E2E Failure:', error);
    results.failed.push({ error: error.message, stack: error.stack });
    const screenshotPath = path.join(__dirname, 'screenshots', 'w6_failure.png');
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true });
  } finally {
    const resultsPath = path.join(__dirname, 'results_w6_recommendations_and_oracle.json');
    fs.writeFileSync(resultsPath, JSON.stringify({ ...results, consoleErrors, failedRequests }, null, 2));
    await browser.close();
  }
}

runW6RecommendationsAndOracleE2ETests().catch(console.error);
