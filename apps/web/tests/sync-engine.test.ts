import { describe, it, expect } from 'vitest';
import {
  detectConflicts,
  applyResolution,
  hasUnresolvedConflicts,
  resolveAllAsLocal,
  resolveAllAsServer,
} from '@/lib/sync/conflict-resolution';
import { transcribeVoiceNote } from '@/lib/sync/voice-transcription';
import type { FieldInspection, ConflictField } from '@/lib/db/types';

function makeInspection(overrides: Partial<FieldInspection> = {}): FieldInspection {
  return {
    id: 1,
    structureId: 'KZ-ZH-0001',
    structureName: 'Test Dam',
    inspectorName: 'Test Inspector',
    inspectionDate: '2026-06-26',
    findings: 'Original findings',
    condition: 'normal',
    gpsCorrected: false,
    syncStatus: 'pending',
    createdAt: '2026-06-26T10:00:00Z',
    updatedAt: '2026-06-26T10:00:00Z',
    ...overrides,
  };
}

describe('conflict-resolution', () => {
  describe('detectConflicts', () => {
    it('returns empty array when server has no conflicting data', () => {
      const local = makeInspection();
      const server: Partial<FieldInspection> = {};
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(0);
    });

    it('returns empty array when all fields match', () => {
      const local = makeInspection();
      const server: Partial<FieldInspection> = {
        findings: local.findings,
        condition: local.condition,
        inspectorName: local.inspectorName,
        inspectionDate: local.inspectionDate,
      };
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(0);
    });

    it('detects findings conflict', () => {
      const local = makeInspection({ findings: 'Local findings' });
      const server: Partial<FieldInspection> = { findings: 'Server findings' };
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(1);
      expect(conflicts[0].field).toBe('findings');
      expect(conflicts[0].localValue).toBe('Local findings');
      expect(conflicts[0].serverValue).toBe('Server findings');
      expect(conflicts[0].resolution).toBeNull();
    });

    it('detects condition conflict', () => {
      const local = makeInspection({ condition: 'normal' });
      const server: Partial<FieldInspection> = { condition: 'critical' };
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(1);
      expect(conflicts[0].field).toBe('condition');
    });

    it('detects multiple field conflicts', () => {
      const local = makeInspection({
        findings: 'Local',
        condition: 'normal',
        inspectorName: 'Inspector A',
      });
      const server: Partial<FieldInspection> = {
        findings: 'Server',
        condition: 'repair',
        inspectorName: 'Inspector B',
      };
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(3);
    });

    it('detects GPS coordinate conflicts', () => {
      const local = makeInspection({ gpsLat: 44.0, gpsLon: 72.6 });
      const server: Partial<FieldInspection> = { gpsLat: 44.1, gpsLon: 72.5 };
      const conflicts = detectConflicts(local, server);
      expect(conflicts).toHaveLength(2);
    });
  });

  describe('applyResolution', () => {
    it('applies local resolution', () => {
      const local = makeInspection();
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'Findings', localValue: 'Local', serverValue: 'Server', resolution: 'local' },
      ];
      const result = applyResolution(local, conflicts);
      expect(result.findings).toBe('Local');
    });

    it('applies server resolution', () => {
      const local = makeInspection();
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'Findings', localValue: 'Local', serverValue: 'Server', resolution: 'server' },
      ];
      const result = applyResolution(local, conflicts);
      expect(result.findings).toBe('Server');
    });

    it('applies merge resolution with mergedValue', () => {
      const local = makeInspection();
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'Findings', localValue: 'Local', serverValue: 'Server', resolution: 'merge', mergedValue: 'Merged' },
      ];
      const result = applyResolution(local, conflicts);
      expect(result.findings).toBe('Merged');
    });

    it('skips unresolved conflicts', () => {
      const local = makeInspection();
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'Findings', localValue: 'Local', serverValue: 'Server', resolution: null },
        { field: 'condition', label: 'Condition', localValue: 'normal', serverValue: 'critical', resolution: 'local' },
      ];
      const result = applyResolution(local, conflicts);
      expect(result.findings).toBeUndefined();
      expect(result.condition).toBe('normal');
    });
  });

  describe('hasUnresolvedConflicts', () => {
    it('returns true when any conflict is unresolved', () => {
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'F', localValue: 'A', serverValue: 'B', resolution: 'local' },
        { field: 'condition', label: 'C', localValue: 'X', serverValue: 'Y', resolution: null },
      ];
      expect(hasUnresolvedConflicts(conflicts)).toBe(true);
    });

    it('returns false when all conflicts are resolved', () => {
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'F', localValue: 'A', serverValue: 'B', resolution: 'local' },
        { field: 'condition', label: 'C', localValue: 'X', serverValue: 'Y', resolution: 'server' },
      ];
      expect(hasUnresolvedConflicts(conflicts)).toBe(false);
    });

    it('returns false for empty conflicts array', () => {
      expect(hasUnresolvedConflicts([])).toBe(false);
    });
  });

  describe('resolveAllAsLocal / resolveAllAsServer', () => {
    it('resolves all conflicts as local', () => {
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'F', localValue: 'A', serverValue: 'B', resolution: null },
        { field: 'condition', label: 'C', localValue: 'X', serverValue: 'Y', resolution: null },
      ];
      const resolved = resolveAllAsLocal(conflicts);
      expect(resolved.every((c) => c.resolution === 'local')).toBe(true);
    });

    it('resolves all conflicts as server', () => {
      const conflicts: ConflictField[] = [
        { field: 'findings', label: 'F', localValue: 'A', serverValue: 'B', resolution: null },
        { field: 'condition', label: 'C', localValue: 'X', serverValue: 'Y', resolution: null },
      ];
      const resolved = resolveAllAsServer(conflicts);
      expect(resolved.every((c) => c.resolution === 'server')).toBe(true);
    });
  });
});

describe('voice-transcription', () => {
  it('returns a non-empty string for Russian', async () => {
    const blob = new Blob(['audio'], { type: 'audio/webm' });
    const result = await transcribeVoiceNote(blob, 'ru');
    expect(result).toBeTruthy();
    expect(result.length).toBeGreaterThan(10);
  });

  it('returns a non-empty string for Kazakh', async () => {
    const blob = new Blob(['audio'], { type: 'audio/webm' });
    const result = await transcribeVoiceNote(blob, 'kk');
    expect(result).toBeTruthy();
    expect(result.length).toBeGreaterThan(10);
  });

  it('returns different transcriptions on multiple calls (randomized)', async () => {
    const blob = new Blob(['audio'], { type: 'audio/webm' });
    const results = new Set<string>();
    for (let i = 0; i < 10; i++) {
      const result = await transcribeVoiceNote(blob, 'ru');
      results.add(result);
    }
    expect(results.size).toBeGreaterThan(1);
  }, 20000);
});
