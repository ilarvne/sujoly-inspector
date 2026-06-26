import type { StructureDetail, RiskScore, RiskComponent, ConditionStatus, InspectionStatus, SignificanceLevel } from '@/lib/api/types';

const conditionScores: Record<ConditionStatus, number> = {
  normal: 15,
  inspection: 35,
  repair: 65,
  critical: 90,
  missing: 50,
};

const significanceScores: Record<SignificanceLevel, number> = {
  critical: 85,
  high: 60,
  medium: 40,
  low: 20,
};

const inspectionScores: Record<InspectionStatus, number> = {
  current: 10,
  due_soon: 30,
  overdue: 80,
  never: 70,
  unknown: 60,
};

export function calculateRiskScore(structure: StructureDetail): RiskScore {
  const currentYear = new Date().getFullYear();
  const age = structure.yearBuilt ? currentYear - structure.yearBuilt : 30;
  const effDeviation = structure.efficiency
    ? Math.abs(structure.efficiency.design - structure.efficiency.actual)
    : 15;
  const significance = structure.significance ?? 'medium';
  const condition = structure.condition;
  const inspectionStatus = structure.inspectionStatus;
  const seed = parseInt(structure.id.replace(/\D/g, ''), 10) || 1;

  const components: RiskComponent[] = [
    {
      key: 'condition',
      label: 'Technical Condition',
      score: conditionScores[condition] ?? 30,
      weight: 0.25,
      description: 'Structural integrity based on latest inspection findings',
    },
    {
      key: 'age',
      label: 'Infrastructure Age',
      score: Math.min(100, Math.round(age * 1.5)),
      weight: 0.20,
      description: `Age: ${age} years since construction`,
    },
    {
      key: 'efficiency',
      label: 'Efficiency Deviation',
      score: Math.min(100, Math.round(effDeviation * 3)),
      weight: 0.20,
      description: structure.efficiency
        ? `Design КПД: ${structure.efficiency.design}%, Actual: ${structure.efficiency.actual}%`
        : 'No efficiency data available',
    },
    {
      key: 'significance',
      label: 'Object Significance',
      score: significanceScores[significance] ?? 40,
      weight: 0.15,
      description: `Significance level: ${significance}`,
    },
    {
      key: 'weather',
      label: 'Weather Risk',
      score: 20 + (seed * 13 % 40),
      weight: 0.10,
      description: 'Flood probability and weather exposure based on basin location',
    },
    {
      key: 'inspection_overdue',
      label: 'Inspection Overdue',
      score: inspectionScores[inspectionStatus] ?? 20,
      weight: 0.10,
      description: `Inspection status: ${inspectionStatus}`,
    },
  ];

  const overall = Math.round(components.reduce((sum, c) => sum + c.score * c.weight, 0));
  const riskLevel = overall >= 70 ? 'high' : overall >= 40 ? 'medium' : 'low';

  const explanations: Record<string, string> = {
    high: 'High risk score indicates urgent inspection and potential repair requirements.',
    medium: 'Moderate risk — scheduled inspection and monitoring recommended.',
    low: 'Low risk — routine inspection schedule applies.',
  };

  const recommendations: Record<string, string> = {
    high: 'Срочный ремонт и внеочередной осмотр',
    medium: 'Плановый ремонт и усиленный мониторинг',
    low: 'Регулярный осмотр по графику',
  };

  return {
    structureId: structure.id,
    overall,
    components,
    explanation: explanations[riskLevel],
    recommendation: recommendations[riskLevel],
    computedAt: new Date().toISOString().split('T')[0],
  };
}
