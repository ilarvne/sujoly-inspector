import type {
  ConditionStatus,
  InspectionStatus,
  StructureType,
  TrilingualText,
} from '@/lib/api/types';
import {
  mockStructures,
  mockRiskScore,
  detectDuplicateStructures,
} from '@/lib/api/mock-data';
import { STATUS_COLORS_HEX } from '@/lib/constants';

export interface ReportStructureSummary {
  id: string;
  name: TrilingualText;
  type: StructureType;
  district: string;
  riskScore: number;
  condition: ConditionStatus;
  inspectionStatus: InspectionStatus;
}

export interface ReportData {
  generatedAt: string;
  totalStructures: number;
  statusDistribution: Record<ConditionStatus, number>;
  avgRiskScore: number;
  missingCoordsCount: number;
  duplicateCount: number;
  byType: Record<StructureType, number>;
  topRisky: ReportStructureSummary[];
  inspectionPlan: {
    next7days: ReportStructureSummary[];
    next30days: ReportStructureSummary[];
  };
}

export interface ReportLabels {
  title: string;
  overview: string;
  totalStructures: string;
  statusDistribution: string;
  avgRiskScore: string;
  missingCoords: string;
  duplicates: string;
  byType: string;
  topRisky: string;
  inspectionPlan: string;
  next7days: string;
  next30days: string;
  rank: string;
  name: string;
  type: string;
  district: string;
  riskScore: string;
  condition: string;
  generated: string;
  conditionLabels: Record<string, string>;
  structureTypeLabels: Record<string, string>;
  inspectionStatusLabels: Record<string, string>;
}

export function generateReportData(): ReportData {
  const collection = mockStructures();
  const features = collection.features;

  const statusDistribution: Record<ConditionStatus, number> = {
    normal: 0,
    inspection: 0,
    repair: 0,
    critical: 0,
    missing: 0,
  };

  const byType: Record<StructureType, number> = {
    dam: 0,
    reservoir: 0,
    canal: 0,
    pumping_station: 0,
    spillway: 0,
    other: 0,
  };

  let missingCoordsCount = 0;
  let totalRisk = 0;

  const summaries: ReportStructureSummary[] = features.map((f) => {
    const { properties } = f;
    statusDistribution[properties.condition]++;
    byType[properties.type]++;

    const isMissing =
      f.geometry === null ||
      (f.geometry.coordinates[0] === 0 && f.geometry.coordinates[1] === 0);
    if (isMissing) missingCoordsCount++;

    const risk = mockRiskScore(properties.id);
    totalRisk += risk.overall;

    return {
      id: properties.id,
      name: properties.name,
      type: properties.type,
      district: properties.district,
      riskScore: risk.overall,
      condition: properties.condition,
      inspectionStatus: properties.inspectionStatus,
    };
  });

  const avgRiskScore =
    features.length > 0 ? Math.round(totalRisk / features.length) : 0;
  const duplicateCount = detectDuplicateStructures().length;

  const topRisky = [...summaries]
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, 10);

  const next7days = summaries
    .filter(
      (s) =>
        s.inspectionStatus === 'overdue' || s.inspectionStatus === 'due_soon',
    )
    .sort((a, b) => b.riskScore - a.riskScore);

  const next30days = summaries
    .filter(
      (s) =>
        s.inspectionStatus === 'due_soon' || s.inspectionStatus === 'current',
    )
    .sort((a, b) => b.riskScore - a.riskScore);

  return {
    generatedAt: new Date().toISOString(),
    totalStructures: features.length,
    statusDistribution,
    avgRiskScore,
    missingCoordsCount,
    duplicateCount,
    byType,
    topRisky,
    inspectionPlan: {
      next7days,
      next30days,
    },
  };
}

export function generateReportJSON(): string {
  return JSON.stringify(generateReportData(), null, 2);
}

function riskColorHex(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 40) return '#f97316';
  return '#22c55e';
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function badgeHtml(label: string, color: string): string {
  return `<span class="badge" style="background:${color}">${escapeHtml(label)}</span>`;
}

export function generateReportHTML(
  locale: 'ru' | 'kk' | 'en',
  labels: ReportLabels,
): string {
  const data = generateReportData();
  const generatedDate = new Date(data.generatedAt).toLocaleString(locale);

  const conditions: ConditionStatus[] = [
    'normal',
    'inspection',
    'repair',
    'critical',
    'missing',
  ];
  const types: StructureType[] = [
    'dam',
    'reservoir',
    'canal',
    'pumping_station',
    'spillway',
    'other',
  ];

  const statCards = [
    { label: labels.totalStructures, value: String(data.totalStructures) },
    {
      label: labels.avgRiskScore,
      value: `${data.avgRiskScore} / 100`,
    },
    { label: labels.missingCoords, value: String(data.missingCoordsCount) },
    { label: labels.duplicates, value: String(data.duplicateCount) },
  ]
    .map(
      (s) => `
      <div class="stat-card">
        <span class="stat-label">${escapeHtml(s.label)}</span>
        <span class="stat-value">${escapeHtml(s.value)}</span>
      </div>`,
    )
    .join('');

  const statusRows = conditions
    .map((c) => {
      const count = data.statusDistribution[c];
      const pct =
        data.totalStructures > 0
          ? Math.round((count / data.totalStructures) * 100)
          : 0;
      return `
        <tr>
          <td>${badgeHtml(labels.conditionLabels[c] ?? c, STATUS_COLORS_HEX[c] ?? '#64748b')}</td>
          <td>${count}</td>
          <td>
            <div class="bar-container">
              <div class="bar-fill" style="width:${pct}%;background:${STATUS_COLORS_HEX[c] ?? '#64748b'}"></div>
            </div>
            <span class="bar-pct">${pct}%</span>
          </td>
        </tr>`;
    })
    .join('');

  const typeRows = types
    .filter((t) => data.byType[t] > 0)
    .map((t) => {
      const count = data.byType[t];
      const pct =
        data.totalStructures > 0
          ? Math.round((count / data.totalStructures) * 100)
          : 0;
      return `
        <tr>
          <td>${escapeHtml(labels.structureTypeLabels[t] ?? t)}</td>
          <td>${count}</td>
          <td>
            <div class="bar-container">
              <div class="bar-fill" style="width:${pct}%"></div>
            </div>
            <span class="bar-pct">${pct}%</span>
          </td>
        </tr>`;
    })
    .join('');

  const topRiskyRows = data.topRisky
    .map((s, i) => {
      const name = s.name[locale] ?? s.name.ru;
      return `
        <tr>
          <td>${i + 1}</td>
          <td>${escapeHtml(name)}</td>
          <td>${escapeHtml(labels.structureTypeLabels[s.type] ?? s.type)}</td>
          <td>${escapeHtml(s.district)}</td>
          <td>${badgeHtml(String(s.riskScore), riskColorHex(s.riskScore))}</td>
          <td>${badgeHtml(labels.conditionLabels[s.condition] ?? s.condition, STATUS_COLORS_HEX[s.condition] ?? '#64748b')}</td>
        </tr>`;
    })
    .join('');

  const planListHtml = (items: ReportStructureSummary[]) => {
    if (items.length === 0) {
      return `<p class="empty-list">—</p>`;
    }
    return items
      .map((s) => {
        const name = s.name[locale] ?? s.name.ru;
        const statusLabel =
          labels.inspectionStatusLabels[s.inspectionStatus] ??
          s.inspectionStatus;
        return `
          <div class="list-item">
            <span class="list-item-name">${escapeHtml(name)}</span>
            <span class="list-item-status">${escapeHtml(statusLabel)}</span>
          </div>`;
      })
      .join('');
  };

  return `<!DOCTYPE html>
<html lang="${locale}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(labels.title)}</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      margin: 0;
      padding: 24px;
      background: #f1f5f9;
      color: #1e293b;
      line-height: 1.5;
    }
    h1 {
      color: #0b4f6c;
      font-size: 1.75rem;
      margin: 0 0 4px 0;
      padding-bottom: 10px;
      border-bottom: 2px solid #0b4f6c;
    }
    h2 {
      color: #0b4f6c;
      font-size: 1.25rem;
      margin: 28px 0 12px 0;
    }
    .generated-at {
      color: #64748b;
      font-size: 0.8125rem;
      margin: 0 0 20px 0;
    }
    .section { margin-bottom: 24px; }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }
    .stat-card {
      background: #fff;
      padding: 14px 16px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stat-label {
      font-size: 0.8125rem;
      color: #64748b;
      display: block;
      margin-bottom: 4px;
    }
    .stat-value {
      font-size: 1.5rem;
      font-weight: 700;
      color: #0b4f6c;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      background: #fff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    th {
      background: #0b4f6c;
      color: #fff;
      padding: 10px 12px;
      text-align: left;
      font-size: 0.8125rem;
      font-weight: 600;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 0.875rem;
      vertical-align: middle;
    }
    tr:last-child td { border-bottom: none; }
    .badge {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      color: #fff;
      white-space: nowrap;
    }
    .bar-container {
      display: inline-block;
      width: 120px;
      height: 8px;
      background: #e2e8f0;
      border-radius: 4px;
      overflow: hidden;
      vertical-align: middle;
      margin-right: 6px;
    }
    .bar-fill {
      height: 100%;
      background: #0b4f6c;
      border-radius: 4px;
    }
    .bar-pct {
      font-size: 0.75rem;
      color: #64748b;
    }
    .list-item {
      padding: 8px 14px;
      background: #fff;
      border-radius: 6px;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .list-item-name { font-weight: 500; font-size: 0.875rem; }
    .list-item-status { font-size: 0.8125rem; color: #64748b; }
    .empty-list { color: #94a3b8; font-style: italic; padding: 8px 0; }
    .plan-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    @media (max-width: 768px) {
      .plan-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <h1>${escapeHtml(labels.title)}</h1>
  <p class="generated-at">${escapeHtml(labels.generated)}: ${escapeHtml(generatedDate)}</p>

  <div class="section">
    <h2>${escapeHtml(labels.overview)}</h2>
    <div class="stats-grid">${statCards}</div>
  </div>

  <div class="section">
    <h2>${escapeHtml(labels.statusDistribution)}</h2>
    <table>
      <thead>
        <tr>
          <th>${escapeHtml(labels.condition)}</th>
          <th>#</th>
          <th>%</th>
        </tr>
      </thead>
      <tbody>${statusRows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>${escapeHtml(labels.byType)}</h2>
    <table>
      <thead>
        <tr>
          <th>${escapeHtml(labels.type)}</th>
          <th>#</th>
          <th>%</th>
        </tr>
      </thead>
      <tbody>${typeRows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>${escapeHtml(labels.topRisky)}</h2>
    <table>
      <thead>
        <tr>
          <th>${escapeHtml(labels.rank)}</th>
          <th>${escapeHtml(labels.name)}</th>
          <th>${escapeHtml(labels.type)}</th>
          <th>${escapeHtml(labels.district)}</th>
          <th>${escapeHtml(labels.riskScore)}</th>
          <th>${escapeHtml(labels.condition)}</th>
        </tr>
      </thead>
      <tbody>${topRiskyRows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>${escapeHtml(labels.inspectionPlan)}</h2>
    <div class="plan-grid">
      <div>
        <h3 style="font-size:1rem;color:#475569;margin:0 0 8px 0">${escapeHtml(labels.next7days)}</h3>
        ${planListHtml(data.inspectionPlan.next7days)}
      </div>
      <div>
        <h3 style="font-size:1rem;color:#475569;margin:0 0 8px 0">${escapeHtml(labels.next30days)}</h3>
        ${planListHtml(data.inspectionPlan.next30days)}
      </div>
    </div>
  </div>
</body>
</html>`;
}
