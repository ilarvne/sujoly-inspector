import { useQuery } from '@tanstack/react-query';
import { mockStructures, mockStructureById, mockInspections, mockDocuments, mockRiskScore, mockOverrides, mockDiscoveryCandidates, mockMatchResults, mockMatchResultByCandidateId, mockDiscoveryCandidateById, mockSubmitReview } from './mock-data';
import type { StructureCollection, StructureDetail, StructureFilters, InspectionRecord, DocumentMeta, RiskScore, EngineerOverride, DiscoveryCandidate, MatchResult, ReviewAction, ReviewActionRecord } from './types';

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

async function fetchInspections(structureId: string): Promise<InspectionRecord[]> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockInspections(structureId);
}

async function fetchDocuments(structureId: string): Promise<DocumentMeta[]> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockDocuments(structureId);
}

async function fetchRiskScore(structureId: string): Promise<RiskScore> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockRiskScore(structureId);
}

async function fetchOverrides(structureId: string): Promise<EngineerOverride[]> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockOverrides(structureId);
}

export function useInspections(structureId: string | null) {
  return useQuery({
    queryKey: ['inspections', structureId],
    queryFn: () => fetchInspections(structureId!),
    enabled: !!structureId,
  });
}

export function useDocuments(structureId: string | null) {
  return useQuery({
    queryKey: ['documents', structureId],
    queryFn: () => fetchDocuments(structureId!),
    enabled: !!structureId,
  });
}

export function useRiskScore(structureId: string | null) {
  return useQuery({
    queryKey: ['risk-score', structureId],
    queryFn: () => fetchRiskScore(structureId!),
    enabled: !!structureId,
  });
}

export function useOverrides(structureId: string | null) {
  return useQuery({
    queryKey: ['overrides', structureId],
    queryFn: () => fetchOverrides(structureId!),
    enabled: !!structureId,
  });
}

async function fetchDiscoveryCandidates(): Promise<DiscoveryCandidate[]> {
  await new Promise((resolve) => setTimeout(resolve, 150));
  return mockDiscoveryCandidates();
}

async function fetchMatchResults(): Promise<MatchResult[]> {
  await new Promise((resolve) => setTimeout(resolve, 150));
  return mockMatchResults();
}

export function useDiscoveryCandidates() {
  return useQuery({
    queryKey: ['discovery', 'candidates'],
    queryFn: () => fetchDiscoveryCandidates(),
  });
}

export function useMatchResults() {
  return useQuery({
    queryKey: ['discovery', 'matches'],
    queryFn: () => fetchMatchResults(),
  });
}

export function useDiscoveryCandidate(candidateId: string | null) {
  return useQuery({
    queryKey: ['discovery', 'candidate', candidateId],
    queryFn: () => {
      if (!candidateId) return null;
      return Promise.resolve(mockDiscoveryCandidateById(candidateId));
    },
    enabled: !!candidateId,
  });
}

export function useMatchResult(candidateId: string | null) {
  return useQuery({
    queryKey: ['discovery', 'match', candidateId],
    queryFn: () => {
      if (!candidateId) return null;
      return Promise.resolve(mockMatchResultByCandidateId(candidateId));
    },
    enabled: !!candidateId,
  });
}

export function mockSubmitReviewAction(candidateId: string, action: ReviewAction, reviewerName: string, reason: string): ReviewActionRecord {
  return mockSubmitReview(candidateId, action, reviewerName, reason);
}
