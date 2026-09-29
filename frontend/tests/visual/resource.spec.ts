import { test, expect } from '@playwright/test';

test('reduced motion preserves the visualization surface', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.locator('#source-form')).toBeVisible();
  await expect(page.locator('.skip-link')).toHaveAttribute('href', '#analysis');
});
