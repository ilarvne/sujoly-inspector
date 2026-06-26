'use client';

import { useMemo, useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import {
  FileText,
  Download,
  AlertTriangle,
  Calendar,
  BarChart3,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { mockStructures, mockRiskScore, detectDuplicateStructures } from '@/lib/api/mock-data';
import { downloadBlob, formatFileSize } from '@/lib/export/export-utils';
import {
  generateReportData,
  generateReportJSON,
  generateReportHTML,
  type ReportLabels,
} from '@/lib/export/report-generator';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import { ExportPanel } from '@/components/export/export-panel';
import type { ConditionStatus, StructureType } from '@/lib/api/types';

function riskColor(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 40) return '#f97316';
  return '#22c55e';
}

const conditionOrder: ConditionStatus[] = [
  'normal',
  'inspection',
  'repair',
  'critical',
  'missing',
];

const typeOrder: StructureType[] = [
  'dam',
  'reservoir',
  'canal',
  'pumping_station',
  'spillway',
  'other',
];

export function ReportView() {
  const t = useTranslations('report');
  const tMap = useTranslations('map');
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const [generating, setGenerating] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const data = useMemo(() => generateReportData(), []);

  const labels: ReportLabels = {
    title: t('title'),
    overview: t('overview'),
    totalStructures: t('totalStructures'),
    statusDistribution: t('statusDistribution'),
    avgRiskScore: t('avgRiskScore'),
    missingCoords: t('missingCoords'),
    duplicates: t('duplicates'),
    byType: t('byType'),
    topRisky: t('topRisky'),
    inspectionPlan: t('inspectionPlan'),
    next7days: t('next7days'),
    next30days: t('next30days'),
    rank: t('rank'),
    name: t('name'),
    type: t('type'),
    district: t('district'),
    riskScore: t('riskScore'),
    condition: t('condition'),
    generated: t('generated'),
    conditionLabels: {
      normal: tMap('condition.normal'),
      inspection: tMap('condition.inspection'),
      repair: tMap('condition.repair'),
      critical: tMap('condition.critical'),
      missing: tMap('condition.missing'),
    },
    structureTypeLabels: {
      dam: tMap('structureType.dam'),
      reservoir: tMap('structureType.reservoir'),
      canal: tMap('structureType.canal'),
      pumping_station: tMap('structureType.pumping_station'),
      spillway: tMap('structureType.spillway'),
      other: tMap('structureType.other'),
    },
    inspectionStatusLabels: {
      current: tMap('inspectionStatus.current'),
      overdue: tMap('inspectionStatus.overdue'),
      due_soon: tMap('inspectionStatus.due_soon'),
      never: tMap('inspectionStatus.never'),
      unknown: tMap('inspectionStatus.unknown'),
    },
  };

  const handleJSONExport = () => {
    setGenerating('json');
    try {
      const json = generateReportJSON();
      downloadBlob(json, 'report.json', 'application/json');
      setMessage({ type: 'success', text: t('generated') });
    } catch {
      setMessage({ type: 'error', text: t('generated') });
    }
    setGenerating(null);
  };

  const handleHTMLExport = () => {
    setGenerating('html');
    try {
      const html = generateReportHTML(locale, labels);
      downloadBlob(html, 'report.html', 'text/html');
      setMessage({ type: 'success', text: t('generated') });
    } catch {
      setMessage({ type: 'error', text: t('generated') });
    }
    setGenerating(null);
  };

  const jsonSize = formatFileSize(new Blob([generateReportJSON()]).size);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="size-5 text-primary" />
            <CardTitle>{t('overview')}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="rounded-lg border p-4">
              <span className="text-xs text-muted-foreground">{t('totalStructures')}</span>
              <p className="text-2xl font-bold text-primary">{data.totalStructures}</p>
            </div>
            <div className="rounded-lg border p-4">
              <span className="text-xs text-muted-foreground">{t('avgRiskScore')}</span>
              <p className="text-2xl font-bold text-primary">
                {data.avgRiskScore}
                <span className="text-sm font-normal text-muted-foreground"> / 100</span>
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <span className="text-xs text-muted-foreground">{t('missingCoords')}</span>
              <p className="text-2xl font-bold text-yellow-600">{data.missingCoordsCount}</p>
            </div>
            <div className="rounded-lg border p-4">
              <span className="text-xs text-muted-foreground">{t('duplicates')}</span>
              <p className="text-2xl font-bold text-blue-600">{data.duplicateCount}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('statusDistribution')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {conditionOrder.map((c) => {
            const count = data.statusDistribution[c];
            const pct = data.totalStructures > 0 ? Math.round((count / data.totalStructures) * 100) : 0;
            return (
              <div key={c} className="flex items-center gap-3">
                <Badge
                  style={{ backgroundColor: STATUS_COLORS_HEX[c], color: '#ffffff' }}
                  className="min-w-32 justify-center"
                >
                  {tMap(`condition.${c}`)}
                </Badge>
                <span className="w-8 text-sm font-medium tabular-nums">{count}</span>
                <Progress value={pct} className="flex-1" />
                <span className="w-10 text-right text-xs text-muted-foreground tabular-nums">{pct}%</span>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('byType')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {typeOrder
            .filter((tp) => data.byType[tp] > 0)
            .map((tp) => {
              const count = data.byType[tp];
              const pct = data.totalStructures > 0 ? Math.round((count / data.totalStructures) * 100) : 0;
              return (
                <div key={tp} className="flex items-center gap-3">
                  <span className="min-w-40 text-sm">{tMap(`structureType.${tp}`)}</span>
                  <span className="w-8 text-sm font-medium tabular-nums">{count}</span>
                  <Progress value={pct} className="flex-1" />
                  <span className="w-10 text-right text-xs text-muted-foreground tabular-nums">{pct}%</span>
                </div>
              );
            })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-5 text-primary" />
            <CardTitle>{t('topRisky')}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">{t('rank')}</TableHead>
                <TableHead>{t('name')}</TableHead>
                <TableHead>{t('type')}</TableHead>
                <TableHead>{t('district')}</TableHead>
                <TableHead className="text-right">{t('riskScore')}</TableHead>
                <TableHead>{t('condition')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.topRisky.map((s, i) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium tabular-nums">{i + 1}</TableCell>
                  <TableCell className="font-medium">
                    {s.name[locale] ?? s.name.ru}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {tMap(`structureType.${s.type}`)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{s.district}</TableCell>
                  <TableCell className="text-right">
                    <Badge
                      style={{ backgroundColor: riskColor(s.riskScore), color: '#ffffff' }}
                    >
                      {s.riskScore}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      style={{
                        backgroundColor: STATUS_COLORS_HEX[s.condition],
                        color: '#ffffff',
                      }}
                    >
                      {tMap(`condition.${s.condition}`)}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="size-5 text-primary" />
            <CardTitle>{t('inspectionPlan')}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">
                {t('next7days')}
              </h3>
              <div className="space-y-2">
                {data.inspectionPlan.next7days.length === 0 ? (
                  <p className="text-sm text-muted-foreground">—</p>
                ) : (
                  data.inspectionPlan.next7days.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2"
                    >
                      <span className="text-sm font-medium">
                        {s.name[locale] ?? s.name.ru}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {tMap(`inspectionStatus.${s.inspectionStatus}`)}
                      </Badge>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">
                {t('next30days')}
              </h3>
              <div className="space-y-2">
                {data.inspectionPlan.next30days.length === 0 ? (
                  <p className="text-sm text-muted-foreground">—</p>
                ) : (
                  data.inspectionPlan.next30days.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2"
                    >
                      <span className="text-sm font-medium">
                        {s.name[locale] ?? s.name.ru}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {tMap(`inspectionStatus.${s.inspectionStatus}`)}
                      </Badge>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Download className="size-5 text-primary" />
            <CardTitle>{t('generateReport')}</CardTitle>
          </div>
          <CardDescription>{t('title')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Button
                onClick={handleJSONExport}
                disabled={generating !== null}
                data-testid="export-json"
              >
                <FileText className="size-4 mr-2" />
                {t('exportJSON')}
              </Button>
              <span className="text-xs text-muted-foreground">~{jsonSize}</span>
            </div>
            <div className="flex flex-col gap-2">
              <Button
                onClick={handleHTMLExport}
                disabled={generating !== null}
                data-testid="export-html"
              >
                <FileText className="size-4 mr-2" />
                {t('exportHTML')}
              </Button>
            </div>
          </div>

          {message && (
            <Alert
              variant={message.type === 'error' ? 'destructive' : 'default'}
              className="mt-4"
            >
              <AlertDescription>{message.text}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Separator />

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          <FileText className="mr-2 inline size-5 text-primary" />
          {t('title')} — CSV / GeoJSON / PDF
        </h2>
        <ExportPanel />
      </div>
    </div>
  );
}
