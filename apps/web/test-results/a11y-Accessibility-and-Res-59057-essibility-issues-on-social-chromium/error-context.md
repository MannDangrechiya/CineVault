# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: a11y.spec.ts >> Accessibility and Responsive tests >> Should not have any automatically detectable accessibility issues on /social
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
- main [ref=e2]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - heading "Sign In to CineVault OS" [level=1] [ref=e12]
      - paragraph [ref=e13]: Access your personal media library, neural recommendations, and social inbox.
    - generic [ref=e14]:
      - generic [ref=e15]:
        - generic [ref=e16]: Quick One-Click Sign In
        - text: Instant Access
      - button "Sign In as Dev User dev@cinevault.local • Full Access Enter →" [ref=e19]:
        - generic [ref=e25]:
          - generic [ref=e26]: Sign In as Dev User
          - generic [ref=e27]: dev@cinevault.local • Full Access
        - text: Enter →
      - generic [ref=e28]:
        - button "Curator Profile curator@cinevault" [ref=e29]:
          - generic [ref=e33]:
            - generic [ref=e34]: Curator Profile
            - generic [ref=e35]: curator@cinevault
        - button "System Admin admin@cinevault" [ref=e36]:
          - generic [ref=e40]:
            - generic [ref=e41]: System Admin
            - generic [ref=e42]: admin@cinevault
    - generic [ref=e44]:
      - generic [ref=e45]:
        - text: Email Address
        - textbox "you@cinevault.local" [ref=e46]: dev@cinevault.local
      - generic [ref=e47]:
        - text: Password
        - textbox "••••••••" [ref=e48]: devpass
      - button "Sign In with Credentials" [ref=e49]
    - button "Enterprise Keycloak OIDC (PKCE S256)" [ref=e54]
    - generic [ref=e60]:
      - generic [ref=e61]: Encrypted Session BFF
      - link "Back to Catalog" [ref=e64] [cursor=pointer]:
        - /url: /
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