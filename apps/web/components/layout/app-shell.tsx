import { getTranslations } from 'next-intl/server';
import { Sidebar } from './sidebar';
import { LanguageSwitcher } from './language-switcher';
import { UserMenu } from '@/components/auth/user-menu';
import { FieldModeIndicator } from '@/components/field/field-mode-indicator';
import { MobileNav } from './mobile-nav';

export async function AppShell({ children }: { children: React.ReactNode }) {
  const t = await getTranslations('common');

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 flex items-center justify-between border-b bg-primary px-4 py-3 text-primary-foreground sm:px-6">
        <div className="flex items-center gap-3">
          <MobileNav />
          <span className="font-display text-base font-semibold sm:text-lg">
            {t('appTitle')}
          </span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <FieldModeIndicator />
          <LanguageSwitcher />
          <UserMenu />
        </div>
      </header>
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
