export const navItems = [
  { href: '/' as const, labelKey: 'home' },
  { href: '/dashboard' as const, labelKey: 'dashboard' },
  { href: '/map' as const, labelKey: 'map' },
  { href: '/objects' as const, labelKey: 'objects' },
  { href: '/copilot' as const, labelKey: 'copilot' },
  { href: '/reports' as const, labelKey: 'reports' },
  { href: '/hydrofinder' as const, labelKey: 'hydrofinder' },
] as const;

export const locales = ['ru', 'kk', 'en'] as const;
