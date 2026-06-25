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
