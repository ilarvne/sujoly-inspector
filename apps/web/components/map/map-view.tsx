'use client';

import { useMemo } from 'react';
import Map, { Source, Layer, type MapMouseEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useMapStore } from '@/lib/stores/map-store';
import { useFilterStore } from '@/lib/stores/filter-store';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { OSM_TILE_URL, ZHAMBYL_CENTER, STATUS_COLORS_HEX } from '@/lib/constants';

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

export function MapView() {
  const setViewport = useMapStore((s) => s.setViewport);
  const filters = useFilterStore();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);
  const { data: geojson } = useStructuresGeoJSON(filters);

  const sourceData = useMemo<GeoJSON.FeatureCollection>(() => {
    if (!geojson) return { type: 'FeatureCollection', features: [] };
    return {
      type: 'FeatureCollection',
      features: geojson.features
        .filter((f) => f.geometry !== null)
        .map((f) => ({
          type: 'Feature' as const,
          geometry: f.geometry!,
          properties: f.properties,
        })),
    };
  }, [geojson]);

  return (
    <Map
      initialViewState={ZHAMBYL_CENTER}
      style={{ width: '100%', height: '100%' }}
      mapStyle={MAP_STYLE}
      interactiveLayerIds={['structures']}
      onLoad={(e) => {
        (window as Window & { __maplibreMap?: unknown }).__maplibreMap = e.target;
      }}
      onClick={(e: MapMouseEvent) => {
        if (e.features && e.features.length > 0) {
          const feature = e.features[0];
          if (feature.properties && feature.properties.id) {
            setSelectedId(feature.properties.id as string);
          }
        }
      }}
      onMove={(e) => setViewport(e.viewState)}
    >
      <Source
        id="structures"
        type="geojson"
        data={sourceData}
      >
        <Layer
          id="structures"
          type="circle"
          paint={{
            'circle-radius': 7,
            'circle-color': [
              'match',
              ['get', 'condition'],
              'normal', STATUS_COLORS_HEX.normal,
              'inspection', STATUS_COLORS_HEX.inspection,
              'repair', STATUS_COLORS_HEX.repair,
              'critical', STATUS_COLORS_HEX.critical,
              STATUS_COLORS_HEX.missing,
            ],
            'circle-stroke-width': 1.5,
            'circle-stroke-color': '#ffffff',
          }}
        />
      </Source>
    </Map>
  );
}
