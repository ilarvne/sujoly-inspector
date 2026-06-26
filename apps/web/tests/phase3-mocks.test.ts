import { describe, it, expect, beforeEach } from 'vitest';
import {
  mockInspections,
  mockDocuments,
  mockRiskScore,
  mockOverrides,
  mockAddDocument,
  mockAddOverride,
} from '@/lib/api/mock-data';
import { useAuthStore } from '@/lib/stores/auth-store';
import type { InspectionRecord, DocumentMeta, RiskScore, EngineerOverride } from '@/lib/api/types';

describe('mockInspections', () => {
  it('returns array with at least 3 records for KZ-ZH-0001', () => {
    const result = mockInspections('KZ-ZH-0001');
    expect(result.length).toBeGreaterThanOrEqual(3);
  });

  it('records are sorted by date descending', () => {
    const result = mockInspections('KZ-ZH-0001');
    for (let i = 0; i < result.length - 1; i++) {
      expect(result[i].date.localeCompare(result[i + 1].date)).toBeGreaterThanOrEqual(0);
    }
  });

  it('each record has required fields', () => {
    const result = mockInspections('KZ-ZH-0001');
    for (const record of result) {
      expect(record.id).toBeDefined();
      expect(record.structureId).toBe('KZ-ZH-0001');
      expect(record.date).toBeDefined();
      expect(record.inspectorName).toBeDefined();
      expect(record.findings).toBeDefined();
      expect(Array.isArray(record.photoUrls)).toBe(true);
      expect(record.conditionAtInspection).toBeDefined();
    }
  });

  it('returns at least 3 records for any valid-format ID', () => {
    const ids = ['KZ-ZH-0005', 'KZ-ZH-0010', 'KZ-ZH-0050', 'KZ-ZH-9999'];
    for (const id of ids) {
      const result = mockInspections(id);
      expect(result.length).toBeGreaterThanOrEqual(3);
    }
  });
});

describe('mockDocuments', () => {
  it('returns array of DocumentMeta objects for KZ-ZH-0001', () => {
    const result = mockDocuments('KZ-ZH-0001');
    expect(Array.isArray(result)).toBe(true);
    for (const doc of result) {
      expect(doc.id).toBeDefined();
      expect(doc.structureId).toBe('KZ-ZH-0001');
      expect(doc.filename).toBeDefined();
      expect(doc.fileType).toBeDefined();
      expect(typeof doc.fileSize).toBe('number');
      expect(doc.uploadedBy).toBeDefined();
      expect(doc.uploadedAt).toBeDefined();
      expect(doc.downloadUrl).toBeDefined();
    }
  });

  it('downloadUrl starts with #mock-download', () => {
    const result = mockDocuments('KZ-ZH-0001');
    for (const doc of result) {
      expect(doc.downloadUrl.startsWith('#mock-download')).toBe(true);
    }
  });
});

describe('mockRiskScore', () => {
  it('returns RiskScore for KZ-ZH-0001', () => {
    const result = mockRiskScore('KZ-ZH-0001');
    expect(result.structureId).toBe('KZ-ZH-0001');
    expect(typeof result.overall).toBe('number');
    expect(result.overall).toBeGreaterThanOrEqual(0);
    expect(result.overall).toBeLessThanOrEqual(100);
    expect(result.explanation).toBeDefined();
    expect(result.explanation.length).toBeGreaterThan(0);
    expect(result.computedAt).toBeDefined();
  });

  it('components array has 4 items', () => {
    const result = mockRiskScore('KZ-ZH-0001');
    expect(result.components.length).toBe(4);
  });

  it('each component has required fields with valid ranges', () => {
    const result = mockRiskScore('KZ-ZH-0001');
    const keys = ['structural', 'hydrological', 'operational', 'age'];
    for (let i = 0; i < result.components.length; i++) {
      const comp = result.components[i];
      expect(comp.key).toBe(keys[i]);
      expect(comp.label).toBeDefined();
      expect(typeof comp.score).toBe('number');
      expect(comp.score).toBeGreaterThanOrEqual(0);
      expect(comp.score).toBeLessThanOrEqual(100);
      expect(typeof comp.weight).toBe('number');
      expect(comp.weight).toBeGreaterThan(0);
      expect(comp.weight).toBeLessThanOrEqual(1);
      expect(comp.description).toBeDefined();
    }
  });

  it('overall is weighted sum of component scores', () => {
    const result = mockRiskScore('KZ-ZH-0001');
    const weightedSum = result.components.reduce((sum, c) => sum + c.score * c.weight, 0);
    expect(result.overall).toBe(Math.round(weightedSum));
  });
});

describe('mockOverrides', () => {
  it('returns array of EngineerOverride objects for KZ-ZH-0001', () => {
    const result = mockOverrides('KZ-ZH-0001');
    expect(Array.isArray(result)).toBe(true);
    for (const override of result) {
      expect(override.id).toBeDefined();
      expect(override.structureId).toBe('KZ-ZH-0001');
      expect(override.field).toBeDefined();
      expect(override.originalValue).toBeDefined();
      expect(override.newValue).toBeDefined();
      expect(override.reason).toBeDefined();
      expect(override.engineerName).toBeDefined();
      expect(override.timestamp).toBeDefined();
    }
  });

  it('field is either inspection_interval or repair_status', () => {
    const result = mockOverrides('KZ-ZH-0001');
    for (const override of result) {
      expect(['inspection_interval', 'repair_status']).toContain(override.field);
    }
  });
});

describe('mockAddDocument', () => {
  it('returns DocumentMeta with generated id containing structureId', () => {
    const result = mockAddDocument('KZ-ZH-0001', {
      filename: 'test.pdf',
      fileType: 'pdf',
      fileSize: 1024,
    });
    expect(result.id).toContain('KZ-ZH-0001');
    expect(result.structureId).toBe('KZ-ZH-0001');
  });

  it('uploadedAt is today date in YYYY-MM-DD format', () => {
    const result = mockAddDocument('KZ-ZH-0001', {
      filename: 'test.pdf',
      fileType: 'pdf',
      fileSize: 1024,
    });
    const today = new Date().toISOString().split('T')[0];
    expect(result.uploadedAt).toBe(today);
  });

  it('filename and fileSize match input', () => {
    const result = mockAddDocument('KZ-ZH-0001', {
      filename: 'report.pdf',
      fileType: 'inspection_report',
      fileSize: 5120,
    });
    expect(result.filename).toBe('report.pdf');
    expect(result.fileSize).toBe(5120);
    expect(result.fileType).toBe('inspection_report');
  });
});

describe('mockAddOverride', () => {
  it('returns EngineerOverride with generated id', () => {
    const result = mockAddOverride('KZ-ZH-0001', {
      field: 'inspection_interval',
      originalValue: '12 months',
      newValue: '6 months',
      reason: 'Increased risk due to age and recent findings.',
      engineerName: 'Test Engineer',
    });
    expect(result.id).toContain('KZ-ZH-0001');
    expect(result.structureId).toBe('KZ-ZH-0001');
  });

  it('timestamp is today date', () => {
    const result = mockAddOverride('KZ-ZH-0001', {
      field: 'repair_status',
      originalValue: 'repair_required',
      newValue: 'monitor',
      reason: 'Condition is stable, monitoring recommended.',
      engineerName: 'Test Engineer',
    });
    const today = new Date().toISOString().split('T')[0];
    expect(result.timestamp).toBe(today);
  });

  it('field, originalValue, newValue, reason, engineerName match input', () => {
    const data = {
      field: 'inspection_interval' as const,
      originalValue: '12 months',
      newValue: '3 months',
      reason: 'Critical condition requires more frequent inspections.',
      engineerName: 'А. Беков',
    };
    const result = mockAddOverride('KZ-ZH-0001', data);
    expect(result.field).toBe(data.field);
    expect(result.originalValue).toBe(data.originalValue);
    expect(result.newValue).toBe(data.newValue);
    expect(result.reason).toBe(data.reason);
    expect(result.engineerName).toBe(data.engineerName);
  });
});

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it('initial state has user null', () => {
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('login sets user with correct role', () => {
    useAuthStore.getState().login('engineer');
    const user = useAuthStore.getState().user;
    expect(user).not.toBeNull();
    expect(user!.role).toBe('engineer');
  });

  it('login with admin sets admin role', () => {
    useAuthStore.getState().login('admin');
    const user = useAuthStore.getState().user;
    expect(user).not.toBeNull();
    expect(user!.role).toBe('admin');
  });

  it('logout sets user to null', () => {
    useAuthStore.getState().login('admin');
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('hasRole returns true for matching role', () => {
    useAuthStore.getState().login('engineer');
    expect(useAuthStore.getState().hasRole('engineer')).toBe(true);
  });

  it('hasRole returns false for non-matching role', () => {
    useAuthStore.getState().login('engineer');
    expect(useAuthStore.getState().hasRole('admin')).toBe(false);
  });

  it('hasRole returns true when multiple roles include current role', () => {
    useAuthStore.getState().login('engineer');
    expect(useAuthStore.getState().hasRole('admin', 'engineer')).toBe(true);
  });

  it('hasRole returns false when user is null', () => {
    expect(useAuthStore.getState().hasRole('admin')).toBe(false);
  });
});
