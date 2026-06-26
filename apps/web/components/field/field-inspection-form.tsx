'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useLiveQuery } from 'dexie-react-hooks';
import { SaveIcon, Trash2Icon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { db } from '@/lib/db/field-db';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useConnectivityStore } from '@/lib/stores/connectivity-store';
import { processSyncQueue } from '@/lib/sync/sync-engine';
import { mockStructures } from '@/lib/api/mock-data';
import { SyncStatusBadge } from './sync-status-badge';
import { PhotoCapture, type CapturedPhoto } from './photo-capture';
import { VoiceNoteRecorder, type RecordedVoiceNote } from './voice-note-recorder';
import { GpsCorrection, type GpsCoordinates } from './gps-correction';

const conditions = ['normal', 'inspection', 'repair', 'critical'] as const;

export function FieldInspectionForm() {
  const t = useTranslations('field');
  const tMap = useTranslations('map');
  const tSync = useTranslations('sync');
  const user = useAuthStore((s) => s.user);
  const isOnline = useConnectivityStore((s) => s.isOnline);

  const [selectedStructureId, setSelectedStructureId] = useState<string | null>(null);
  const [inspectorName, setInspectorName] = useState('');
  const [inspectionDate, setInspectionDate] = useState(new Date().toISOString().split('T')[0]);
  const [findings, setFindings] = useState('');
  const [condition, setCondition] = useState<string>('normal');
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [voiceNotes, setVoiceNotes] = useState<RecordedVoiceNote[]>([]);
  const [gpsCoordinates, setGpsCoordinates] = useState<GpsCoordinates | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const savedInspections = useLiveQuery(() => db.fieldInspections.toArray());
  const allStructures = mockStructures();

  useEffect(() => {
    if (user) {
      setInspectorName(user.name);
    }
  }, [user]);

  const handleAddPhoto = (photo: CapturedPhoto) => {
    setPhotos((prev) => [...prev, photo]);
  };

  const handleRemovePhoto = (index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddVoiceNote = (note: RecordedVoiceNote) => {
    setVoiceNotes((prev) => [...prev, note]);
  };

  const handleRemoveVoiceNote = (index: number) => {
    setVoiceNotes((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!selectedStructureId || !findings.trim()) return;

    setIsSaving(true);
    setSaveMessage(null);

    try {
      const structure = allStructures.features.find(
        (f) => f.properties.id === selectedStructureId
      );
      const now = new Date().toISOString();

      const inspectionId = await db.fieldInspections.add({
        structureId: selectedStructureId,
        structureName: structure?.properties.name.ru || selectedStructureId,
        inspectorName: inspectorName || 'Unknown',
        inspectionDate,
        findings,
        condition,
        gpsLat: gpsCoordinates?.lat,
        gpsLon: gpsCoordinates?.lon,
        gpsCorrected: gpsCoordinates !== null,
        syncStatus: 'pending',
        createdAt: now,
        updatedAt: now,
      });

      for (const photo of photos) {
        await db.fieldPhotos.add({
          inspectionId: inspectionId as number,
          blob: photo.blob,
          filename: photo.filename,
          mimeType: photo.mimeType,
          size: photo.size,
          createdAt: now,
        });
      }

      for (const note of voiceNotes) {
        await db.fieldVoiceNotes.add({
          inspectionId: inspectionId as number,
          blob: note.blob,
          language: note.language,
          durationSeconds: note.durationSeconds,
          transcriptionStatus: 'pending',
          createdAt: now,
        });
      }

      await db.syncQueue.add({
        inspectionId: inspectionId as number,
        recordType: 'inspection',
        status: 'pending',
        attempts: 0,
        createdAt: now,
        updatedAt: now,
      });

      for (const _photo of photos) {
        await db.syncQueue.add({
          inspectionId: inspectionId as number,
          recordType: 'photo',
          status: 'pending',
          attempts: 0,
          createdAt: now,
          updatedAt: now,
        });
      }

      for (const _note of voiceNotes) {
        await db.syncQueue.add({
          inspectionId: inspectionId as number,
          recordType: 'voice_note',
          status: 'pending',
          attempts: 0,
          createdAt: now,
          updatedAt: now,
        });
      }

      const pendingCount = await db.syncQueue
        .where('status')
        .anyOf(['pending', 'failed', 'conflict'])
        .count();
      useConnectivityStore.getState().setPendingSyncCount(pendingCount);

      setSaveMessage({ type: 'success', text: t('saveSuccess') });

      setSelectedStructureId(null);
      setFindings('');
      setCondition('normal');
      setPhotos([]);
      setVoiceNotes([]);
      setGpsCoordinates(null);

      if (isOnline) {
        processSyncQueue();
      }
    } catch {
      setSaveMessage({ type: 'error', text: t('saveError') });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    await db.fieldInspections.delete(id);
    await db.fieldPhotos.where('inspectionId').equals(id).delete();
    await db.fieldVoiceNotes.where('inspectionId').equals(id).delete();
    await db.syncQueue.where('inspectionId').equals(id).delete();

    const pendingCount = await db.syncQueue
      .where('status')
      .anyOf(['pending', 'failed', 'conflict'])
      .count();
    useConnectivityStore.getState().setPendingSyncCount(pendingCount);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t('newInspection')}</CardTitle>
          <CardDescription>{t('subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>{t('structure')}</Label>
              <Select
                value={selectedStructureId ?? ''}
                onValueChange={setSelectedStructureId}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('selectStructure')} />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {allStructures.features.map((f) => (
                    <SelectItem key={f.properties.id} value={f.properties.id}>
                      {f.properties.id} — {f.properties.name.ru}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>{t('inspectorName')}</Label>
              <Input
                value={inspectorName}
                onChange={(e) => setInspectorName(e.target.value)}
                placeholder={t('inspectorName')}
                data-testid="inspector-name"
              />
            </div>

            <div className="space-y-2">
              <Label>{t('inspectionDate')}</Label>
              <Input
                type="date"
                value={inspectionDate}
                onChange={(e) => setInspectionDate(e.target.value)}
                data-testid="inspection-date"
              />
            </div>

            <div className="space-y-2">
              <Label>{t('condition')}</Label>
              <Select value={condition} onValueChange={setCondition}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {conditions.map((c) => (
                    <SelectItem key={c} value={c}>
                      {tMap(`condition.${c}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t('findings')}</Label>
            <Textarea
              value={findings}
              onChange={(e) => setFindings(e.target.value)}
              placeholder={t('findingsPlaceholder')}
              rows={4}
              data-testid="findings-input"
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label className="text-sm font-semibold">{t('photos')}</Label>
            <PhotoCapture
              photos={photos}
              onAdd={handleAddPhoto}
              onRemove={handleRemovePhoto}
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label className="text-sm font-semibold">{t('voiceNotes')}</Label>
            <VoiceNoteRecorder
              notes={voiceNotes}
              onAdd={handleAddVoiceNote}
              onRemove={handleRemoveVoiceNote}
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label className="text-sm font-semibold">{t('gpsCorrection')}</Label>
            <GpsCorrection
              coordinates={gpsCoordinates}
              onChange={setGpsCoordinates}
            />
          </div>

          <Button
            onClick={handleSave}
            disabled={isSaving || !selectedStructureId || !findings.trim()}
            className="w-full"
            size="lg"
            data-testid="save-inspection-btn"
          >
            <SaveIcon className="size-4 mr-2" />
            {isSaving ? t('saving') : t('saveInspection')}
          </Button>

          {saveMessage && (
            <Alert variant={saveMessage.type === 'error' ? 'destructive' : 'default'}>
              <AlertDescription>{saveMessage.text}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('savedInspections')}</CardTitle>
        </CardHeader>
        <CardContent>
          {!savedInspections || savedInspections.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t('noSavedInspections')}</p>
          ) : (
            <ScrollArea className="h-[400px] w-full pr-4">
              <div className="space-y-3">
                {savedInspections
                  .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
                  .map((inspection) => (
                    <div
                      key={inspection.id}
                      className="rounded-md border p-3 space-y-2"
                      data-testid={`saved-inspection-${inspection.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1">
                          <div className="text-sm font-semibold">
                            {inspection.structureId} — {inspection.structureName}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {inspection.inspectionDate} · {inspection.inspectorName}
                          </div>
                          <div className="text-sm">{inspection.findings}</div>
                          {inspection.gpsCorrected && (
                            <div className="text-xs text-muted-foreground">
                              GPS: {inspection.gpsLat?.toFixed(6)}, {inspection.gpsLon?.toFixed(6)}
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <SyncStatusBadge status={inspection.syncStatus} />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(inspection.id!)}
                            className="text-destructive hover:text-destructive"
                            data-testid={`delete-inspection-${inspection.id}`}
                          >
                            <Trash2Icon className="size-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
