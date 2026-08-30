import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const testPages = [
  '/',
  '/dashboard',
  '/search',
  '/collections',
  '/clubs',
  '/social',
  '/history',
  '/friends',
  '/import',
];

test.describe('Accessibility and Responsive tests', () => {
  for (const pagePath of testPages) {
    test(`Should not have any automatically detectable accessibility issues on ${pagePath}`, async ({ page }) => {
      // Navigate to the page
      await page.goto(pagePath);
      
      // Wait for network idle or main content to ensure page is loaded
      await page.waitForLoadState('networkidle');

      // Analyze page with axe
      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

      // Ensure no violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }

  test('Mobile drawer navigation should open properly', async ({ page, isMobile }) => {
    // Only run this test on mobile viewports
    test.skip(!isMobile, 'This test is only relevant for mobile devices');

    await page.goto('/dashboard');
    
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
