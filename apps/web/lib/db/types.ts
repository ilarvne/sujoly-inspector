export type SyncStatus = 'pending' | 'syncing' | 'confirmed' | 'failed' | 'conflict';

export type VoiceNoteLanguage = 'ru' | 'kk';

export type TranscriptionStatus = 'none' | 'pending' | 'complete' | 'failed';

export type RecordType = 'inspection' | 'photo' | 'voice_note';

export interface FieldInspection {
  id?: number;
  structureId: string;
  structureName: string;
  inspectorName: string;
  inspectionDate: string;
  findings: string;
  condition: string;
  gpsLat?: number;
  gpsLon?: number;
  gpsCorrected: boolean;
  syncStatus: SyncStatus;
  conflictData?: ConflictField[];
  createdAt: string;
  updatedAt: string;
}

export interface FieldPhoto {
  id?: number;
  inspectionId: number;
  blob: Blob;
  filename: string;
  mimeType: string;
  size: number;
  createdAt: string;
}

export interface FieldVoiceNote {
  id?: number;
  inspectionId: number;
  blob: Blob;
  language: VoiceNoteLanguage;
  durationSeconds: number;
  transcriptionStatus: TranscriptionStatus;
  transcriptionText?: string;
  transcriptionError?: string;
  createdAt: string;
  transcribedAt?: string;
}

export interface SyncQueueEntry {
  id?: number;
  inspectionId: number;
  recordType: RecordType;
  status: SyncStatus;
  attempts: number;
  lastError?: string;
  conflictData?: ConflictField[];
  createdAt: string;
  updatedAt: string;
}

export interface ConflictField {
  field: string;
  label: string;
  localValue: unknown;
  serverValue: unknown;
  resolution: 'local' | 'server' | 'merge' | null;
  mergedValue?: unknown;
}
