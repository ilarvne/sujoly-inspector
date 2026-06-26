import type {
  ConditionStatus,
  InspectionStatus,
  InspectionRecord,
  DocumentMeta,
  RiskScore,
  RiskComponent,
  EngineerOverride,
  OverrideField,
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

const inspectorNames = [
  'А. Беков', 'К. Жусупов', 'М. Сулейменов', 'Б. Ахметов', 'Д. Касымов',
];

const findingsText = [
  'Состояние удовлетворительное. Требуется плановый осмотр через 6 месяцев.',
  'Обнаружены трещины на бетонной части. Рекомендуется ремонт.',
  'Водосбросное сооружение работает в штатном режиме.',
  'Уровень воды близок к критическому. Усиленный мониторинг.',
  'Грунтовая плотина имеет просадку на 2 см. Наблюдение продолжается.',
  'Оборудование насосной станции требует замены отдельных узлов.',
  'Канал очищен от наносов. Пропускная способность восстановлена.',
  'Выявлена фильтрация через тело плотины. Срочный ремонт.',
];

const documentTypes = ['passport_scan', 'inspection_report', 'photo', 'technical_drawing', 'certificate'];
const documentExtensions: Record<string, string> = {
  passport_scan: 'pdf',
  inspection_report: 'pdf',
  photo: 'jpg',
  technical_drawing: 'pdf',
  certificate: 'pdf',
};

export function mockInspections(structureId: string): InspectionRecord[] {
  const seed = parseInt(structureId.replace(/\D/g, ''), 10) || 1;
  const count = 3 + (seed % 6);
  const records: InspectionRecord[] = [];
  for (let i = 0; i < count; i++) {
    const year = 2024 - i;
    const month = ((seed + i) % 12) + 1;
    const day = ((seed + i * 3) % 28) + 1;
    records.push({
      id: `${structureId}-INS-${String(i + 1).padStart(3, '0')}`,
      structureId,
      date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      inspectorName: inspectorNames[(seed + i) % inspectorNames.length],
      findings: findingsText[(seed + i) % findingsText.length],
      photoUrls: i < 2 ? [`/mock-photos/${structureId}-${i + 1}.jpg`] : [],
      conditionAtInspection: conditions[(seed + i) % conditions.length] as ConditionStatus,
    });
  }
  return records.sort((a, b) => b.date.localeCompare(a.date));
}

export function mockDocuments(structureId: string): DocumentMeta[] {
  const seed = parseInt(structureId.replace(/\D/g, ''), 10) || 1;
  const count = seed % 4;
  const docs: DocumentMeta[] = [];
  for (let i = 0; i < count; i++) {
    const type = documentTypes[(seed + i) % documentTypes.length];
    docs.push({
      id: `${structureId}-DOC-${String(i + 1).padStart(3, '0')}`,
      structureId,
      filename: `${structureId}_${type}.${documentExtensions[type]}`,
      fileType: type,
      fileSize: 1024 * (100 + (seed + i) * 500),
      uploadedBy: inspectorNames[(seed + i) % inspectorNames.length],
      uploadedAt: `2024-${String(((seed + i) % 12) + 1).padStart(2, '0')}-15`,
      downloadUrl: `#mock-download/${structureId}/${type}/${i + 1}`,
    });
  }
  return docs;
}

export function mockAddDocument(structureId: string, meta: { filename: string; fileType: string; fileSize: number }): DocumentMeta {
  const id = `${structureId}-DOC-${Date.now()}`;
  return {
    id,
    structureId,
    filename: meta.filename,
    fileType: meta.fileType,
    fileSize: meta.fileSize,
    uploadedBy: 'Current User',
    uploadedAt: new Date().toISOString().split('T')[0],
    downloadUrl: `#mock-download/${structureId}/upload/${id}`,
  };
}

export function mockRiskScore(structureId: string): RiskScore {
  const seed = parseInt(structureId.replace(/\D/g, ''), 10) || 1;
  const components: RiskComponent[] = [
    {
      key: 'structural',
      label: 'Structural Integrity',
      score: 30 + (seed % 40),
      weight: 0.35,
      description: 'Condition of dam body, spillway, and load-bearing structures',
    },
    {
      key: 'hydrological',
      label: 'Hydrological Risk',
      score: 20 + (seed * 7 % 50),
      weight: 0.25,
      description: 'Flood probability, capacity utilization, basin characteristics',
    },
    {
      key: 'operational',
      label: 'Operational Status',
      score: 25 + (seed * 3 % 45),
      weight: 0.25,
      description: 'Equipment condition, maintenance frequency, operational readiness',
    },
    {
      key: 'age',
      label: 'Infrastructure Age',
      score: 35 + (seed * 11 % 50),
      weight: 0.15,
      description: 'Years since construction, design lifetime, obsolescence factors',
    },
  ];
  const overall = Math.round(components.reduce((sum, c) => sum + c.score * c.weight, 0));
  const riskLevel = overall >= 70 ? 'high' : overall >= 40 ? 'medium' : 'low';
  const explanations: Record<string, string> = {
    high: 'High risk score indicates urgent inspection and potential repair requirements.',
    medium: 'Moderate risk — scheduled inspection and monitoring recommended.',
    low: 'Low risk — routine inspection schedule applies.',
  };
  return {
    structureId,
    overall,
    components,
    explanation: explanations[riskLevel],
    computedAt: '2024-06-01',
  };
}

export function mockOverrides(structureId: string): EngineerOverride[] {
  const seed = parseInt(structureId.replace(/\D/g, ''), 10) || 1;
  const count = seed % 3;
  const overrides: EngineerOverride[] = [];
  const fields: OverrideField[] = ['inspection_interval', 'repair_status'];
  for (let i = 0; i < count; i++) {
    const field = fields[i % fields.length];
    overrides.push({
      id: `${structureId}-OVR-${String(i + 1).padStart(3, '0')}`,
      structureId,
      field,
      originalValue: field === 'inspection_interval' ? '12 months' : 'repair_required',
      newValue: field === 'inspection_interval' ? '6 months' : 'monitor',
      reason: field === 'inspection_interval'
        ? 'Increased risk due to age and recent findings of minor cracking.'
        : 'Visual inspection shows condition is stable. Monitoring recommended instead of immediate repair.',
      engineerName: inspectorNames[(seed + i) % inspectorNames.length],
      timestamp: `2024-${String(((seed + i) % 6) + 1).padStart(2, '0')}-10`,
    });
  }
  return overrides;
}

export function mockAddOverride(structureId: string, data: { field: OverrideField; originalValue: string; newValue: string; reason: string; engineerName: string }): EngineerOverride {
  return {
    id: `${structureId}-OVR-${Date.now()}`,
    structureId,
    ...data,
    timestamp: new Date().toISOString().split('T')[0],
  };
}
