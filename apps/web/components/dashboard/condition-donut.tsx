'use client';

import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useTranslations } from 'next-intl';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import type { ConditionStatus, StructureFeature } from '@/lib/api/types';

interface ConditionDonutProps {
  features: StructureFeature[];
  isLoading: boolean;
}

const CONDITIONS: ConditionStatus[] = ['normal', 'inspection', 'repair', 'critical', 'missing'];

export function ConditionDonut({ features, isLoading }: ConditionDonutProps) {
  const tDash = useTranslations('dashboard');
  const tMap = useTranslations('map');

  const chartData = useMemo(
    () =>
      CONDITIONS.map((condition) => ({
        name: tMap(`condition.${condition}`),
        condition,
        value: features.filter((f) => f.properties.condition === condition).length,
      })).filter((entry) => entry.value > 0),
    [features, tMap],
  );

  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        {tDash('noData')}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
        >
          {chartData.map((entry) => (
            <Cell key={entry.condition} fill={STATUS_COLORS_HEX[entry.condition]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
