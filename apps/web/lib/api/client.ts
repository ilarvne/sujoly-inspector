import { useQuery } from '@tanstack/react-query';
import { mockStructures, mockStructureById } from './mock-data';
import type { StructureCollection, StructureDetail, StructureFilters } from './types';

async function fetchStructures(filters?: StructureFilters): Promise<StructureCollection> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockStructures(filters);
}

async function fetchStructureDetail(id: string): Promise<StructureDetail | null> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockStructureById(id);
}

export function useStructuresGeoJSON(filters?: StructureFilters) {
  return useQuery({
    queryKey: ['structures', 'geojson', filters],
    queryFn: () => fetchStructures(filters),
  });
}

export function useStructureDetail(id: string | null) {
  return useQuery({
    queryKey: ['structure', id],
    queryFn: () => fetchStructureDetail(id!),
    enabled: !!id,
  });
}
