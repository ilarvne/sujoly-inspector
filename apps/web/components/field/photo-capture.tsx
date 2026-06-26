'use client';

import { useState, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { CameraIcon, XIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface CapturedPhoto {
  blob: Blob;
  filename: string;
  mimeType: string;
  size: number;
  previewUrl: string;
}

export function PhotoCapture({
  photos,
  onAdd,
  onRemove,
}: {
  photos: CapturedPhoto[];
  onAdd: (photo: CapturedPhoto) => void;
  onRemove: (index: number) => void;
}) {
  const t = useTranslations('field');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files) return;

      for (const file of Array.from(files)) {
        if (!file.type.startsWith('image/')) continue;
        if (file.size > 10 * 1024 * 1024) continue;

        const previewUrl = URL.createObjectURL(file);
        onAdd({
          blob: file,
          filename: file.name || `photo-${Date.now()}.jpg`,
          mimeType: file.type,
          size: file.size,
          previewUrl,
        });
      }

      if (inputRef.current) {
        inputRef.current.value = '';
      }
    },
    [onAdd]
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          data-testid="photo-input"
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => inputRef.current?.click()}
          data-testid="add-photo-btn"
        >
          <CameraIcon className="size-4 mr-2" />
          {t('addPhoto')}
        </Button>
      </div>

      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
          {photos.map((photo, index) => (
            <div
              key={index}
              className="group relative aspect-square overflow-hidden rounded-md border bg-muted"
              data-testid={`photo-${index}`}
            >
              <img
                src={photo.previewUrl}
                alt={photo.filename}
                className="size-full object-cover"
              />
              <button
                type="button"
                onClick={() => onRemove(index)}
                className="absolute right-1 top-1 rounded-full bg-black/60 p-1 text-white opacity-0 transition-opacity group-hover:opacity-100"
                data-testid={`remove-photo-${index}`}
              >
                <XIcon className="size-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
