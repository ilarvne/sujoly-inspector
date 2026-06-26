import '../globals.css';
import type { Metadata, Viewport } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { hasLocale } from 'next-intl';
import { notFound } from 'next/navigation';
import { NextIntlClientProvider } from 'next-intl';
import { Inter, Manrope } from 'next/font/google';
import { routing } from '@/i18n/routing';
import { getMessages } from 'next-intl/server';
import { AppShell } from '@/components/layout/app-shell';
import { QueryProvider } from '@/components/providers/query-provider';
import { SWRegister } from '@/components/pwa/sw-register';

const inter = Inter({
  subsets: ['latin', 'cyrillic', 'cyrillic-ext'],
  display: 'swap',
  variable: '--font-inter',
});

const manrope = Manrope({
  subsets: ['latin', 'cyrillic', 'cyrillic-ext'],
  display: 'swap',
  variable: '--font-manrope',
});

export const metadata: Metadata = {
  applicationName: 'Zhambyl ГТС',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Zhambyl ГТС',
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  themeColor: '#0b4f6c',
  width: 'device-width',
  initialScale: 1,
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale} className={`${inter.variable} ${manrope.variable} antialiased`}>
      <body>
        <SWRegister>
          <NextIntlClientProvider messages={messages}>
            <QueryProvider>
              <AppShell>{children}</AppShell>
            </QueryProvider>
          </NextIntlClientProvider>
        </SWRegister>
      </body>
    </html>
  );
}
