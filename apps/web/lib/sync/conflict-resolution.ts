import type { FieldInspection, ConflictField } from '@/lib/db/types';

const COMPARABLE_FIELDS: Array<{ key: keyof FieldInspection; label: string }> = [
  { key: 'findings', label: 'Findings' },
  { key: 'condition', label: 'Condition' },
  { key: 'inspectorName', label: 'Inspector' },
  { key: 'inspectionDate', label: 'Date' },
  { key: 'gpsLat', label: 'Latitude' },
  { key: 'gpsLon', label: 'Longitude' },
];

export function detectConflicts(
  local: FieldInspection,
  server: Partial<FieldInspection>
): ConflictField[] {
  const conflicts: ConflictField[] = [];
  for (const { key, label } of COMPARABLE_FIELDS) {
    const localVal = local[key];
    const serverVal = server[key];
    if (serverVal !== undefined && String(localVal) !== String(serverVal)) {
      conflicts.push({
        field: key as string,
        label,
        localValue: localVal,
        serverValue: serverVal,
        resolution: null,
      });
    }
  }
  return conflicts;
}

export function applyResolution(
  _local: FieldInspection,
  conflicts: ConflictField[]
): Partial<FieldInspection> {
  const resolved: Record<string, unknown> = {};
  for (const conflict of conflicts) {
    if (conflict.resolution === 'local') {
      resolved[conflict.field] = conflict.localValue;
    } else if (conflict.resolution === 'server') {
      resolved[conflict.field] = conflict.serverValue;
    } else if (conflict.resolution === 'merge' && conflict.mergedValue !== undefined) {
      resolved[conflict.field] = conflict.mergedValue;
    }
  }
  return resolved as Partial<FieldInspection>;
}

export function hasUnresolvedConflicts(conflicts: ConflictField[]): boolean {
  return conflicts.some((c) => c.resolution === null);
}

export function resolveAllAsLocal(conflicts: ConflictField[]): ConflictField[] {
  return conflicts.map((c) => ({ ...c, resolution: 'local' as const }));
}

export function resolveAllAsServer(conflicts: ConflictField[]): ConflictField[] {
  return conflicts.map((c) => ({ ...c, resolution: 'server' as const }));
}
