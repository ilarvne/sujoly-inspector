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
  SignificanceLevel,
  DuplicateCandidate,
  DiscoverySource,
  ConfidenceLevel,
  DiscoveryCandidate,
  MatchResult,
  MatchEvidence,
  ReviewStatus,
  ReviewAction,
  ReviewActionRecord,
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
    const age = new Date().getFullYear() - yearBuilt;
    const designEff = 75 + (i % 20);
    const actualEff = designEff - (5 + (i % 25));
    const significanceLevels: SignificanceLevel[] = ['critical', 'high', 'medium', 'low'];
    const significance = significanceLevels[i % 4];
    const wearPercentage = Math.min(100, Math.round(age * 1.2 + (i % 15)));

    const recommendationByCondition: Record<ConditionStatus, string> = {
      critical: 'Срочный ремонт и декоммиссия при невозможности восстановления',
      repair: 'Плановый ремонт в течение 3 месяцев',
      inspection: 'Усиленный мониторинг и внеочередной осмотр',
      normal: 'Регулярный осмотр по графику',
      missing: 'Запрос координат и идентификация объекта',
    };

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
      efficiency: { design: designEff, actual: actualEff },
      wearPercentage,
      significance,
      recommendation: recommendationByCondition[condition],
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
      efficiency: s.efficiency,
      wearPercentage: s.wearPercentage,
      significance: s.significance,
      recommendation: s.recommendation,
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
  const structure = mockStructuresRaw.find((s) => s.id === structureId);
  const yearBuilt = structure?.yearBuilt ?? 1980;
  const age = new Date().getFullYear() - yearBuilt;
  const condition = structure?.condition ?? 'normal';
  const inspectionStatus = structure?.inspectionStatus ?? 'current';
  const efficiency = structure?.efficiency;
  const significance = structure?.significance ?? 'medium';

  const conditionScores: Record<string, number> = { normal: 15, inspection: 35, repair: 65, critical: 90, missing: 50 };
  const significanceScores: Record<string, number> = { critical: 85, high: 60, medium: 40, low: 20 };
  const inspectionScores: Record<string, number> = { current: 10, due_soon: 30, overdue: 80, never: 70, unknown: 60 };
  const effDeviation = efficiency ? Math.abs(efficiency.design - efficiency.actual) : 15 + (seed % 20);

  const components: RiskComponent[] = [
    {
      key: 'condition',
      label: 'Technical Condition',
      score: conditionScores[condition] ?? 30,
      weight: 0.25,
      description: 'Structural integrity based on latest inspection findings',
    },
    {
      key: 'age',
      label: 'Infrastructure Age',
      score: Math.min(100, Math.round(age * 1.5)),
      weight: 0.20,
      description: `Age: ${age} years since construction`,
    },
    {
      key: 'efficiency',
      label: 'Efficiency Deviation',
      score: Math.min(100, Math.round(effDeviation * 3)),
      weight: 0.20,
      description: efficiency ? `Design КПД: ${efficiency.design}%, Actual: ${efficiency.actual}%` : 'No efficiency data available',
    },
    {
      key: 'significance',
      label: 'Object Significance',
      score: significanceScores[significance] ?? 40,
      weight: 0.15,
      description: `Significance level: ${significance}`,
    },
    {
      key: 'weather',
      label: 'Weather Risk',
      score: 20 + (seed * 13 % 40),
      weight: 0.10,
      description: 'Flood probability and weather exposure based on basin location',
    },
    {
      key: 'inspection_overdue',
      label: 'Inspection Overdue',
      score: inspectionScores[inspectionStatus] ?? 20,
      weight: 0.10,
      description: `Inspection status: ${inspectionStatus}`,
    },
  ];
  const overall = Math.round(components.reduce((sum, c) => sum + c.score * c.weight, 0));
  const riskLevel = overall >= 70 ? 'high' : overall >= 40 ? 'medium' : 'low';
  const explanations: Record<string, string> = {
    high: 'High risk score indicates urgent inspection and potential repair requirements.',
    medium: 'Moderate risk — scheduled inspection and monitoring recommended.',
    low: 'Low risk — routine inspection schedule applies.',
  };
  const recommendations: Record<string, string> = {
    high: 'Срочный ремонт и внеочередной осмотр',
    medium: 'Плановый ремонт и усиленный мониторинг',
    low: 'Регулярный осмотр по графику',
  };
  return {
    structureId,
    overall,
    components,
    explanation: explanations[riskLevel],
    recommendation: recommendations[riskLevel],
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

const discoverySources: DiscoverySource[] = ['osm', 'satellite', 'osm', 'satellite', 'kazvodhoz'];

const candidateNames: { ru: string; kk: string; en: string }[] = [
  { ru: 'Плотина №1 (OSM)', kk: 'Бөгет №1 (OSM)', en: 'Dam #1 (OSM)' },
  { ru: 'Водохранилище Тасуткель (спутник)', kk: 'Суқойма Тасөткел (жер серігі)', en: 'Tasutkel Reservoir (satellite)' },
  { ru: 'Канал Мерке-Талас (OSM)', kk: 'Канал Мерке-Талас (OSM)', en: 'Merke-Talas Canal (OSM)' },
  { ru: 'Насосная станция Акколь (спутник)', kk: 'Сорғы станциясы Ақкөл (жер серігі)', en: 'Akkol Pumping Station (satellite)' },
  { ru: 'Водосброс Каратау (OSM)', kk: 'Су ағызатын Қаратау (OSM)', en: 'Karatau Spillway (OSM)' },
  { ru: 'Плотина Кулан (спутник)', kk: 'Бөгет Құлан (жер серігі)', en: 'Kulan Dam (satellite)' },
  { ru: 'Водохранилище Асса (OSM)', kk: 'Суқойма Аса (OSM)', en: 'Assa Reservoir (OSM)' },
  { ru: 'Канал Шу-Мойынкум (спутник)', kk: 'Канал Шу-Мойынқұм (жер серігі)', en: 'Chu-Moynkum Canal (satellite)' },
  { ru: 'Плотина Кордай (OSM)', kk: 'Бөгет Қордай (OSM)', en: 'Korday Dam (OSM)' },
  { ru: 'Водосброс Сарыкемер (спутник)', kk: 'Су ағызатын Сарыкемер (жер серігі)', en: 'Sarykemer Spillway (satellite)' },
  { ru: 'Насосная станция Талас (OSM)', kk: 'Сорғы станциясы Талас (OSM)', en: 'Talas Pumping Station (OSM)' },
  { ru: 'Плотина Акколь-2 (спутник)', kk: 'Бөгет Ақкөл-2 (жер серігі)', en: 'Akkol Dam #2 (satellite)' },
  { ru: 'Канал Мерке-2 (OSM)', kk: 'Канал Мерке-2 (OSM)', en: 'Merke Canal #2 (OSM)' },
  { ru: 'Водохранилище Кулан (спутник)', kk: 'Суқойма Құлан (жер серігі)', en: 'Kulan Reservoir (satellite)' },
  { ru: 'Плотина Шу (OSM)', kk: 'Бөгет Шу (OSM)', en: 'Chu Dam (OSM)' },
  { ru: 'Водосброс Тасуткель-2 (спутник)', kk: 'Су ағызатын Тасөткел-2 (жер серігі)', en: 'Tasutkel Spillway #2 (satellite)' },
  { ru: 'Насосная станция Асса (OSM)', kk: 'Сорғы станциясы Аса (OSM)', en: 'Assa Pumping Station (OSM)' },
  { ru: 'Канал Каратау-Талас (спутник)', kk: 'Канал Қаратау-Талас (жер серігі)', en: 'Karatau-Talas Canal (satellite)' },
  { ru: 'Плотина Сарыкемер (OSM)', kk: 'Бөгет Сарыкемер (OSM)', en: 'Sarykemer Dam (OSM)' },
  { ru: 'Водохранилище Кордай-2 (спутник)', kk: 'Суқойма Қордай-2 (жер серігі)', en: 'Korday Reservoir #2 (satellite)' },
];

const sourceNames: Record<DiscoverySource, { ru: string; kk: string; en: string }> = {
  osm: { ru: 'OpenStreetMap', kk: 'OpenStreetMap', en: 'OpenStreetMap' },
  satellite: { ru: 'Спутниковые снимки', kk: 'Жер серігі суреттері', en: 'Satellite Imagery' },
  kazvodhoz: { ru: 'Реестр Казводхоза', kk: 'Қазсуден шаруашылығы', en: 'Kazvodhoz Registry' },
  manual: { ru: 'Ручной ввод', kk: 'Қолмен енгізу', en: 'Manual Entry' },
};

function generateMockCandidates(): DiscoveryCandidate[] {
  const candidates: DiscoveryCandidate[] = [];

  for (let i = 0; i < 20; i++) {
    const source = discoverySources[i % discoverySources.length];
    const settlementIdx = i % settlements.length;
    const settlement = settlements[settlementIdx];
    const typeIdx = i % types.length;
    const type = types[typeIdx];
    const confidence = (i % 3 === 0 ? 'high' : i % 3 === 1 ? 'medium' : 'low') as ConfidenceLevel;

    const coords = settlement.coords;
    const jitter = 0.02;
    const coordinates = {
      lon: coords[0] + (Math.sin(i * 3.7) * jitter),
      lat: coords[1] + (Math.cos(i * 5.3) * jitter),
    };

    candidates.push({
      id: `CAND-${String(i + 1).padStart(3, '0')}`,
      source,
      sourceName: sourceNames[source],
      name: candidateNames[i],
      type,
      coordinates,
      district: districts[settlement.dIdx],
      basin: basins[settlement.bIdx],
      confidence,
      detectedAt: `2025-${String((i % 6) + 1).padStart(2, '0')}-${String((i * 3 % 28) + 1).padStart(2, '0')}`,
      properties: {
        height: type === 'dam' || type === 'reservoir' ? 8 + (i % 25) : undefined,
        length: type === 'dam' || type === 'canal' ? 50 + (i % 3000) : undefined,
        capacity: type === 'reservoir' ? 2 + (i % 150) : undefined,
        yearBuilt: 1965 + (i % 45),
        osmId: source === 'osm' ? `way/${1000000 + i * 137}` : undefined,
        osmTags: source === 'osm' ? { waterway: type === 'dam' ? 'dam' : type === 'canal' ? 'canal' : 'reservoir', name: candidateNames[i].en } : undefined,
        satelliteTile: source === 'satellite' ? `tile/${i + 100}/${i % 8}/${i % 6}` : undefined,
      },
    });
  }

  return candidates;
}

const mockCandidatesRaw: DiscoveryCandidate[] = generateMockCandidates();

export function mockDiscoveryCandidates(): DiscoveryCandidate[] {
  return mockCandidatesRaw;
}

export function mockDiscoveryCandidateById(id: string): DiscoveryCandidate | null {
  return mockCandidatesRaw.find((c) => c.id === id) ?? null;
}

const reviewStatuses: ReviewStatus[] = ['pending', 'pending', 'pending', 'pending', 'accepted', 'pending', 'rejected', 'pending', 'linked', 'pending', 'pending', 'pending', 'pending', 'pending', 'rejected', 'pending', 'accepted', 'pending', 'pending', 'linked'];

function generateMatchResults(): MatchResult[] {
  return mockCandidatesRaw.map((cand, i) => {
    const matchScore = cand.confidence === 'high' ? 70 + (i % 25) : cand.confidence === 'medium' ? 40 + (i % 30) : 15 + (i % 25);
    const hasExisting = matchScore >= 45 && i % 3 !== 2;
    const existingId = hasExisting ? `KZ-ZH-${String((i % 55) + 1).padStart(4, '0')}` : null;

    const evidence: MatchEvidence[] = [];

    if (existingId) {
      const existing = mockStructuresRaw.find((s) => s.id === existingId);
      if (existing) {
        const nameSim = Math.min(95, 50 + (matchScore % 40));
        evidence.push({
          type: 'name_similarity',
          label: 'Name Similarity',
          value: `${nameSim}%`,
          score: nameSim,
          agreement: nameSim >= 60,
        });

        const distKm = Math.abs(matchScore - 80) * 0.5;
        evidence.push({
          type: 'distance',
          label: 'Distance',
          value: `${distKm.toFixed(1)} km`,
          score: Math.max(0, 100 - distKm * 10),
          agreement: distKm < 5,
        });

        const typeMatch = existing.type === cand.type;
        evidence.push({
          type: 'type_agreement',
          label: 'Type Agreement',
          value: typeMatch ? 'Match' : 'Mismatch',
          score: typeMatch ? 100 : 0,
          agreement: typeMatch,
        });

        if (existing.provenance.source === cand.source || (existing.provenance.source === 'kazvodhoz' && cand.source === 'osm')) {
          evidence.push({
            type: 'source_overlap',
            label: 'Source Overlap',
            value: 'Confirmed',
            score: 85,
            agreement: true,
          });
        }
      }
    }

    return {
      candidateId: cand.id,
      existingStructureId: existingId,
      matchScore,
      evidence,
      reviewStatus: reviewStatuses[i % reviewStatuses.length] as ReviewStatus,
    };
  });
}

const mockMatchResultsRaw: MatchResult[] = generateMatchResults();

export function mockMatchResults(): MatchResult[] {
  return mockMatchResultsRaw;
}

export function mockMatchResultByCandidateId(candidateId: string): MatchResult | null {
  return mockMatchResultsRaw.find((m) => m.candidateId === candidateId) ?? null;
}

export function mockSubmitReview(candidateId: string, action: ReviewAction, reviewerName: string, reason: string): ReviewActionRecord {
  return {
    id: `REV-${candidateId}-${Date.now()}`,
    candidateId,
    action,
    reviewerName,
    reason,
    timestamp: new Date().toISOString(),
  };
}

export function detectDuplicateStructures(): DuplicateCandidate[] {
  const groups: Record<string, number[]> = {};
  for (let i = 0; i < mockStructuresRaw.length; i++) {
    const s = mockStructuresRaw[i];
    const key = `${s.district}|${s.basin}|${s.type}|${s.yearBuilt ?? 0}|${Math.round((s.length ?? 0) / 100)}`;
    if (!groups[key]) groups[key] = [];
    groups[key].push(i);
  }
  const duplicates: DuplicateCandidate[] = [];
  for (const [key, indices] of Object.entries(groups)) {
    if (indices.length < 2) continue;
    const structures = indices.map((i) => mockStructuresRaw[i]);
    const [d, b, t, y, l] = key.split('|');
    duplicates.push({
      id: `DUP-${duplicates.length + 1}`,
      structureIds: structures.map((s) => s.id),
      reason: `Same district "${d}", basin "${b}", type "${t}", year ${y}, similar length bucket ${l}`,
      matchFields: ['district', 'basin', 'type', 'yearBuilt', 'length'],
    });
  }
  return duplicates;
}
