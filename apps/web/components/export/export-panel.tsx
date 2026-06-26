'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { FileTextIcon, MapIcon, FileSpreadsheetIcon, DownloadIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { useStructuresGeoJSON, useStructureDetail, useInspections } from '@/lib/api/client';
import { useFilterStore } from '@/lib/stores/filter-store';
import { mockStructures } from '@/lib/api/mock-data';
import {
  generateCSV,
  generateGeoJSON,
  generatePDF,
  downloadBlob,
} from '@/lib/export/export-utils';

type ExportFormat = 'csv' | 'geojson' | 'pdf';

export function ExportPanel() {
  const t = useTranslations('exportNs');
  const locale = useLocale();
  const filters = useFilterStore();
  const { data: geojsonData } = useStructuresGeoJSON(filters);
  const [selectedStructureId, setSelectedStructureId] = useState<string | null>(null);
  const [generating, setGenerating] = useState<ExportFormat | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const allStructures = mockStructures();
  const { data: structureDetail } = useStructureDetail(selectedStructureId);
  const { data: inspections } = useInspections(selectedStructureId);

  const handleCSVExport = () => {
    if (!geojsonData) return;
    setGenerating('csv');
    try {
      const csv = generateCSV(geojsonData.features);
      downloadBlob(csv, 'structures.csv', 'text/csv;charset=utf-8');
      setMessage({ type: 'success', text: t('exportComplete') });
    } catch {
      setMessage({ type: 'error', text: t('exportError') });
    }
    setGenerating(null);
  };

  const handleGeoJSONExport = () => {
    if (!geojsonData) return;
    setGenerating('geojson');
    try {
      const json = generateGeoJSON(geojsonData);
      downloadBlob(json, 'structures.geojson', 'application/geo+json');
      setMessage({ type: 'success', text: t('exportComplete') });
    } catch {
      setMessage({ type: 'error', text: t('exportError') });
    }
    setGenerating(null);
  };

  const handlePDFExport = () => {
    if (!structureDetail || !inspections) return;
    setGenerating('pdf');
    try {
      generatePDF(structureDetail, inspections, t('pdf'));
      setMessage({ type: 'success', text: t('exportComplete') });
    } catch {
      setMessage({ type: 'error', text: t('exportError') });
    }
    setGenerating(null);
  };

  const formatCards = [
    {
      format: 'csv' as ExportFormat,
      icon: FileSpreadsheetIcon,
      title: t('csv'),
      description: t('csvDescription'),
      onClick: handleCSVExport,
    },
    {
      format: 'geojson' as ExportFormat,
      icon: MapIcon,
      title: t('geojson'),
      description: t('geojsonDescription'),
      onClick: handleGeoJSONExport,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {formatCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.format}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="size-5 text-primary" />
                  <CardTitle className="text-base">{card.title}</CardTitle>
                </div>
                <CardDescription>{card.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={card.onClick}
                  disabled={generating !== null || !geojsonData}
                  className="w-full"
                  data-testid={`export-${card.format}`}
                >
                  <DownloadIcon className="size-4 mr-2" />
                  {generating === card.format ? t('generating') : t('download')}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Separator />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileTextIcon className="size-5 text-primary" />
            <CardTitle className="text-base">{t('pdf')}</CardTitle>
          </div>
          <CardDescription>{t('pdfDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>{t('selectStructure')}</Label>
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
                    {f.properties.id} — {f.properties.name[locale as keyof typeof f.properties.name] || f.properties.name.ru}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={handlePDFExport}
            disabled={generating !== null || !selectedStructureId || !structureDetail || !inspections}
            className="w-full"
            data-testid="export-pdf"
          >
            <DownloadIcon className="size-4 mr-2" />
            {generating === 'pdf' ? t('generating') : t('download')}
          </Button>
        </CardContent>
      </Card>

      {message && (
        <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
