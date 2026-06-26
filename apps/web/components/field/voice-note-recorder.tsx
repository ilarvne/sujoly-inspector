'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { MicIcon, SquareIcon, PlayIcon, Trash2Icon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import type { VoiceNoteLanguage } from '@/lib/db/types';

export interface RecordedVoiceNote {
  blob: Blob;
  language: VoiceNoteLanguage;
  durationSeconds: number;
  audioUrl: string;
}

export function VoiceNoteRecorder({
  notes,
  onAdd,
  onRemove,
}: {
  notes: RecordedVoiceNote[];
  onAdd: (note: RecordedVoiceNote) => void;
  onRemove: (index: number) => void;
}) {
  const t = useTranslations('field');
  const tCommon = useTranslations('common');
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState<VoiceNoteLanguage>('ru');
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const isSupported = typeof MediaRecorder !== 'undefined';

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    if (!isSupported) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(blob);
        onAdd({
          blob,
          language,
          durationSeconds: recordingSeconds,
          audioUrl,
        });
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1);
      }, 1000);
    } catch (_error) {
      setIsRecording(false);
    }
  }, [isSupported, language, onAdd, recordingSeconds]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const playNote = (url: string) => {
    if (audioRef.current) {
      audioRef.current.src = url;
      audioRef.current.play();
    }
  };

  if (!isSupported) {
    return (
      <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
        {t('voiceNotes')} — MediaRecorder API not available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Select
          value={language}
          onValueChange={(v) => setLanguage(v as VoiceNoteLanguage)}
        >
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ru">{tCommon('locale.ru')}</SelectItem>
            <SelectItem value="kk">{tCommon('locale.kk')}</SelectItem>
          </SelectContent>
        </Select>

        {!isRecording ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={startRecording}
            data-testid="record-voice-btn"
          >
            <MicIcon className="size-4 mr-2" />
            {t('recordVoice')}
          </Button>
        ) : (
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={stopRecording}
            data-testid="stop-recording-btn"
          >
            <SquareIcon className="size-4 mr-2" />
            {t('stopRecording')} ({recordingSeconds}s)
          </Button>
        )}
      </div>

      <audio ref={audioRef} className="hidden" />

      {notes.length === 0 && !isRecording && (
        <p className="text-sm text-muted-foreground">{t('noVoiceNotes')}</p>
      )}

      {notes.length > 0 && (
        <div className="space-y-2">
          {notes.map((note, index) => (
            <div
              key={index}
              className="flex items-center gap-2 rounded-md border p-2"
              data-testid={`voice-note-${index}`}
            >
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => playNote(note.audioUrl)}
              >
                <PlayIcon className="size-4" />
              </Button>
              <span className="text-sm">
                {t('recordingDuration', { seconds: note.durationSeconds })}
              </span>
              <span className="text-xs text-muted-foreground">
                ({note.language === 'ru' ? 'RU' : 'KK'})
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="ml-auto"
                onClick={() => onRemove(index)}
              >
                <Trash2Icon className="size-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
