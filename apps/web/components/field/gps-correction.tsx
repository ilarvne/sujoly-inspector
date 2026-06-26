'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { MapPinIcon, Loader2Icon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export interface GpsCoordinates {
  lat: number;
  lon: number;
}

export function GpsCorrection({
  coordinates,
  onChange,
}: {
  coordinates: GpsCoordinates | null;
  onChange: (coords: GpsCoordinates | null) => void;
}) {
  const t = useTranslations('field');
  const [isFetching, setIsFetching] = useState(false);
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');

  const handleFetchGps = () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) return;

    setIsFetching(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        onChange({ lat: latitude, lon: longitude });
        setManualLat(String(latitude.toFixed(6)));
        setManualLon(String(longitude.toFixed(6)));
        setIsFetching(false);
      },
      () => {
        setIsFetching(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleManualOverride = () => {
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);
    if (!isNaN(lat) && !isNaN(lon)) {
      onChange({ lat, lon });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleFetchGps}
          disabled={isFetching}
          data-testid="fetch-gps-btn"
        >
          {isFetching ? (
            <Loader2Icon className="size-4 mr-2 animate-spin" />
          ) : (
            <MapPinIcon className="size-4 mr-2" />
          )}
          {isFetching ? t('fetchingGps') : t('fetchGps')}
        </Button>
      </div>

      {coordinates && (
        <div className="rounded-md bg-muted p-3 text-sm" data-testid="gps-display">
          <div className="flex justify-between">
            <span className="text-muted-foreground">{t('latitude')}:</span>
            <span className="font-mono">{coordinates.lat.toFixed(6)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">{t('longitude')}:</span>
            <span className="font-mono">{coordinates.lon.toFixed(6)}</span>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <Label className="text-sm font-medium">{t('manualOverride')}</Label>
        <div className="flex gap-2">
          <Input
            type="number"
            step="0.000001"
            placeholder={t('latitude')}
            value={manualLat}
            onChange={(e) => setManualLat(e.target.value)}
            className="flex-1"
            data-testid="manual-lat"
          />
          <Input
            type="number"
            step="0.000001"
            placeholder={t('longitude')}
            value={manualLon}
            onChange={(e) => setManualLon(e.target.value)}
            className="flex-1"
            data-testid="manual-lon"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleManualOverride}
            data-testid="apply-gps-btn"
          >
            OK
          </Button>
        </div>
      </div>
    </div>
  );
}
