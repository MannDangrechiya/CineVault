const { test, expect } = require('@playwright/test');

test.describe('W9 Search Quality & Catalog Discovery', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the search/browse page (assuming /movies or /search)
    await page.goto('/movies');
  });

  test('should execute basic search and navigate to detail page', async ({ page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('Matrix');
    await searchInput.press('Enter');

    // Wait for search results
    const results = page.locator('.title-card, a[href*="/movies/"]');
    await expect(results.first()).toBeVisible({ timeout: 10000 });

    // Click the first result
    await results.first().click();

    // Verify it navigates to the movie detail page
    await expect(page).toHaveURL(/\/movies\/.+/);
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should handle zero results honestly', async ({ page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]');
    await searchInput.fill('xyzabc12349876nonsense');
    await searchInput.press('Enter');

    // Should display an honest empty state, e.g., "No results found"
    await expect(page.getByText(/no results|nothing found/i)).toBeVisible({ timeout: 10000 });
  });
});
