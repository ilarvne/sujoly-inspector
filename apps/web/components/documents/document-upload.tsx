'use client';

import { useState, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { UploadCloudIcon } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { mockAddDocument } from '@/lib/api/mock-data';
import { useQueryClient } from '@tanstack/react-query';

const ACCEPTED_TYPES = ['application/pdf', 'image/jpeg', 'image/png'];
const MAX_SIZE = 10 * 1024 * 1024;

export function DocumentUpload({ structureId }: { structureId: string }) {
  const t = useTranslations('documents');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const handleFile = useCallback((file: File) => {
    setError(null);
    setSuccess(false);

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError(t('invalidFileType'));
      return;
    }
    if (file.size > MAX_SIZE) {
      setError(t('fileTooLarge'));
      return;
    }

    setUploading(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          setUploading(false);
          setSuccess(true);
          mockAddDocument(structureId, {
            filename: file.name,
            fileType: file.type.split('/')[1] || 'file',
            fileSize: file.size,
          });
          queryClient.invalidateQueries({ queryKey: ['documents', structureId] });
          setTimeout(() => setSuccess(false), 3000);
          return 100;
        }
        return p + 20;
      });
    }, 200);
  }, [structureId, t, queryClient]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  return (
    <div className="space-y-3">
      <div
        data-testid="document-upload-area"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={handleClick}
        className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/25 p-6 cursor-pointer hover:border-primary/50 transition-colors"
      >
        <UploadCloudIcon className="size-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground text-center">{t('dragDrop')}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {uploading && (
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">{t('uploading')}</span>
          <Progress value={progress} />
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <AlertDescription>{t('uploadSuccess')}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
