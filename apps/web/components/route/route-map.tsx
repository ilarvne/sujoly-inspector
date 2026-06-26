'use client';

import { useMemo } from 'react';
import { Map, Marker, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { OSM_TILE_URL, ZHAMBYL_CENTER } from '@/lib/constants';

const MAP_STYLE = {
  version: 8 as const,
  sources: {
    osm: {
      type: 'raster' as const,
      tiles: [OSM_TILE_URL],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [
    { id: 'osm', type: 'raster' as const, source: 'osm' },
  ],
};

interface RouteMapProps {
  stops: { lat: number; lon: number }[];
}

export function RouteMap({ stops }: RouteMapProps) {
  const lineData = useMemo<GeoJSON.FeatureCollection>(
    () => ({
      type: 'FeatureCollection',
      features:
        stops.length >= 2
          ? [
              {
                type: 'Feature' as const,
                geometry: {
                  type: 'LineString' as const,
                  coordinates: stops.map((s) => [s.lon, s.lat]),
                },
                properties: {},
              },
            ]
          : [],
    }),
    [stops],
  );

  return (
    <Map
      initialViewState={ZHAMBYL_CENTER}
      style={{ width: '100%', height: '100%' }}
      mapStyle={MAP_STYLE}
    >
      <Source id="route-line" type="geojson" data={lineData}>
        <Layer
          id="route-line"
          type="line"
          paint={{
            'line-color': '#2563eb',
            'line-width': 3,
            'line-dasharray': [2, 1],
          }}
        />
      </Source>
      {stops.map((stop, idx) => (
        <Marker
          key={idx}
          longitude={stop.lon}
          latitude={stop.lat}
          anchor="center"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 28,
              height: 28,
              borderRadius: '50%',
              backgroundColor:
                idx === 0
                  ? '#22c55e'
                  : idx === stops.length - 1
                    ? '#ef4444'
                    : '#2563eb',
              color: '#fff',
              fontWeight: 'bold',
              fontSize: 14,
              border: '2px solid #fff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
            }}
          >
            {idx + 1}
          </div>
        </Marker>
      ))}
    </Map>
  );
}
