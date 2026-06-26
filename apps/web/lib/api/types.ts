export type ConditionStatus = 'normal' | 'inspection' | 'repair' | 'critical' | 'missing';

export type InspectionStatus = 'current' | 'overdue' | 'due_soon' | 'never' | 'unknown';

export type StructureType = 'dam' | 'reservoir' | 'canal' | 'pumping_station' | 'spillway' | 'other';

export interface TrilingualText {
  ru: string;
  kk: string;
  en: string;
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
  key: 'structural' | 'hydrological' | 'operational' | 'age';
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
  computedAt: string;
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
