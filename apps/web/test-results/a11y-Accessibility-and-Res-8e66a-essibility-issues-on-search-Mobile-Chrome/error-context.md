# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: a11y.spec.ts >> Accessibility and Responsive tests >> Should not have any automatically detectable accessibility issues on /search
- Location: tests\a11y.spec.ts:18:9

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - complementary [ref=e3]:
    - generic [ref=e11]:
      - generic [ref=e12]: CineVault
      - text: v2.0
    - navigation "Sidebar Navigation" [ref=e13]:
      - generic [ref=e14]: Navigation
      - link "Dashboard" [ref=e15] [cursor=pointer]:
        - /url: /dashboard
      - link "AI Oracle Oracle" [ref=e22] [cursor=pointer]:
        - /url: /oracle
        - generic [ref=e23]: AI Oracle
        - generic [ref=e27]: Oracle
      - link "Movies" [ref=e28] [cursor=pointer]:
        - /url: /movies
      - link "Series" [ref=e32] [cursor=pointer]:
        - /url: /series
      - link "Social & Match AI" [ref=e37] [cursor=pointer]:
        - /url: /social
        - generic [ref=e38]: Social & Match
        - generic [ref=e41]: AI
      - link "Watch Clubs Club" [ref=e42] [cursor=pointer]:
        - /url: /clubs
        - generic [ref=e43]: Watch Clubs
        - generic [ref=e49]: Club
      - link "Library" [ref=e50] [cursor=pointer]:
        - /url: /library
      - link "Watchlist" [ref=e54] [cursor=pointer]:
        - /url: /watchlist
      - link "History" [ref=e58] [cursor=pointer]:
        - /url: /history
      - link "Collections" [ref=e64] [cursor=pointer]:
        - /url: /collections
      - link "Import" [ref=e68] [cursor=pointer]:
        - /url: /import
      - link "Settings" [ref=e73] [cursor=pointer]:
        - /url: /settings
    - generic [ref=e78]:
      - generic [ref=e79]: CineVault Engine Active
      - paragraph [ref=e80]: OLED Cinematic Edition
  - generic [ref=e81]:
    - banner [ref=e82]:
      - generic [ref=e83]:
        - generic [ref=e84]: Vector AI Ready
        - link "Notifications" [ref=e87] [cursor=pointer]:
          - /url: /social
        - link "Sign In" [ref=e91] [cursor=pointer]:
          - /url: /login
    - main [ref=e96]:
      - generic [ref=e97]:
        - heading "404" [level=1] [ref=e98]
        - paragraph [ref=e99]: This page doesn't exist in the vault. It may have been moved or removed.
        - link "← Back to Dashboard" [ref=e100] [cursor=pointer]:
          - /url: /dashboard
  - navigation "Mobile Bottom Navigation" [ref=e101]:
    - link "Dashboard" [ref=e102] [cursor=pointer]:
      - /url: /dashboard
    - link "Oracle" [ref=e108] [cursor=pointer]:
      - /url: /oracle
    - link "Movies" [ref=e112] [cursor=pointer]:
      - /url: /movies
    - link "Social" [ref=e115] [cursor=pointer]:
      - /url: /social
    - link "Watchlist" [ref=e118] [cursor=pointer]:
      - /url: /watchlist
    - button "Open more menu" [ref=e121]: More
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import AxeBuilder from '@axe-core/playwright';
  3  | 
  4  | const testPages = [
  5  |   '/',
  6  |   '/dashboard',
  7  |   '/search',
  8  |   '/collections',
  9  |   '/clubs',
  10 |   '/social',
  11 |   '/history',
  12 |   '/friends',
  13 |   '/import',
  14 | ];
  15 | 
  16 | test.describe('Accessibility and Responsive tests', () => {
  17 |   for (const pagePath of testPages) {
  18 |     test(`Should not have any automatically detectable accessibility issues on ${pagePath}`, async ({ page }) => {
  19 |       // Navigate to the page
  20 |       await page.goto(pagePath);
  21 |       
  22 |       // Wait for network idle or main content to ensure page is loaded
> 23 |       await page.waitForLoadState('networkidle');
     |                  ^ Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
  24 | 
  25 |       // Analyze page with axe
  26 |       const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
  27 | 
  28 |       // Ensure no violations
  29 |       expect(accessibilityScanResults.violations).toEqual([]);
  30 |     });
  31 |   }
  32 | 
  33 |   test('Mobile drawer navigation should open properly', async ({ page, isMobile }) => {
  34 |     // Only run this test on mobile viewports
  35 |     test.skip(!isMobile, 'This test is only relevant for mobile devices');
  36 | 
  37 |     await page.goto('/dashboard');
  38 |     
  39 |     // Check if the drawer button is visible
  40 |     const moreButton = page.locator('button', { hasText: 'More' });
  41 |     if (await moreButton.isVisible()) {
  42 |       await moreButton.click();
  43 |       
  44 |       // Drawer should appear
  45 |       const dialog = page.locator('[role="dialog"]');
  46 |       await expect(dialog).toBeVisible();
  47 |       
  48 |       // Drawer should have proper ARIA attributes
  49 |       await expect(dialog).toHaveAttribute('aria-modal', 'true');
  50 |     }
  51 |   });
  52 | });
  53 | 
```