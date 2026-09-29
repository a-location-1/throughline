import { test, expect } from '@playwright/test';

test('landing workflow exposes keyboard-accessible source controls', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /see the shape/i })).toBeVisible();
  await expect(page.getByLabel('Play URL')).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toBeVisible();
  await expect(page.getByText(/primarily English-language/i)).toBeVisible();
});

test('mobile layout keeps the source action visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: /analyze play/i })).toBeVisible();
  await expect(page.locator('body')).toHaveCSS('overflow-x', 'visible');
});
