'use client';

import { usePathname, useRouter } from '@/i18n/navigation';
import { routing } from '@/i18n/routing';
import { useTranslations } from 'next-intl';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations('common');

  const switchLocale = (locale: string) => {
    router.replace(pathname, { locale });
  };

  return (
    <select
      data-testid="language-switcher"
      onChange={(e) => switchLocale(e.target.value)}
      className="rounded-md border bg-background px-3 py-1.5 text-sm text-foreground"
    >
      {routing.locales.map((locale) => (
        <option key={locale} value={locale}>
          {t(`locale.${locale}`)}
        </option>
      ))}
    </select>
  );
}
