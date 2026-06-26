import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('design tokens in globals.css', () => {
  const cssPath = path.resolve(__dirname, '../app/globals.css');
  const css = fs.readFileSync(cssPath, 'utf-8');

  it('imports tailwindcss', () => {
    expect(css).toMatch(/@import\s+["']tailwindcss["']/);
  });

  it('imports tw-animate-css', () => {
    expect(css).toMatch(/@import\s+["']tw-animate-css["']/);
  });

  it('defines --primary with OKLCH color', () => {
    expect(css).toMatch(/--primary:\s*oklch/);
  });

  it('defines --font-sans mapping to Inter', () => {
    expect(css).toMatch(/--font-sans/);
  });

  it('defines --font-display mapping to Manrope', () => {
    expect(css).toMatch(/--font-display/);
  });

  it('defines all 6 status color tokens', () => {
    expect(css).toMatch(/--color-status-normal/);
    expect(css).toMatch(/--color-status-inspection/);
    expect(css).toMatch(/--color-status-repair/);
    expect(css).toMatch(/--color-status-critical/);
    expect(css).toMatch(/--color-status-unknown/);
    expect(css).toMatch(/--color-status-missing/);
  });
});
