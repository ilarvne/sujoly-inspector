import { mockStructures, mockStructureById, mockRiskScore, mockInspections } from '@/lib/api/mock-data';
import type {
  ChatIntent,
  CopilotSource,
  CopilotCard,
  StructureDetail,
  TrilingualText,
} from '@/lib/api/types';

type Locale = 'ru' | 'kk' | 'en';

const intentKeywords: Record<ChatIntent, string[]> = {
  explain_condition: ['почему', 'неге', 'why', 'почем'],
  summarize_inspections: ['сводк', 'summarize', 'summari', 'histor', 'истор', 'тарих', 'барлық', 'все осмотр', 'all inspection'],
  list_critical: ['критическ', 'critical', 'критикалық', 'критикал'],
  list_repair: ['ремонт', 'repair', 'жөндеу', 'жөнде'],
  list_inspection: ['инспекц', 'осмотр', 'тексер', 'inspection', 'inspect'],
  show_risk: ['риск', 'тәуекел', 'risk'],
  list_by_district: ['район', 'аудан', 'district'],
  list_by_basin: ['бассейн', 'алқап', 'basin'],
  general: [],
};

export function detectIntent(query: string): ChatIntent {
  const q = query.toLowerCase();
  const intentOrder: ChatIntent[] = [
    'explain_condition',
    'summarize_inspections',
    'list_critical',
    'list_repair',
    'list_inspection',
    'show_risk',
    'list_by_district',
    'list_by_basin',
  ];
  for (const intent of intentOrder) {
    const keywords = intentKeywords[intent];
    if (keywords.some((kw) => q.includes(kw))) {
      return intent;
    }
  }
  return 'general';
}

function nameInLocale(name: TrilingualText, locale: Locale): string {
  return name[locale] || name.ru;
}

function makeSource(
  type: CopilotSource['type'],
  label: string,
  reference: string,
  structureId?: string,
): CopilotSource {
  return {
    id: `src-${type}-${reference}-${Math.random().toString(36).slice(2, 8)}`,
    type,
    label,
    reference,
    structureId,
  };
}

function makeStructureCard(s: StructureDetail, locale: Locale): CopilotCard {
  return {
    type: 'structure',
    data: s,
  };
}

function makeRiskCard(structureId: string, structureName: string): CopilotCard {
  return {
    type: 'risk',
    data: mockRiskScore(structureId),
    structureId,
    structureName,
  };
}

function makeInspectionCard(structureId: string, structureName: string): CopilotCard[] {
  const inspections = mockInspections(structureId).slice(0, 2);
  return inspections.map((insp) => ({
    type: 'inspection' as const,
    data: insp,
    structureName,
  }));
}

const responseTemplates: Record<ChatIntent, (locale: Locale, structures: StructureDetail[]) => {
  text: string;
  sources: CopilotSource[];
  cards: CopilotCard[];
}> = {
  list_critical: (locale, structures) => {
    const critical = structures.filter((s) => s.condition === 'critical');
    const msgs = {
      ru: `Найдено ${critical.length} сооружений в критическом состоянии. Эти объекты требуют немедленного внимания.`,
      kk: `${critical.length} критикалық жағдайдағы құрылым табылды. Бұл нысандар дереу назар аударуды қажет етеді.`,
      en: `Found ${critical.length} structures in critical condition. These require immediate attention.`,
    };
    const cards = critical.slice(0, 4).map((s) => makeStructureCard(s, locale));
    const sources = critical.slice(0, 3).map((s) =>
      makeSource('registry', `Kazvodhoz Registry: ${s.id}`, s.id, s.id),
    );
    return { text: msgs[locale], sources, cards };
  },

  list_repair: (locale, structures) => {
    const repair = structures.filter((s) => s.condition === 'repair');
    const msgs = {
      ru: `Найдено ${repair.length} сооружений, требующих ремонта.`,
      kk: `${repair.length} жөндеуді қажет ететін құрылым табылды.`,
      en: `Found ${repair.length} structures requiring repair.`,
    };
    const cards = repair.slice(0, 4).map((s) => makeStructureCard(s, locale));
    const sources = repair.slice(0, 3).map((s) =>
      makeSource('inspection', `Inspection Report: ${s.id}`, s.id, s.id),
    );
    return { text: msgs[locale], sources, cards };
  },

  list_inspection: (locale, structures) => {
    const needInspection = structures.filter((s) => s.condition === 'inspection');
    const msgs = {
      ru: `${needInspection.length} сооружений требуют плановой инспекции.`,
      kk: `${needInspection.length} құрылым жоспарлы тексеруді қажет етеді.`,
      en: `${needInspection.length} structures require scheduled inspection.`,
    };
    const cards = needInspection.slice(0, 4).map((s) => makeStructureCard(s, locale));
    const sources = needInspection.slice(0, 3).map((s) =>
      makeSource('registry', `Registry: ${s.id}`, s.id, s.id),
    );
    return { text: msgs[locale], sources, cards };
  },

  show_risk: (locale, structures) => {
    const sorted = [...structures].sort((a, b) => {
      const ra = mockRiskScore(a.id);
      const rb = mockRiskScore(b.id);
      return rb.overall - ra.overall;
    });
    const top = sorted.slice(0, 3);
    const msgs = {
      ru: `Топ-3 сооружения с наивысшим риском:\n${top.map((s, i) => `${i + 1}. ${nameInLocale(s.name, 'ru')} (ID: ${s.id}) — балл риска: ${mockRiskScore(s.id).overall}`).join('\n')}`,
      kk: `Ең жоғары тәуекелді 3 құрылым:\n${top.map((s, i) => `${i + 1}. ${nameInLocale(s.name, 'kk')} (ID: ${s.id}) — тәуекел баллы: ${mockRiskScore(s.id).overall}`).join('\n')}`,
      en: `Top 3 structures with highest risk:\n${top.map((s, i) => `${i + 1}. ${nameInLocale(s.name, 'en')} (ID: ${s.id}) — risk score: ${mockRiskScore(s.id).overall}`).join('\n')}`,
    };
    const cards = top.map((s) => makeRiskCard(s.id, nameInLocale(s.name, locale)));
    const sources = top.map((s) =>
      makeSource('risk_assessment', `Risk Assessment: ${s.id}`, s.id, s.id),
    );
    return { text: msgs[locale], sources, cards };
  },

  summarize_inspections: (locale, structures) => {
    const target = structures[0];
    if (!target) {
      return { text: locale === 'ru' ? 'Нет данных об осмотрах.' : locale === 'kk' ? 'Тексеру деректері жоқ.' : 'No inspection data available.', sources: [], cards: [] };
    }
    const inspections = mockInspections(target.id);
    const msgs = {
      ru: `Сооружение "${nameInLocale(target.name, 'ru')}" (ID: ${target.id}) имеет ${inspections.length} зарегистрированных осмотров. Последний осмотр: ${inspections[0]?.date}. Основные выводы: ${inspections[0]?.findings}`,
      kk: `"${nameInLocale(target.name, 'kk')}" құрылымы (ID: ${target.id}) бойынша ${inspections.length} қарап шығу тіркелген. Соңғы қарап шығу: ${inspections[0]?.date}. Негізгі қорытынды: ${inspections[0]?.findings}`,
      en: `Structure "${nameInLocale(target.name, 'en')}" (ID: ${target.id}) has ${inspections.length} recorded inspections. Last inspection: ${inspections[0]?.date}. Key findings: ${inspections[0]?.findings}`,
    };
    const cards = makeInspectionCard(target.id, nameInLocale(target.name, locale));
    const sources = inspections.slice(0, 3).map((insp) =>
      makeSource('inspection', `Inspection: ${insp.id}`, insp.id, target.id),
    );
    return { text: msgs[locale], sources, cards };
  },

  explain_condition: (locale, structures) => {
    const target = structures.find((s) => s.condition !== 'normal') || structures[0];
    if (!target) {
      return { text: '', sources: [], cards: [] };
    }
    const risk = mockRiskScore(target.id);
    const conditionMsgs: Record<string, Record<Locale, string>> = {
      critical: {
        ru: `Сооружение "${nameInLocale(target.name, 'ru')}" имеет критическое состояние. Общий балл риска: ${risk.overall}/100. Основные факторы: ${risk.components.filter((c) => c.score > 50).map((c) => c.label).join(', ')}.`,
        kk: `"${nameInLocale(target.name, 'kk')}" құрылымы критикалық жағдайда. Жалпы тәуекел баллы: ${risk.overall}/100. Негізгі факторлар: ${risk.components.filter((c) => c.score > 50).map((c) => c.label).join(', ')}.`,
        en: `Structure "${nameInLocale(target.name, 'en')}" is in critical condition. Overall risk score: ${risk.overall}/100. Key factors: ${risk.components.filter((c) => c.score > 50).map((c) => c.label).join(', ')}.`,
      },
      repair: {
        ru: `Сооружение "${nameInLocale(target.name, 'ru')}" требует ремонта. Балл риска: ${risk.overall}/100. Рекомендуется плановый ремонт на основе результатов последних осмотров.`,
        kk: `"${nameInLocale(target.name, 'kk')}" құрылымы жөндеуді қажет етеді. Тәуекел баллы: ${risk.overall}/100. Соңғы тексерулер нәтижелері бойынша жоспарлы жөндеу ұсынылады.`,
        en: `Structure "${nameInLocale(target.name, 'en')}" requires repair. Risk score: ${risk.overall}/100. Scheduled repair recommended based on recent inspection findings.`,
      },
      inspection: {
        ru: `Сооружение "${nameInLocale(target.name, 'ru')}" требует инспекции. Балл риска: ${risk.overall}/100. Необходимо провести плановый осмотр для подтверждения состояния.`,
        kk: `"${nameInLocale(target.name, 'kk')}" құрылымы тексеруді қажет етеді. Тәуекел баллы: ${risk.overall}/100. Жағдайды растау үшін жоспарлы қарап шығу қажет.`,
        en: `Structure "${nameInLocale(target.name, 'en')}" requires inspection. Risk score: ${risk.overall}/100. A scheduled inspection is needed to confirm condition.`,
      },
      normal: {
        ru: `Сооружение "${nameInLocale(target.name, 'ru')}" в нормальном состоянии. Балл риска: ${risk.overall}/100. Регулярный мониторинг достаточен.`,
        kk: `"${nameInLocale(target.name, 'kk')}" құрылымы қалыпты жағдайда. Тәуекел баллы: ${risk.overall}/100. Тұрақты бақылау жеткілікті.`,
        en: `Structure "${nameInLocale(target.name, 'en')}" is in normal condition. Risk score: ${risk.overall}/100. Regular monitoring is sufficient.`,
      },
      missing: {
        ru: `Координаты сооружения "${nameInLocale(target.name, 'ru')}" отсутствуют. Требуется уточнение геопозиции.`,
        kk: `"${nameInLocale(target.name, 'kk')}" құрылымының координаталары жоқ. Геоорналасуды нақтылау қажет.`,
        en: `Structure "${nameInLocale(target.name, 'en')}" has missing coordinates. Geolocation needs to be verified.`,
      },
    };
    const text = conditionMsgs[target.condition]?.[locale] || conditionMsgs.normal[locale];
    const cards = [makeRiskCard(target.id, nameInLocale(target.name, locale))];
    const sources = [
      makeSource('risk_assessment', `Risk Assessment: ${target.id}`, target.id, target.id),
      makeSource('inspection', `Latest Inspection: ${target.id}`, target.id, target.id),
    ];
    return { text, sources, cards };
  },

  list_by_district: (locale, structures) => {
    const districts = [...new Set(structures.map((s) => s.district))];
    const districtSummaries = districts.map((d) => {
      const count = structures.filter((s) => s.district === d).length;
      return `${d}: ${count}`;
    });
    const msgs = {
      ru: `Сооружения по районам:\n${districtSummaries.join('\n')}`,
      kk: `Аудандар бойынша құрылымдар:\n${districtSummaries.join('\n')}`,
      en: `Structures by district:\n${districtSummaries.join('\n')}`,
    };
    const firstPerDistrict = districts.map((d) => structures.find((s) => s.district === d)!).filter(Boolean);
    const cards = firstPerDistrict.slice(0, 4).map((s) => makeStructureCard(s, locale));
    const sources = districts.slice(0, 3).map((d) => makeSource('registry', `Registry: ${d}`, d));
    return { text: msgs[locale], sources, cards };
  },

  list_by_basin: (locale, structures) => {
    const basins = [...new Set(structures.map((s) => s.basin))];
    const basinSummaries = basins.map((b) => {
      const count = structures.filter((s) => s.basin === b).length;
      return `${b}: ${count}`;
    });
    const msgs = {
      ru: `Сооружения по бассейнам:\n${basinSummaries.join('\n')}`,
      kk: `Алқаптар бойынша құрылымдар:\n${basinSummaries.join('\n')}`,
      en: `Structures by basin:\n${basinSummaries.join('\n')}`,
    };
    const firstPerBasin = basins.map((b) => structures.find((s) => s.basin === b)!).filter(Boolean);
    const cards = firstPerBasin.slice(0, 4).map((s) => makeStructureCard(s, locale));
    const sources = basins.slice(0, 3).map((b) => makeSource('registry', `Registry: ${b}`, b));
    return { text: msgs[locale], sources, cards };
  },

  general: (locale, structures) => {
    const total = structures.length;
    const byCondition = {
      normal: structures.filter((s) => s.condition === 'normal').length,
      inspection: structures.filter((s) => s.condition === 'inspection').length,
      repair: structures.filter((s) => s.condition === 'repair').length,
      critical: structures.filter((s) => s.condition === 'critical').length,
    };
    const msgs = {
      ru: `В каталоге Жамбылской области зарегистрировано ${total} гидротехнических сооружений. Распределение по состоянию: нормальное — ${byCondition.normal}, требуется инспекция — ${byCondition.inspection}, требуется ремонт — ${byCondition.repair}, критическое — ${byCondition.critical}. Задайте вопрос о конкретном сооружении, районе или типе сооружения для получения детальной информации.`,
      kk: `Жамбыл облысының каталогында ${total} гидротехникалық құрылым тіркелген. Жағдай бойынша таралуы: қалыпты — ${byCondition.normal}, тексеру қажет — ${byCondition.inspection}, жөндеу қажет — ${byCondition.repair}, критикалық — ${byCondition.critical}. Толық ақпарат алу үшін нақты құрылым, аудан немесе құрылым түрі туралы сұрақ қойыңыз.`,
      en: `The Zhambyl Oblast catalog contains ${total} hydraulic structures. Condition distribution: normal — ${byCondition.normal}, inspection required — ${byCondition.inspection}, repair required — ${byCondition.repair}, critical — ${byCondition.critical}. Ask about a specific structure, district, or structure type for detailed information.`,
    };
    const cards: CopilotCard[] = [
      {
        type: 'report',
        data: {
          title: locale === 'ru' ? 'Сводка по портфелю' : locale === 'kk' ? 'Портфель қорытындысы' : 'Portfolio Summary',
          summary: msgs[locale],
          structureCount: total,
          structures: structures.slice(0, 5),
        },
      },
    ];
    const sources = [
      makeSource('registry', 'Kazvodhoz Registry', 'KZ-ZH-0001'),
      makeSource('osm', 'OpenStreetMap', 'OSM-ZH'),
    ];
    return { text: msgs[locale], sources, cards };
  },
};

export function mockAIEngine(
  query: string,
  locale: Locale,
): { text: string; sources: CopilotSource[]; cards: CopilotCard[] } {
  const intent = detectIntent(query);
  const collection = mockStructures();
  const allStructures: StructureDetail[] = collection.features.map((f) =>
    mockStructureById(f.properties.id),
  ).filter((s): s is StructureDetail => s !== null);

  const districtMatch = allStructures.find((s) =>
    query.toLowerCase().includes(s.district.toLowerCase()),
  );
  const basinMatch = allStructures.find((s) =>
    query.toLowerCase().includes(s.basin.toLowerCase()),
  );

  let filtered = allStructures;
  if (districtMatch && (intent === 'list_by_district' || intent === 'general')) {
    filtered = allStructures.filter((s) => s.district === districtMatch.district);
  } else if (basinMatch && (intent === 'list_by_basin' || intent === 'general')) {
    filtered = allStructures.filter((s) => s.basin === basinMatch.basin);
  }

  const nameMatch = allStructures.find((s) => {
    const q = query.toLowerCase();
    return (
      q.includes(s.name.ru.toLowerCase()) ||
      q.includes(s.name.kk.toLowerCase()) ||
      q.includes(s.name.en.toLowerCase()) ||
      q.includes(s.id.toLowerCase())
    );
  });

  if (nameMatch && (intent === 'show_risk' || intent === 'summarize_inspections' || intent === 'explain_condition')) {
    filtered = [nameMatch];
  }

  const handler = responseTemplates[intent];
  return handler(locale, filtered.length > 0 ? filtered : allStructures);
}

export function getSuggestedPrompts(locale: Locale): string[] {
  const prompts: Record<Locale, string[]> = {
    ru: [
      'Какие сооружения в критическом состоянии?',
      'Покажи сооружения, требующие ремонта',
      'Какие сооружения нуждаются в инспекции?',
      'Покажи топ-3 сооружения по уровню риска',
      'Сооружения по районам',
    ],
    kk: [
      'Қандай құрылымдар критикалық жағдайда?',
      'Жөндеуді қажет ететін құрылымдарды көрсет',
      'Қандай құрылымдар тексеруді қажет етеді?',
      'Тәуекел деңгейі бойынша топ-3 құрылымды көрсет',
      'Аудандар бойынша құрылымдар',
    ],
    en: [
      'Which structures are in critical condition?',
      'Show structures requiring repair',
      'Which structures need inspection?',
      'Show top 3 structures by risk level',
      'Structures by district',
    ],
  };
  return prompts[locale];
}
