export type ConditionStatus = 'normal' | 'inspection' | 'repair' | 'critical' | 'missing';

export type InspectionStatus = 'current' | 'overdue' | 'due_soon' | 'never' | 'unknown';

export type StructureType = 'dam' | 'reservoir' | 'canal' | 'pumping_station' | 'spillway' | 'other';

export interface TrilingualText {
  ru: string;
  kk: string;
  en: string;
}

export type SignificanceLevel = 'critical' | 'high' | 'medium' | 'low';

export interface Efficiency {
  design: number;
  actual: number;
}

export interface StructureProperties {
  id: string;
  name: TrilingualText;
  type: StructureType;
  condition: ConditionStatus;
  inspectionStatus: InspectionStatus;
  district: string;
  basin: string;
  height?: number;
  length?: number;
  capacity?: number;
  yearBuilt?: number;
  efficiency?: Efficiency;
  wearPercentage?: number;
  significance?: SignificanceLevel;
  recommendation?: string;
  provenance: {
    source: string;
    confidence: 'high' | 'medium' | 'low';
    lastVerified: string;
  };
}

export interface StructureFeature {
  type: 'Feature';
  geometry: GeoJSON.Point | null;
  properties: StructureProperties;
}

export interface StructureCollection {
  type: 'FeatureCollection';
  features: StructureFeature[];
}

export interface StructureDetail extends StructureProperties {
  coordinates: { lon: number; lat: number } | null;
  administrativeLocation: {
    region: string;
    district: string;
    nearestSettlement: string;
  };
  technicalSpecs: {
    height?: number;
    length?: number;
    capacity?: number;
    yearBuilt?: number;
    designType?: string;
    materials?: string;
  };
}

export interface StructureFilters {
  district?: string | null;
  basin?: string | null;
  type?: string | null;
  condition?: string | null;
  inspectionStatus?: string | null;
  riskLevel?: string | null;
  efficiencyMin?: number | null;
  ageMin?: number | null;
  ageMax?: number | null;
}

export type UserRole = 'admin' | 'engineer' | 'inspector' | 'viewer';

export interface AuthUser {
  id: string;
  name: string;
  role: UserRole;
}

export interface InspectionRecord {
  id: string;
  structureId: string;
  date: string;
  inspectorName: string;
  findings: string;
  photoUrls: string[];
  conditionAtInspection: ConditionStatus;
}

export interface DocumentMeta {
  id: string;
  structureId: string;
  filename: string;
  fileType: string;
  fileSize: number;
  uploadedBy: string;
  uploadedAt: string;
  downloadUrl: string;
}

export interface RiskComponent {
  key: 'condition' | 'age' | 'efficiency' | 'significance' | 'weather' | 'inspection_overdue';
  label: string;
  score: number;
  weight: number;
  description: string;
}

export interface RiskScore {
  structureId: string;
  overall: number;
  components: RiskComponent[];
  explanation: string;
  recommendation: string;
  computedAt: string;
}

export interface DuplicateCandidate {
  id: string;
  structureIds: string[];
  reason: string;
  matchFields: string[];
}

export type OverrideField = 'inspection_interval' | 'repair_status';

export interface EngineerOverride {
  id: string;
  structureId: string;
  field: OverrideField;
  originalValue: string;
  newValue: string;
  reason: string;
  engineerName: string;
  timestamp: string;
}

export type ChatIntent =
  | 'list_critical'
  | 'list_repair'
  | 'list_inspection'
  | 'show_risk'
  | 'summarize_inspections'
  | 'explain_condition'
  | 'list_by_district'
  | 'list_by_basin'
  | 'general';

export type CopilotSourceType = 'inspection' | 'registry' | 'osm' | 'document' | 'risk_assessment';

export interface CopilotSource {
  id: string;
  type: CopilotSourceType;
  label: string;
  reference: string;
  structureId?: string;
}

export type CopilotCardType = 'structure' | 'risk' | 'inspection' | 'report';

export interface StructureCardData {
  type: 'structure';
  data: StructureDetail;
}

export interface RiskCardData {
  type: 'risk';
  data: RiskScore;
  structureId: string;
  structureName: string;
}

export interface InspectionCardData {
  type: 'inspection';
  data: InspectionRecord;
  structureName: string;
}

export interface ReportCardData {
  type: 'report';
  data: {
    title: string;
    summary: string;
    structureCount: number;
    structures: StructureDetail[];
  };
}

export type CopilotCard = StructureCardData | RiskCardData | InspectionCardData | ReportCardData;

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: CopilotSource[];
  cards?: CopilotCard[];
  isStreaming?: boolean;
}

export type DiscoverySource = 'osm' | 'satellite' | 'kazvodhoz' | 'manual';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export type EvidenceType = 'name_similarity' | 'distance' | 'type_agreement' | 'source_overlap';

export interface MatchEvidence {
  type: EvidenceType;
  label: string;
  value: string;
  score: number;
  agreement: boolean;
}

export type ReviewStatus = 'pending' | 'accepted' | 'linked' | 'rejected';

export type ReviewAction = 'accept' | 'link' | 'reject';

export interface DiscoveryCandidate {
  id: string;
  source: DiscoverySource;
  sourceName: TrilingualText;
  name: TrilingualText;
  type: StructureType;
  coordinates: { lon: number; lat: number } | null;
  district: string;
  basin: string;
  confidence: ConfidenceLevel;
  detectedAt: string;
  properties: {
    height?: number;
    length?: number;
    capacity?: number;
    yearBuilt?: number;
    osmId?: string;
    osmTags?: Record<string, string>;
    satelliteTile?: string;
  };
}

export interface MatchResult {
  candidateId: string;
  existingStructureId: string | null;
  matchScore: number;
  evidence: MatchEvidence[];
  reviewStatus: ReviewStatus;
}

export interface ReviewActionRecord {
  id: string;
  candidateId: string;
  action: ReviewAction;
  reviewerName: string;
  reason: string;
  timestamp: string;
}

export interface DiscoveryFilters {
  reviewStatus: ReviewStatus | 'all';
  searchQuery: string;
}
