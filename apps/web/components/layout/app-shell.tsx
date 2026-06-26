import { getTranslations } from 'next-intl/server';
import { Sidebar } from './sidebar';
import { LanguageSwitcher } from './language-switcher';
import { UserMenu } from '@/components/auth/user-menu';

export async function AppShell({ children }: { children: React.ReactNode }) {
  const t = await getTranslations('common');

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b bg-primary px-6 py-3 text-primary-foreground">
        <span className="font-display text-lg font-semibold">
          {t('appTitle')}
        </span>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <UserMenu />
        </div>
      </header>
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
