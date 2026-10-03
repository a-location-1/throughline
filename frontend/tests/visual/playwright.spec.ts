import { test, expect } from '@playwright/test';

function buildPdfFromText(text: string): Buffer {
  const lines = text.split('\n');
  const content = lines.map((line, index) => {
    const y = 780 - index * 18;
    return `BT /F1 12 Tf 72 ${y} Td (${line.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)')}) Tj ET`;
  }).join('\n');

  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${content.length + 2} >>\nstream\n${content}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ];

  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  for (let index = 0; index < objects.length; index += 1) {
    offsets.push(Buffer.byteLength(pdf, 'binary'));
    pdf += `${index + 1} 0 obj\n${objects[index]}\nendobj\n`;
  }

  const xrefStart = Buffer.byteLength(pdf, 'binary');
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let index = 1; index <= objects.length; index += 1) {
    pdf += `${String(offsets[index]).padStart(10, '0')} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF`;

  return Buffer.from(pdf, 'binary');
}

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

test('submitting a real Gutenberg URL creates a working analysis', async ({ page }) => {
  const url = 'https://www.gutenberg.org/cache/epub/1513/pg1513.txt';

  await page.goto('/');
  await page.getByLabel('Play URL').fill(url);
  await page.getByRole('button', { name: /analyze play/i }).click();

  await expect(page.locator('#analysis')).toBeVisible({ timeout: 60000 });
  await expect(page.locator('#result-status')).toContainText(/analysis ready|retrieving source|extracting text|identifying scenes and speakers/i, { timeout: 60000 });
  await expect(page.locator('#results-heading')).not.toHaveText('', { timeout: 60000 });
  await expect(page.locator('#result-meta')).toContainText(/acts|scenes|characters/i, { timeout: 60000 });
});

test('uploading a generated PDF completes a real end-to-end analysis', async ({ page }) => {
  const pdfText = [
    'ACT I',
    'SCENE I',
    'ALICE',
    'Welcome.',
    'SCENE II',
    'BOB',
    'I have arrived.',
    'ACT II',
    'SCENE I',
    'ALICE',
    'Again.',
  ].join('\n');

  await page.goto('/');
  await page.locator('#pdf-upload').setInputFiles({
    name: 'explicit-acts-scenes.pdf',
    mimeType: 'application/pdf',
    buffer: buildPdfFromText(pdfText),
  });

  await expect(page.locator('#analysis')).toBeVisible({ timeout: 120000 });
  await expect(page.locator('#result-status')).toContainText('Analysis ready', { timeout: 120000 });
  await expect(page.locator('#results-heading')).not.toHaveText('', { timeout: 120000 });
  await expect(page.locator('#result-meta')).toContainText(/acts|scenes|characters/i, { timeout: 120000 });
});

test('submitting a public URL completes a real end-to-end analysis', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Play URL').fill('https://www.gutenberg.org/cache/epub/1513/pg1513.txt');
  await page.getByRole('button', { name: /analyze play/i }).click();

  await expect(page.locator('#result-status')).toContainText('Analysis ready', { timeout: 120000 });
  await expect(page.locator('#results-heading')).not.toHaveText('', { timeout: 120000 });
  await expect(page.locator('#plot-view svg')).toBeVisible({ timeout: 120000 });
  await expect(page.locator('#result-meta')).toContainText('acts');
});
