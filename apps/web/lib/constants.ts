export const navItems = [
  { href: '/' as const, labelKey: 'home' },
  { href: '/dashboard' as const, labelKey: 'dashboard' },
  { href: '/map' as const, labelKey: 'map' },
  { href: '/objects' as const, labelKey: 'objects' },
  { href: '/field' as const, labelKey: 'field' },
  { href: '/copilot' as const, labelKey: 'copilot' },
  { href: '/reports' as const, labelKey: 'reports' },
  { href: '/hydrofinder' as const, labelKey: 'hydrofinder' },
] as const;

export const locales = ['ru', 'kk', 'en'] as const;

export const OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

export const ZHAMBYL_CENTER = { longitude: 72.6, latitude: 44.0, zoom: 7 };

export const STATUS_COLORS_HEX: Record<string, string> = {
  normal: '#22c55e',
  inspection: '#eab308',
  repair: '#f97316',
  critical: '#ef4444',
  missing: '#9ca3af',
};
