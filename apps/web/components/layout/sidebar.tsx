'use client';

import { Link, usePathname } from '@/i18n/navigation';
import { useTranslations } from 'next-intl';
import { navItems } from '@/lib/constants';

export function Sidebar({ onNavigate, mobile = false }: { onNavigate?: () => void; mobile?: boolean }) {
  const t = useTranslations('nav');
  const pathname = usePathname();

  const content = (
    <nav className="flex flex-col gap-1 p-4" aria-label={t('title')}>
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`rounded-md px-3 py-2 text-sm transition-colors ${
              isActive
                ? 'bg-primary font-medium text-primary-foreground'
                : 'text-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
          >
            {t(item.labelKey)}
          </Link>
        );
      })}
    </nav>
  );

  if (mobile) {
    return content;
  }

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-secondary/30 lg:block">
      {content}
    </aside>
  );
}
