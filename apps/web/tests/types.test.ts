import { describe, it, expect } from 'vitest';
import { mockStructures, mockStructureById } from '@/lib/api/mock-data';

const validConditions = ['normal', 'inspection', 'repair', 'critical', 'missing'];
const validInspectionStatuses = ['current', 'overdue', 'due_soon', 'never', 'unknown'];
const validTypes = ['dam', 'reservoir', 'canal', 'pumping_station', 'spillway', 'other'];

describe('StructureCollection type validation', () => {
  const collection = mockStructures();

  it('has type FeatureCollection', () => {
    expect(collection.type).toBe('FeatureCollection');
  });

  it('features is an array of StructureFeature objects', () => {
    for (const feature of collection.features) {
      expect(feature.type).toBe('Feature');
    }
  });
});

describe('StructureProperties type validation', () => {
  const collection = mockStructures();

  it('each feature has required properties fields', () => {
    for (const feature of collection.features) {
      const props = feature.properties;
      expect(props.id).toBeDefined();
      expect(typeof props.id).toBe('string');
      expect(props.name).toBeDefined();
      expect(typeof props.name.ru).toBe('string');
      expect(typeof props.name.kk).toBe('string');
      expect(typeof props.name.en).toBe('string');
      expect(props.type).toBeDefined();
      expect(props.condition).toBeDefined();
      expect(props.district).toBeDefined();
      expect(props.basin).toBeDefined();
      expect(props.provenance).toBeDefined();
    }
  });

  it('condition values are within the ConditionStatus union', () => {
    for (const feature of collection.features) {
      expect(validConditions).toContain(feature.properties.condition);
    }
  });

  it('inspectionStatus values are within the InspectionStatus union', () => {
    for (const feature of collection.features) {
      expect(validInspectionStatuses).toContain(feature.properties.inspectionStatus);
    }
  });

  it('type values are within the StructureType union', () => {
    for (const feature of collection.features) {
      expect(validTypes).toContain(feature.properties.type);
    }
  });

  it('provenance has source, confidence, and lastVerified', () => {
    for (const feature of collection.features) {
      const prov = feature.properties.provenance;
      expect(typeof prov.source).toBe('string');
      expect(['high', 'medium', 'low']).toContain(prov.confidence);
      expect(typeof prov.lastVerified).toBe('string');
    }
  });
});

describe('StructureDetail type validation', () => {
  it('has coordinates, administrativeLocation, and technicalSpecs', () => {
    const detail = mockStructureById('KZ-ZH-0001');
    expect(detail).not.toBeNull();
    expect(detail!.coordinates).toBeDefined();
    expect(detail!.administrativeLocation).toBeDefined();
    expect(detail!.technicalSpecs).toBeDefined();
  });

  it('administrativeLocation has region, district, and nearestSettlement', () => {
    const detail = mockStructureById('KZ-ZH-0001');
    const loc = detail!.administrativeLocation;
    expect(typeof loc.region).toBe('string');
    expect(typeof loc.district).toBe('string');
    expect(typeof loc.nearestSettlement).toBe('string');
  });

  it('technicalSpecs has optional fields when present', () => {
    const detail = mockStructureById('KZ-ZH-0001');
    const specs = detail!.technicalSpecs;
    if (specs.height !== undefined) expect(typeof specs.height).toBe('number');
    if (specs.length !== undefined) expect(typeof specs.length).toBe('number');
    if (specs.capacity !== undefined) expect(typeof specs.capacity).toBe('number');
    if (specs.yearBuilt !== undefined) expect(typeof specs.yearBuilt).toBe('number');
    if (specs.designType !== undefined) expect(typeof specs.designType).toBe('string');
    if (specs.materials !== undefined) expect(typeof specs.materials).toBe('string');
  });
});
