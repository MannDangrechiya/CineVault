import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const testPages = [
  '/',
  '/login',
  '/dashboard',
  '/movies',
  '/series',
  '/search',
  '/library',
  '/watchlist',
  '/history',
  '/collections',
  '/clubs',
  '/social',
  '/friends',
  '/import',
  '/oracle',
  '/settings',
  '/movies/MOV-000001',
  '/series/TV-000001',
  '/collections/col_criterion_essentials',
  '/clubs/cinephiles-guild',
  '/pick/weekend-movie-night',
];

test.describe('Accessibility and Responsive tests', () => {
  for (const pagePath of testPages) {
    test(`Should not have any automatically detectable accessibility issues on ${pagePath}`, async ({ page }) => {
      // Navigate to the page
      await page.goto(pagePath, { waitUntil: 'domcontentloaded' });
      
      // Wait for content container
      await page.waitForSelector('main, [role="main"], body', { state: 'attached' });
      await page.waitForTimeout(500);

      // Analyze page with axe for WCAG AA compliance, excluding Next.js dev overlay
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .exclude('nextjs-portal')
        .exclude('[data-nextjs-portal]')
        .analyze();

      // Ensure no violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }

  test('Mobile drawer navigation should open properly', async ({ page, isMobile }) => {
    // Only run this test on mobile viewports
    test.skip(!isMobile, 'This test is only relevant for mobile devices');

    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    
    // Check if the drawer button is visible
    const moreButton = page.locator('button', { hasText: 'More' });
    if (await moreButton.isVisible()) {
      await moreButton.click();
      
      // Drawer should appear
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();
      
      // Drawer should have proper ARIA attributes
      await expect(dialog).toHaveAttribute('aria-modal', 'true');
    }
  });
});
