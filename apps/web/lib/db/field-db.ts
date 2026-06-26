import Dexie, { type EntityTable } from 'dexie';
import type { FieldInspection, FieldPhoto, FieldVoiceNote, SyncQueueEntry } from './types';

class FieldDatabase extends Dexie {
  fieldInspections!: EntityTable<FieldInspection, 'id'>;
  fieldPhotos!: EntityTable<FieldPhoto, 'id'>;
  fieldVoiceNotes!: EntityTable<FieldVoiceNote, 'id'>;
  syncQueue!: EntityTable<SyncQueueEntry, 'id'>;

  constructor() {
    super('sujoly-field-db');
    this.version(1).stores({
      fieldInspections: '++id, structureId, syncStatus, inspectionDate, createdAt',
      fieldPhotos: '++id, inspectionId, createdAt',
      fieldVoiceNotes: '++id, inspectionId, transcriptionStatus, createdAt',
      syncQueue: '++id, inspectionId, status, createdAt',
    });
  }
}

export const db = new FieldDatabase();
