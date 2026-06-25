import type {
  ConditionStatus,
  InspectionStatus,
  StructureCollection,
  StructureDetail,
  StructureFilters,
  StructureFeature,
  StructureType,
} from './types';

const districts = [
  'Жамбылский район',
  'Меркенский район',
  'Мойынкумский район',
  'Таласский район',
];

const basins = ['р. Талас', 'р. Чу', 'р. Аса'];

const region = 'Жамбылская область';

const settlements = [
  { name: { ru: 'Тасуткель', kk: 'Тасөткел', en: 'Tasutkel' }, coords: [71.35, 42.95] as [number, number], dIdx: 0, bIdx: 0 },
  { name: { ru: 'Мерке', kk: 'Мерке', en: 'Merke' }, coords: [73.25, 42.75] as [number, number], dIdx: 1, bIdx: 0 },
  { name: { ru: 'Мойынкум', kk: 'Мойынқұм', en: 'Moynkum' }, coords: [73.50, 43.70] as [number, number], dIdx: 2, bIdx: 1 },
  { name: { ru: 'Каратау', kk: 'Қаратау', en: 'Karatau' }, coords: [71.20, 43.80] as [number, number], dIdx: 3, bIdx: 0 },
  { name: { ru: 'Акколь', kk: 'Ақкөл', en: 'Akkol' }, coords: [72.10, 43.50] as [number, number], dIdx: 0, bIdx: 2 },
  { name: { ru: 'Асса', kk: 'Аса', en: 'Assa' }, coords: [72.40, 43.20] as [number, number], dIdx: 1, bIdx: 2 },
  { name: { ru: 'Шу', kk: 'Шу', en: 'Chu' }, coords: [73.60, 43.60] as [number, number], dIdx: 2, bIdx: 1 },
  { name: { ru: 'Талас', kk: 'Талас', en: 'Talas' }, coords: [71.80, 43.20] as [number, number], dIdx: 3, bIdx: 0 },
  { name: { ru: 'Кулан', kk: 'Құлан', en: 'Kulan' }, coords: [72.80, 43.10] as [number, number], dIdx: 1, bIdx: 0 },
  { name: { ru: 'Кордай', kk: 'Қордай', en: 'Korday' }, coords: [74.60, 43.00] as [number, number], dIdx: 0, bIdx: 2 },
  { name: { ru: 'Сарыкемер', kk: 'Сарыкемер', en: 'Sarykemer' }, coords: [71.50, 43.30] as [number, number], dIdx: 3, bIdx: 0 },
];

const conditions: ConditionStatus[] = ['normal', 'inspection', 'repair', 'critical', 'missing'];
const inspectionStatuses: InspectionStatus[] = ['current', 'overdue', 'due_soon', 'never', 'unknown'];
const types: StructureType[] = ['dam', 'reservoir', 'canal', 'pumping_station', 'spillway', 'other'];

const typeNames: Record<StructureType, { ru: string; kk: string; en: string }> = {
  dam: { ru: 'Плотина', kk: 'Бөгет', en: 'Dam' },
  reservoir: { ru: 'Водохранилище', kk: 'Суқойма', en: 'Reservoir' },
  canal: { ru: 'Канал', kk: 'Канал', en: 'Canal' },
  pumping_station: { ru: 'Насосная станция', kk: 'Сорғы станциясы', en: 'Pumping Station' },
  spillway: { ru: 'Водосброс', kk: 'Су ағызатын құрылғы', en: 'Spillway' },
  other: { ru: 'Сооружение', kk: 'Құрылым', en: 'Structure' },
};

const designTypes = ['земляная плотина', 'бетонная плотина', 'каменно-набросная плотина', 'железобетонная конструкция'];
const materialsList = ['грунт', 'бетон', 'железобетон', 'камень', 'грунт и бетон'];
const sources = ['kazvodhoz', 'osm', 'satellite', 'manual'];

function generateMockStructures(): StructureDetail[] {
  const structures: StructureDetail[] = [];

  for (let i = 0; i < 55; i++) {
    const conditionIdx = Math.floor(i / 11);
    const condition = conditions[conditionIdx];
    const typeIdx = i % types.length;
    const type = types[typeIdx];
    const settlementIdx = i % settlements.length;
    const settlement = settlements[settlementIdx];
    const inspectionIdx = i % inspectionStatuses.length;
    const inspectionStatus = inspectionStatuses[inspectionIdx];

    const id = `KZ-ZH-${String(i + 1).padStart(4, '0')}`;
    const district = districts[settlement.dIdx];
    const basin = basins[settlement.bIdx];

    const missingOffset = i - 44;
    const coordinates =
      condition === 'missing' && missingOffset < 2
        ? null
        : condition === 'missing' && missingOffset < 4
          ? { lon: 0, lat: 0 }
          : { lon: settlement.coords[0], lat: settlement.coords[1] };

    const height = type === 'dam' || type === 'reservoir' ? 10 + (i % 30) : undefined;
    const length = type === 'dam' || type === 'canal' ? 100 + (i % 5000) : undefined;
    const capacity = type === 'reservoir' ? 5 + (i % 200) : undefined;
    const yearBuilt = 1960 + (i % 50);

    structures.push({
      id,
      name: {
        ru: `${typeNames[type].ru} ${settlement.name.ru}`,
        kk: `${typeNames[type].kk} ${settlement.name.kk}`,
        en: `${typeNames[type].en} ${settlement.name.en}`,
      },
      type,
      condition,
      inspectionStatus,
      district,
      basin,
      height,
      length,
      capacity,
      yearBuilt,
      coordinates,
      administrativeLocation: {
        region,
        district,
        nearestSettlement: settlement.name.ru,
      },
      technicalSpecs: {
        height,
        length,
        capacity,
        yearBuilt,
        designType: designTypes[i % designTypes.length],
        materials: materialsList[i % materialsList.length],
      },
      provenance: {
        source: sources[i % sources.length],
        confidence: (i % 3 === 0 ? 'high' : i % 3 === 1 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
        lastVerified: `2024-${String((i % 12) + 1).padStart(2, '0')}-15`,
      },
    });
  }

  return structures;
}

const mockStructuresRaw: StructureDetail[] = generateMockStructures();

export function mockStructures(filters?: StructureFilters): StructureCollection {
  const filtered = mockStructuresRaw.filter((s) => {
    if (filters?.district && s.district !== filters.district) return false;
    if (filters?.basin && s.basin !== filters.basin) return false;
    if (filters?.type && s.type !== filters.type) return false;
    if (filters?.condition && s.condition !== filters.condition) return false;
    if (filters?.inspectionStatus && s.inspectionStatus !== filters.inspectionStatus) return false;
    return true;
  });

  const features: StructureFeature[] = filtered.map((s) => ({
    type: 'Feature' as const,
    geometry: s.coordinates
      ? { type: 'Point' as const, coordinates: [s.coordinates.lon, s.coordinates.lat] }
      : null,
    properties: {
      id: s.id,
      name: s.name,
      type: s.type,
      condition: s.condition,
      inspectionStatus: s.inspectionStatus,
      district: s.district,
      basin: s.basin,
      height: s.height,
      length: s.length,
      capacity: s.capacity,
      yearBuilt: s.yearBuilt,
      provenance: s.provenance,
    },
  }));

  return {
    type: 'FeatureCollection' as const,
    features,
  };
}

export function mockStructureById(id: string): StructureDetail | null {
  return mockStructuresRaw.find((s) => s.id === id) ?? null;
}

export function mockDistricts(): string[] {
  return [...new Set(mockStructuresRaw.map((s) => s.district))];
}

export function mockBasins(): string[] {
  return [...new Set(mockStructuresRaw.map((s) => s.basin))];
}
