import { describe, it, expect } from 'vitest';
import { generateCSV, generateGeoJSON, formatFileSize } from '@/lib/export/export-utils';
import { mockStructures } from '@/lib/api/mock-data';
import type { StructureCollection } from '@/lib/api/types';

describe('generateCSV', () => {
  it('produces CSV string with BOM prefix', () => {
    const collection = mockStructures();
    const csv = generateCSV(collection.features.slice(0, 5));
    expect(csv.startsWith('\uFEFF')).toBe(true);
  });

  it('has header row with expected columns', () => {
    const collection = mockStructures();
    const csv = generateCSV(collection.features.slice(0, 1));
    const lines = csv.split('\n');
    expect(lines[0]).toContain('id');
    expect(lines[0]).toContain('name');
    expect(lines[0]).toContain('type');
    expect(lines[0]).toContain('condition');
    expect(lines[0]).toContain('district');
    expect(lines[0]).toContain('basin');
  });

  it('produces one data row per feature', () => {
    const collection = mockStructures();
    const features = collection.features.slice(0, 3);
    const csv = generateCSV(features);
    const lines = csv.split('\n').filter((l) => l.trim() && !l.startsWith('\uFEFFid'));
    expect(lines.length).toBe(3);
  });

  it('contains Cyrillic text from structure names', () => {
    const collection = mockStructures();
    const csv = generateCSV(collection.features.slice(0, 1));
    expect(csv).toContain('KZ-ZH');
  });
});

describe('generateGeoJSON', () => {
  it('produces valid JSON string', () => {
    const collection: StructureCollection = mockStructures();
    const json = generateGeoJSON(collection);
    const parsed = JSON.parse(json);
    expect(parsed.type).toBe('FeatureCollection');
    expect(Array.isArray(parsed.features)).toBe(true);
  });

  it('preserves feature count', () => {
    const collection = mockStructures();
    const json = generateGeoJSON(collection);
    const parsed = JSON.parse(json);
    expect(parsed.features.length).toBe(collection.features.length);
  });

  it('preserves feature properties', () => {
    const collection = mockStructures();
    const json = generateGeoJSON(collection);
    const parsed = JSON.parse(json);
    expect(parsed.features[0].properties).toBeDefined();
    expect(parsed.features[0].properties.id).toBeDefined();
    expect(parsed.features[0].properties.condition).toBeDefined();
  });
});

describe('formatFileSize', () => {
  it('formats bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 B');
  });

  it('formats kilobytes correctly', () => {
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
  });

  it('formats megabytes correctly', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
    expect(formatFileSize(5 * 1024 * 1024)).toBe('5.0 MB');
  });
});
