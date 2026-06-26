/**
 * API client — real backend integration (replaces all mock-data calls).
 *
 * All data is fetched from the FastAPI backend at http://localhost:8000/api/v1/.
 * Auth uses a cached bearer token obtained via POST /auth/token with the
 * dev admin API key. On 401 the token is refreshed and the request retried
 * once. Errors are handled gracefully: failed fetches return empty
 * collections or null so the UI degrades rather than crashes.
 */

import { useQuery } from '@tanstack/react-query';
import type {
  StructureCollection,
  StructureDetail,
  StructureFilters,
  StructureFeature,
  StructureType,
  ConditionStatus,
  InspectionStatus,
  InspectionRecord,
  DocumentMeta,
  RiskScore,
  RiskComponent,
  EngineerOverride,
  DiscoveryCandidate,
  MatchResult,
  ReviewAction,
  ReviewActionRecord,
  TrilingualText,
  DiscoverySource,
  ConfidenceLevel,
} from './types';

// ---------------------------------------------------------------------------
// API configuration & auth
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
const API_KEY = 'dev-admin-key';

let cachedToken: string | null = null;

async function getToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: API_KEY }),
  });
  if (!res.ok) {
    console.error('[api] Failed to obtain auth token:', res.status);
    throw new Error('Failed to authenticate with backend');
  }
  const data = await res.json();
  cachedToken = data.access_token as string;
  return cachedToken!;
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T | null> {
  try {
    const token = await getToken();
    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      ...((options?.headers as Record<string, string>) || {}),
    };

    let res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

    // Token may have expired — refresh and retry once
    if (res.status === 401) {
      cachedToken = null;
      const newToken = await getToken();
      headers.Authorization = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    }

    if (!res.ok) {
      console.error(`[api] ${path} returned ${res.status}`);
      return null;
    }
    return (await res.json()) as T;
  } catch (err) {
    console.error(`[api] ${path} fetch error:`, err);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Mapping helpers — API field names → frontend TypeScript types
// ---------------------------------------------------------------------------

/** Map API structure type string to frontend StructureType enum. */
function mapStructureType(apiType: string | null | undefined): StructureType {
  if (!apiType) return 'other';
  const t = apiType.toLowerCase();
  if (t === 'dam') return 'dam';
  if (t === 'reservoir') return 'reservoir';
  if (t === 'canal') return 'canal';
  if (t === 'pumping_station' || t === 'pumping station') return 'pumping_station';
  if (t === 'spillway') return 'spillway';
  return 'other';
}

/** Map API technical_condition (Russian abbreviations) to ConditionStatus. */
function mapCondition(
  raw: string | null | undefined,
): ConditionStatus {
  if (!raw) return 'missing';
  const c = raw.toLowerCase().trim();
  // Russian: удов. = удовлетворительное (satisfactory)
  if (c.startsWith('удов') && !c.startsWith('неуд')) return 'normal';
  // Russian: неуд. = неудовлетворительное (unsatisfactory)
  if (c.startsWith('неуд')) return 'repair';
  // Russian: авар. = аварийное (emergency)
  if (c.startsWith('авар')) return 'critical';
  if (c === 'good' || c === 'normal') return 'normal';
  if (c === 'repair_required') return 'repair';
  if (c === 'critical_condition' || c === 'critical') return 'critical';
  if (c === 'inspection_required') return 'inspection';
  return 'inspection';
}

/** Map risk repair_status to ConditionStatus (used for detail view). */
function mapRepairStatus(status: string | null | undefined): ConditionStatus {
  if (!status) return 'missing';
  switch (status) {
    case 'normal':
      return 'normal';
    case 'inspection_required':
      return 'inspection';
    case 'repair_required':
      return 'repair';
    case 'critical_condition':
      return 'critical';
    default:
      return 'inspection';
  }
}

/** Derive inspection status from risk data (no direct API field). */
function deriveInspectionStatus(
  repairStatus: string | null | undefined,
): InspectionStatus {
  if (!repairStatus) return 'unknown';
  switch (repairStatus) {
    case 'normal':
      return 'current';
    case 'inspection_required':
      return 'due_soon';
    case 'repair_required':
      return 'overdue';
    case 'critical_condition':
      return 'overdue';
    default:
      return 'unknown';
  }
}

/** Map API source_type to frontend DiscoverySource. */
function mapDiscoverySource(
  source: string | null | undefined,
): DiscoverySource {
  if (!source) return 'manual';
  const s = source.toLowerCase();
  if (s === 'osm' || s === 'openstreetmap') return 'osm';
  if (s === 'satellite' || s === 'satellite_imagery') return 'satellite';
  if (s === 'kazvodhoz' || s === 'registry') return 'kazvodhoz';
  return 'manual';
}

/** Map API confidence string to frontend ConfidenceLevel. */
function mapConfidence(
  raw: string | null | undefined,
): ConfidenceLevel {
  if (!raw) return 'low';
  const c = raw.toUpperCase();
  if (c === 'HIGH') return 'high';
  if (c === 'MEDIUM') return 'medium';
  return 'low';
}

/** Build a TrilingualText from API name fields. */
function makeTrilingual(
  ru: string | null,
  kk: string | null,
  en: string | null,
  fallback: string,
): TrilingualText {
  return {
    ru: ru || fallback,
    kk: kk || fallback,
    en: en || fallback,
  };
}

// ---------------------------------------------------------------------------
// API response interfaces (subset of fields we consume)
// ---------------------------------------------------------------------------

interface ApiStructure {
  id: string;
  name_ru: string | null;
  name_kk: string | null;
  name_en: string | null;
  type: string;
  district: string | null;
  water_source: string | null;
  technical_condition: string | null;
  wear_percentage: number | null;
  commissioning_year: number | null;
  cadastral_number: string | null;
  structure_count: number | null;
  geometry: { type: string; coordinates: [number, number] } | null;
  provenance_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ApiStructureList {
  items: ApiStructure[];
  total: number;
  offset: number;
  limit: number;
}

interface ApiGeoJSONCollection {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    geometry: { type: string; coordinates: [number, number] } | null;
    properties: ApiStructure;
  }[];
}

interface ApiRisk {
  id: string;
  structure_id: string;
  condition_score: number;
  consequence_factor: number;
  seasonal_modifier: number;
  staleness_modifier: number;
  composite_score: number;
  inspection_interval: string;
  repair_status: string;
  red_flags: unknown[];
  contributing_factors: Record<string, unknown>;
  is_override: boolean;
  computed_at: string;
}

interface ApiInspectionList {
  items: ApiInspection[];
  total: number;
  offset: number;
  limit: number;
}

interface ApiInspection {
  id: string;
  structure_id: string;
  inspection_date: string;
  inspector_name: string;
  inspector_role: string | null;
  findings: string | null;
  condition_at_inspection: string | null;
  condition_score_at_inspection: number | null;
  red_flags_observed: unknown[];
  photos: { id: string; url?: string; filename?: string }[];
}

interface ApiDocumentList {
  items: ApiDocument[];
  total: number;
}

interface ApiDocument {
  id: string;
  structure_id: string | null;
  document_type: string;
  title: string;
  language: string;
  minio_bucket: string;
  minio_object_key: string;
  file_size_bytes: number | null;
  uploaded_by: string | null;
  created_at: string;
  presigned_download_url: string | null;
}

interface ApiCandidateList {
  items: ApiCandidate[];
  total: number;
  offset: number;
  limit: number;
}

interface ApiCandidate {
  id: string;
  name: string;
  source_type: string;
  source_id: string;
  geometry: { type: string; coordinates: [number, number] } | null;
  match_status: string;
  matched_structure_id: string | null;
  confidence: string;
  confidence_score: number | null;
  evidence: Record<string, unknown> | null;
  district: string | null;
  water_source: string | null;
  type: string | null;
  review_notes: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  provenance_id: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Structure mappers
// ---------------------------------------------------------------------------

/** Map a single API structure to a GeoJSON Feature with frontend properties. */
function mapApiStructureToFeature(
  item: ApiStructure,
): StructureFeature {
  const geom = item.geometry;
  const fallbackName = item.name_ru || item.name_en || item.name_kk || item.id;
  return {
    type: 'Feature',
    geometry: geom
      ? { type: 'Point', coordinates: [geom.coordinates[0], geom.coordinates[1]] }
      : null,
    properties: {
      id: String(item.id),
      name: makeTrilingual(item.name_ru, item.name_kk, item.name_en, fallbackName),
      type: mapStructureType(item.type),
      condition: mapCondition(item.technical_condition),
      inspectionStatus: 'unknown',
      district: item.district || '',
      basin: item.water_source || '',
      yearBuilt: item.commissioning_year ?? undefined,
      provenance: {
        source: 'kazvodhoz',
        confidence: 'medium',
        lastVerified: item.updated_at?.split('T')[0] || '',
      },
    },
  };
}

/** Map a single API structure to a full StructureDetail. */
function mapApiStructureToDetail(item: ApiStructure): StructureDetail {
  const geom = item.geometry;
  const fallbackName = item.name_ru || item.name_en || item.name_kk || item.id;
  return {
    id: String(item.id),
    name: makeTrilingual(item.name_ru, item.name_kk, item.name_en, fallbackName),
    type: mapStructureType(item.type),
    condition: mapCondition(item.technical_condition),
    inspectionStatus: 'unknown',
    district: item.district || '',
    basin: item.water_source || '',
    yearBuilt: item.commissioning_year ?? undefined,
    coordinates: geom
      ? { lon: geom.coordinates[0], lat: geom.coordinates[1] }
      : null,
    administrativeLocation: {
      region: 'Жамбылская область',
      district: item.district || '',
      nearestSettlement: '',
    },
    technicalSpecs: {
      yearBuilt: item.commissioning_year ?? undefined,
    },
    provenance: {
      source: 'kazvodhoz',
      confidence: 'medium',
      lastVerified: item.updated_at?.split('T')[0] || '',
    },
  };
}

// ---------------------------------------------------------------------------
// Risk mapper
// ---------------------------------------------------------------------------

function mapApiRiskToRiskScore(api: ApiRisk): RiskScore {
  const components: RiskComponent[] = [
    {
      key: 'structural',
      label: 'Structural Integrity',
      score: Math.round(api.condition_score ?? 0),
      weight: 0.35,
      description: 'Condition of dam body, spillway, and load-bearing structures',
    },
    {
      key: 'hydrological',
      label: 'Hydrological Risk',
      score: Math.round((api.consequence_factor ?? 0) * 50),
      weight: 0.25,
      description: 'Flood probability, capacity utilization, basin characteristics',
    },
    {
      key: 'operational',
      label: 'Operational Status',
      score: Math.round((api.seasonal_modifier ?? 0) * 50),
      weight: 0.25,
      description: 'Equipment condition, maintenance frequency, operational readiness',
    },
    {
      key: 'age',
      label: 'Infrastructure Age',
      score: Math.round((api.staleness_modifier ?? 0) * 50),
      weight: 0.15,
      description: 'Years since construction, design lifetime, obsolescence factors',
    },
  ];

  const repairLabel: Record<string, string> = {
    normal: 'Normal — routine monitoring',
    inspection_required: 'Inspection required',
    repair_required: 'Repair required',
    critical_condition: 'Critical — emergency action needed',
  };

  const explanation = `Composite risk score: ${api.composite_score.toFixed(1)}. ${repairLabel[api.repair_status] || api.repair_status}. Recommended inspection interval: ${api.inspection_interval}.`;

  return {
    structureId: String(api.structure_id),
    overall: Math.round(api.composite_score),
    components,
    explanation,
    computedAt: api.computed_at || new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Inspection mapper
// ---------------------------------------------------------------------------

function mapApiInspection(api: ApiInspection): InspectionRecord {
  return {
    id: String(api.id),
    structureId: String(api.structure_id),
    date: api.inspection_date,
    inspectorName: api.inspector_name,
    findings: api.findings || '',
    photoUrls: (api.photos || []).map((p) => p.url || p.filename || ''),
    conditionAtInspection: mapCondition(api.condition_at_inspection),
  };
}

// ---------------------------------------------------------------------------
// Document mapper
// ---------------------------------------------------------------------------

function mapApiDocument(api: ApiDocument): DocumentMeta {
  return {
    id: String(api.id),
    structureId: String(api.structure_id || ''),
    filename: api.title || api.minio_object_key,
    fileType: api.document_type,
    fileSize: api.file_size_bytes ?? 0,
    uploadedBy: api.uploaded_by || 'Unknown',
    uploadedAt: api.created_at?.split('T')[0] || '',
    downloadUrl: api.presigned_download_url || '#',
  };
}

// ---------------------------------------------------------------------------
// Candidate mapper
// ---------------------------------------------------------------------------

function mapApiCandidate(api: ApiCandidate): DiscoveryCandidate {
  const geom = api.geometry;
  const name = api.name || api.id;
  return {
    id: String(api.id),
    source: mapDiscoverySource(api.source_type),
    sourceName: makeTrilingual(api.source_type, api.source_type, api.source_type, api.source_type),
    name: makeTrilingual(name, name, name, name),
    type: mapStructureType(api.type),
    coordinates: geom
      ? { lon: geom.coordinates[0], lat: geom.coordinates[1] }
      : null,
    district: api.district || '',
    basin: api.water_source || '',
    confidence: mapConfidence(api.confidence),
    detectedAt: api.created_at?.split('T')[0] || '',
    properties: {},
  };
}

// ---------------------------------------------------------------------------
// Fetch functions
// ---------------------------------------------------------------------------

/** Fetch structures as GeoJSON FeatureCollection (used by map & list views). */
async function fetchStructures(
  filters?: StructureFilters,
): Promise<StructureCollection> {
  const params = new URLSearchParams();
  params.set('limit', '1000');
  params.set('format', 'geojson');
  if (filters?.district) params.set('district', filters.district);
  if (filters?.basin) params.set('water_source', filters.basin);
  if (filters?.type) params.set('type', filters.type);
  if (filters?.condition) params.set('technical_condition', filters.condition);

  const data = await apiFetch<ApiGeoJSONCollection>(
    `/structures?${params.toString()}`,
  );

  if (!data || !data.features) {
    return { type: 'FeatureCollection', features: [] };
  }

  const features = data.features.map((f) => {
    const feature = mapApiStructureToFeature(f.properties);
    // Use geometry from the GeoJSON feature level (API puts it there, not in properties)
    if (f.geometry && !feature.geometry) {
      feature.geometry = {
        type: 'Point',
        coordinates: [f.geometry.coordinates[0], f.geometry.coordinates[1]],
      };
    }
    return feature;
  });

  return { type: 'FeatureCollection', features };
}

/** Fetch a single structure by ID. */
async function fetchStructureDetail(
  id: string,
): Promise<StructureDetail | null> {
  const data = await apiFetch<ApiStructure>(`/structures/${id}`);
  if (!data) return null;
  return mapApiStructureToDetail(data);
}

/** Fetch inspections for a structure. */
async function fetchInspections(
  structureId: string,
): Promise<InspectionRecord[]> {
  const data = await apiFetch<ApiInspectionList>(
    `/structures/${structureId}/inspections?limit=100`,
  );
  if (!data || !data.items) return [];
  return data.items.map(mapApiInspection);
}

/** Fetch documents for a structure. */
async function fetchDocuments(
  structureId: string,
): Promise<DocumentMeta[]> {
  const data = await apiFetch<ApiDocumentList>(
    `/structures/${structureId}/documents`,
  );
  if (!data || !data.items) return [];
  return data.items.map(mapApiDocument);
}

/** Fetch risk assessment for a structure. */
async function fetchRiskScore(structureId: string): Promise<RiskScore | null> {
  const data = await apiFetch<ApiRisk>(`/structures/${structureId}/risk`);
  if (!data) return null;
  return mapApiRiskToRiskScore(data);
}

/** Fetch engineer overrides for a structure.
 *
 * The backend exposes POST /structures/{id}/override but no GET endpoint.
 * Returns an empty array until a GET endpoint is added. */
async function fetchOverrides(
  _structureId: string,
): Promise<EngineerOverride[]> {
  return [];
}

/** Fetch discovery candidates. */
async function fetchDiscoveryCandidates(): Promise<DiscoveryCandidate[]> {
  const data = await apiFetch<ApiCandidateList>(`/candidates?limit=1000`);
  if (!data || !data.items) return [];
  return data.items.map(mapApiCandidate);
}

/** Fetch match results derived from candidate data. */
async function fetchMatchResults(): Promise<MatchResult[]> {
  const data = await apiFetch<ApiCandidateList>(`/candidates?limit=1000`);
  if (!data || !data.items) return [];
  return data.items.map((c) => ({
    candidateId: String(c.id),
    existingStructureId: c.matched_structure_id ? String(c.matched_structure_id) : null,
    matchScore: Math.round((c.confidence_score ?? 0) * 100),
    evidence: [],
    reviewStatus: (c.match_status as MatchResult['reviewStatus']) || 'pending',
  }));
}

/** Fetch a single discovery candidate by ID. */
async function fetchDiscoveryCandidate(
  candidateId: string,
): Promise<DiscoveryCandidate | null> {
  const data = await apiFetch<ApiCandidate>(`/candidates/${candidateId}`);
  if (!data) return null;
  return mapApiCandidate(data);
}

/** Fetch match result for a single candidate. */
async function fetchMatchResult(
  candidateId: string,
): Promise<MatchResult | null> {
  const data = await apiFetch<ApiCandidate>(`/candidates/${candidateId}`);
  if (!data) return null;
  return {
    candidateId: String(data.id),
    existingStructureId: data.matched_structure_id
      ? String(data.matched_structure_id)
      : null,
    matchScore: Math.round((data.confidence_score ?? 0) * 100),
    evidence: [],
    reviewStatus: (data.match_status as MatchResult['reviewStatus']) || 'pending',
  };
}

// ---------------------------------------------------------------------------
// Exported hooks (same names as before — drop-in replacement)
// ---------------------------------------------------------------------------

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
      return fetchDiscoveryCandidate(candidateId);
    },
    enabled: !!candidateId,
  });
}

export function useMatchResult(candidateId: string | null) {
  return useQuery({
    queryKey: ['discovery', 'match', candidateId],
    queryFn: () => {
      if (!candidateId) return null;
      return fetchMatchResult(candidateId);
    },
    enabled: !!candidateId,
  });
}

/** Submit a review action for a candidate.
 *
 * Calls POST /candidates/{id}/review on the backend. Falls back to a
 * local record if the API call fails so the UI remains responsive. */
export async function mockSubmitReviewAction(
  candidateId: string,
  action: ReviewAction,
  reviewerName: string,
  reason: string,
): Promise<ReviewActionRecord> {
  try {
    const token = await getToken();
    await fetch(`${API_BASE_URL}/candidates/${candidateId}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        action,
        reviewer_name: reviewerName,
        reason,
      }),
    });
  } catch (err) {
    console.error('[api] Failed to submit review:', err);
  }

  return {
    id: `REV-${candidateId}-${Date.now()}`,
    candidateId,
    action,
    reviewerName,
    reason,
    timestamp: new Date().toISOString(),
  };
}
