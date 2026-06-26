import type { RiskScore, RiskComponent } from '@/lib/api/types';
import type { WeatherMode } from '@/lib/stores/weather-store';

const HEAVY_RAIN_BOOSTS: Record<RiskComponent['key'], number> = {
  structural: 1.1,
  hydrological: 1.4,
  operational: 1.15,
  age: 1.2,
};

const FLOOD_SEASON_BOOSTS: Record<RiskComponent['key'], number> = {
  structural: 1.2,
  hydrological: 1.6,
  operational: 1.25,
  age: 1.3,
};

const WEATHER_EXPLANATIONS: Record<Exclude<WeatherMode, 'normal'>, string> = {
  heavy_rain: '\u26A0 Heavy rain conditions amplify hydrological risk by 40%',
  flood_season: '\u26A0 Flood season conditions significantly amplify all risk components',
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function applyWeatherBoost(
  structureId: string,
  baseScore: RiskScore,
  mode: WeatherMode,
): RiskScore {
  if (mode === 'normal') {
    return baseScore;
  }

  const boosts = mode === 'heavy_rain' ? HEAVY_RAIN_BOOSTS : FLOOD_SEASON_BOOSTS;

  const boostedComponents: RiskComponent[] = baseScore.components.map((component) => ({
    ...component,
    score: clamp(Math.round(component.score * boosts[component.key]), 0, 100),
  }));

  const overall = clamp(
    Math.round(boostedComponents.reduce((sum, c) => sum + c.score * c.weight, 0)),
    0,
    100,
  );

  const weatherExplanation = WEATHER_EXPLANATIONS[mode];
  const explanation = `${weatherExplanation}. ${baseScore.explanation}`;

  return {
    ...baseScore,
    structureId,
    overall,
    components: boostedComponents,
    explanation,
  };
}
