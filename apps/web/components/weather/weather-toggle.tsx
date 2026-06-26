'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { useWeatherStore, type WeatherMode } from '@/lib/stores/weather-store';

const MODES: WeatherMode[] = ['normal', 'heavy_rain', 'flood_season'];

const MODE_LABEL_KEYS: Record<WeatherMode, 'normal' | 'heavyRain' | 'floodSeason'> = {
  normal: 'normal',
  heavy_rain: 'heavyRain',
  flood_season: 'floodSeason',
};

export function WeatherToggle() {
  const t = useTranslations('weather');
  const mode = useWeatherStore((s) => s.mode);
  const setMode = useWeatherStore((s) => s.setMode);

  return (
    <div data-testid="weather-toggle" className="flex flex-wrap items-center gap-2">
      <span className="text-sm font-semibold">{t('title')}</span>
      <div className="flex gap-1">
        {MODES.map((m) => (
          <Button
            key={m}
            variant={mode === m ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode(m)}
          >
            {t(MODE_LABEL_KEYS[m])}
          </Button>
        ))}
      </div>
    </div>
  );
}
