import { describe, it, expect } from 'vitest';
import { mockStructures, mockStructureById, mockDistricts, mockBasins } from '@/lib/api/mock-data';

describe('mockStructures', () => {
  it('returns a valid GeoJSON FeatureCollection', () => {
    const result = mockStructures();
    expect(result.type).toBe('FeatureCollection');
    expect(Array.isArray(result.features)).toBe(true);
  });

  it('returns a non-empty features array', () => {
    const result = mockStructures();
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('returns at least 50 structures', () => {
    const result = mockStructures();
    expect(result.features.length).toBeGreaterThanOrEqual(50);
  });

  it('each feature has properties.id', () => {
    const result = mockStructures();
    for (const feature of result.features) {
      expect(feature.properties.id).toBeDefined();
      expect(typeof feature.properties.id).toBe('string');
    }
  });

  it('features with non-null geometry have geometry.type Point', () => {
    const result = mockStructures();
    for (const feature of result.features) {
      if (feature.geometry !== null) {
        expect(feature.geometry.type).toBe('Point');
      }
    }
  });

  it('represents all 5 condition statuses', () => {
    const result = mockStructures();
    const conditions = new Set(result.features.map((f) => f.properties.condition));
    expect(conditions.has('normal')).toBe(true);
    expect(conditions.has('inspection')).toBe(true);
    expect(conditions.has('repair')).toBe(true);
    expect(conditions.has('critical')).toBe(true);
    expect(conditions.has('missing')).toBe(true);
  });

  it('includes structures with null geometry (missing coordinates)', () => {
    const result = mockStructures();
    const nullGeometryCount = result.features.filter((f) => f.geometry === null).length;
    expect(nullGeometryCount).toBeGreaterThanOrEqual(2);
  });

  it('filters by district correctly', () => {
    const districts = mockDistricts();
    const district = districts[0];
    const result = mockStructures({ district });
    for (const feature of result.features) {
      expect(feature.properties.district).toBe(district);
    }
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('filters by basin correctly', () => {
    const basins = mockBasins();
    const basin = basins[0];
    const result = mockStructures({ basin });
    for (const feature of result.features) {
      expect(feature.properties.basin).toBe(basin);
    }
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('filters by type correctly', () => {
    const result = mockStructures({ type: 'dam' });
    for (const feature of result.features) {
      expect(feature.properties.type).toBe('dam');
    }
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('filters by condition correctly', () => {
    const result = mockStructures({ condition: 'critical' });
    for (const feature of result.features) {
      expect(feature.properties.condition).toBe('critical');
    }
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('filters by inspectionStatus correctly', () => {
    const result = mockStructures({ inspectionStatus: 'overdue' });
    for (const feature of result.features) {
      expect(feature.properties.inspectionStatus).toBe('overdue');
    }
    expect(result.features.length).toBeGreaterThan(0);
  });

  it('combines all filters as intersection', () => {
    const districts = mockDistricts();
    const result = mockStructures({
      district: districts[0],
      condition: 'normal',
    });
    for (const feature of result.features) {
      expect(feature.properties.district).toBe(districts[0]);
      expect(feature.properties.condition).toBe('normal');
    }
  });

  it('returns empty features array when no structures match', () => {
    const result = mockStructures({ district: 'Несуществующий район' });
    expect(result.features.length).toBe(0);
  });
});

describe('mockStructureById', () => {
  it('returns the correct structure for a valid ID', () => {
    const structure = mockStructureById('KZ-ZH-0001');
    expect(structure).not.toBeNull();
    expect(structure!.id).toBe('KZ-ZH-0001');
  });

  it('returns null for a non-existent ID', () => {
    const structure = mockStructureById('nonexistent');
    expect(structure).toBeNull();
  });
});

describe('mockDistricts', () => {
  it('returns unique district names', () => {
    const districts = mockDistricts();
    expect(districts.length).toBe(new Set(districts).size);
    expect(districts.length).toBeGreaterThanOrEqual(4);
  });
});

describe('mockBasins', () => {
  it('returns unique basin names', () => {
    const basins = mockBasins();
    expect(basins.length).toBe(new Set(basins).size);
    expect(basins.length).toBeGreaterThanOrEqual(3);
  });
});
