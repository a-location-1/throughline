import { test, expect } from '@playwright/test';

test('landing workflow exposes keyboard-accessible source controls', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /see the shape/i })).toBeVisible();
  await expect(page.getByLabel('Play URL')).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: /skip to analysis/i })).toBeFocused();
  await expect(page.getByText(/primarily English-language/i)).toBeVisible();
});

test('mobile layout keeps the source action visible without horizontal overflow', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: /analyze play/i })).toBeVisible();
  const overflowed = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflowed).toBeFalsy();
});
