'use client';

import { usePathname, useRouter } from '@/i18n/navigation';
import { routing } from '@/i18n/routing';
import { useTranslations, useLocale } from 'next-intl';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('common');

  const switchLocale = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale });
  };

  return (
    <select
      data-testid="language-switcher"
      aria-label={t('languageSwitcher')}
      value={locale}
      onChange={(e) => switchLocale(e.target.value)}
      className="rounded-md border bg-background px-3 py-1.5 text-sm text-foreground"
    >
      {routing.locales.map((l) => (
        <option key={l} value={l}>
          {t(`locale.${l}`)}
        </option>
      ))}
    </select>
  );
}
