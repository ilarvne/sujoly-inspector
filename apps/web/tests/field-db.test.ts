import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '@/lib/db/field-db';
import type { FieldInspection, SyncQueueEntry } from '@/lib/db/types';

describe('FieldDatabase', () => {
  beforeEach(async () => {
    await db.fieldInspections.clear();
    await db.fieldPhotos.clear();
    await db.fieldVoiceNotes.clear();
    await db.syncQueue.clear();
  });

  describe('fieldInspections table', () => {
    it('can add an inspection and retrieve it by id', async () => {
      const id = await db.fieldInspections.add({
        structureId: 'KZ-ZH-0001',
        structureName: 'Test Dam',
        inspectorName: 'Test Inspector',
        inspectionDate: '2026-06-26',
        findings: 'Test findings',
        condition: 'normal',
        gpsCorrected: false,
        syncStatus: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      const retrieved = await db.fieldInspections.get(id);
      expect(retrieved).toBeDefined();
      expect(retrieved?.structureId).toBe('KZ-ZH-0001');
      expect(retrieved?.findings).toBe('Test findings');
      expect(retrieved?.syncStatus).toBe('pending');
    });

    it('can query inspections by structureId', async () => {
      await db.fieldInspections.bulkAdd([
        {
          structureId: 'KZ-ZH-0001',
          structureName: 'Dam A',
          inspectorName: 'Inspector 1',
          inspectionDate: '2026-06-26',
          findings: 'Findings A',
          condition: 'normal',
          gpsCorrected: false,
          syncStatus: 'pending',
          createdAt: '2026-06-26T10:00:00Z',
          updatedAt: '2026-06-26T10:00:00Z',
        },
        {
          structureId: 'KZ-ZH-0002',
          structureName: 'Dam B',
          inspectorName: 'Inspector 2',
          inspectionDate: '2026-06-26',
          findings: 'Findings B',
          condition: 'repair',
          gpsCorrected: true,
          gpsLat: 44.0,
          gpsLon: 72.6,
          syncStatus: 'confirmed',
          createdAt: '2026-06-26T11:00:00Z',
          updatedAt: '2026-06-26T11:00:00Z',
        },
        {
          structureId: 'KZ-ZH-0001',
          structureName: 'Dam A',
          inspectorName: 'Inspector 3',
          inspectionDate: '2026-06-25',
          findings: 'Findings C',
          condition: 'critical',
          gpsCorrected: false,
          syncStatus: 'failed',
          createdAt: '2026-06-25T10:00:00Z',
          updatedAt: '2026-06-25T10:00:00Z',
        },
      ]);

      const forStructure1 = await db.fieldInspections
        .where('structureId')
        .equals('KZ-ZH-0001')
        .toArray();
      expect(forStructure1).toHaveLength(2);
    });

    it('can query inspections by syncStatus', async () => {
      await db.fieldInspections.bulkAdd([
        {
          structureId: 'KZ-ZH-0001',
          structureName: 'Dam A',
          inspectorName: 'Inspector 1',
          inspectionDate: '2026-06-26',
          findings: 'A',
          condition: 'normal',
          gpsCorrected: false,
          syncStatus: 'pending',
          createdAt: '2026-06-26T10:00:00Z',
          updatedAt: '2026-06-26T10:00:00Z',
        },
        {
          structureId: 'KZ-ZH-0002',
          structureName: 'Dam B',
          inspectorName: 'Inspector 2',
          inspectionDate: '2026-06-26',
          findings: 'B',
          condition: 'normal',
          gpsCorrected: false,
          syncStatus: 'confirmed',
          createdAt: '2026-06-26T11:00:00Z',
          updatedAt: '2026-06-26T11:00:00Z',
        },
      ]);

      const pending = await db.fieldInspections
        .where('syncStatus')
        .equals('pending')
        .toArray();
      expect(pending).toHaveLength(1);
      expect(pending[0].structureId).toBe('KZ-ZH-0001');
    });

    it('can update an inspection', async () => {
      const id = await db.fieldInspections.add({
        structureId: 'KZ-ZH-0001',
        structureName: 'Test Dam',
        inspectorName: 'Inspector',
        inspectionDate: '2026-06-26',
        findings: 'Original',
        condition: 'normal',
        gpsCorrected: false,
        syncStatus: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      await db.fieldInspections.update(id, {
        findings: 'Updated findings',
        syncStatus: 'confirmed',
      });

      const updated = await db.fieldInspections.get(id);
      expect(updated?.findings).toBe('Updated findings');
      expect(updated?.syncStatus).toBe('confirmed');
    });

    it('can delete an inspection', async () => {
      const id = await db.fieldInspections.add({
        structureId: 'KZ-ZH-0001',
        structureName: 'Test Dam',
        inspectorName: 'Inspector',
        inspectionDate: '2026-06-26',
        findings: 'To be deleted',
        condition: 'normal',
        gpsCorrected: false,
        syncStatus: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      await db.fieldInspections.delete(id);
      const deleted = await db.fieldInspections.get(id);
      expect(deleted).toBeUndefined();
    });
  });

  describe('syncQueue table', () => {
    it('can add and query sync queue entries by status', async () => {
      const inspectionId = await db.fieldInspections.add({
        structureId: 'KZ-ZH-0001',
        structureName: 'Test',
        inspectorName: 'Test',
        inspectionDate: '2026-06-26',
        findings: 'Test',
        condition: 'normal',
        gpsCorrected: false,
        syncStatus: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      const entries: Omit<SyncQueueEntry, 'id'>[] = [
        {
          inspectionId: inspectionId as number,
          recordType: 'inspection',
          status: 'pending',
          attempts: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          inspectionId: inspectionId as number,
          recordType: 'photo',
          status: 'pending',
          attempts: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          inspectionId: inspectionId as number,
          recordType: 'voice_note',
          status: 'confirmed',
          attempts: 0,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];

      await db.syncQueue.bulkAdd(entries);

      const pending = await db.syncQueue.where('status').equals('pending').toArray();
      expect(pending).toHaveLength(2);

      const confirmed = await db.syncQueue.where('status').equals('confirmed').toArray();
      expect(confirmed).toHaveLength(1);
    });

    it('can count entries by status', async () => {
      const now = new Date().toISOString();
      await db.syncQueue.bulkAdd([
        { inspectionId: 1, recordType: 'inspection', status: 'pending', attempts: 0, createdAt: now, updatedAt: now },
        { inspectionId: 1, recordType: 'photo', status: 'pending', attempts: 0, createdAt: now, updatedAt: now },
        { inspectionId: 1, recordType: 'voice_note', status: 'failed', attempts: 1, createdAt: now, updatedAt: now },
      ]);

      const pendingCount = await db.syncQueue.where('status').anyOf(['pending', 'failed', 'conflict']).count();
      expect(pendingCount).toBe(3);
    });

    it('can query entries by inspectionId', async () => {
      const now = new Date().toISOString();
      await db.syncQueue.bulkAdd([
        { inspectionId: 1, recordType: 'inspection', status: 'pending', attempts: 0, createdAt: now, updatedAt: now },
        { inspectionId: 2, recordType: 'inspection', status: 'pending', attempts: 0, createdAt: now, updatedAt: now },
        { inspectionId: 1, recordType: 'photo', status: 'pending', attempts: 0, createdAt: now, updatedAt: now },
      ]);

      const forInspection1 = await db.syncQueue.where('inspectionId').equals(1).toArray();
      expect(forInspection1).toHaveLength(2);
    });
  });

  describe('fieldPhotos table', () => {
    it('can add and retrieve photos by inspectionId', async () => {
      const blob = new Blob(['test'], { type: 'image/jpeg' });
      const now = new Date().toISOString();

      await db.fieldPhotos.add({
        inspectionId: 1,
        blob,
        filename: 'test.jpg',
        mimeType: 'image/jpeg',
        size: 4,
        createdAt: now,
      });

      const photos = await db.fieldPhotos.where('inspectionId').equals(1).toArray();
      expect(photos).toHaveLength(1);
      expect(photos[0].filename).toBe('test.jpg');
    });
  });

  describe('fieldVoiceNotes table', () => {
    it('can add and query voice notes by transcriptionStatus', async () => {
      const blob = new Blob(['audio'], { type: 'audio/webm' });
      const now = new Date().toISOString();

      await db.fieldVoiceNotes.bulkAdd([
        { inspectionId: 1, blob, language: 'ru', durationSeconds: 10, transcriptionStatus: 'pending', createdAt: now },
        { inspectionId: 1, blob, language: 'kk', durationSeconds: 5, transcriptionStatus: 'complete', transcriptionText: 'Test', createdAt: now, transcribedAt: now },
        { inspectionId: 2, blob, language: 'ru', durationSeconds: 15, transcriptionStatus: 'pending', createdAt: now },
      ]);

      const pending = await db.fieldVoiceNotes.where('transcriptionStatus').equals('pending').toArray();
      expect(pending).toHaveLength(2);

      const complete = await db.fieldVoiceNotes.where('transcriptionStatus').equals('complete').toArray();
      expect(complete).toHaveLength(1);
      expect(complete[0].transcriptionText).toBe('Test');
    });
  });
});
