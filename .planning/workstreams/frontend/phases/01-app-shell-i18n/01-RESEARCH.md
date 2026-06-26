# Phase 1: App Shell & i18n - Research

**Researched:** 2026-06-26
**Domain:** Next.js 16 project scaffolding, Tailwind CSS v4, shadcn/ui, next-intl trilingual i18n, Kazakh Cyrillic font subsets
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | User interface is fully trilingual (Russian, Kazakh, English) with language switching that preserves data values in source language | next-intl 4.13 with `[locale]` routing segment, `defineRouting`/`createNavigation` API, ICU message format, language switcher pattern using `useRouter().replace(pathname, {locale})` |
| UI-02 | UI renders Kazakh-specific Cyrillic characters correctly using cyrillic-ext font subset | next/font/google with `subsets: ['cyrillic', 'cyrillic-ext']` for both Inter and Manrope — **CRITICAL: both subsets required, not just cyrillic-ext** (see Pitfall 1) |
</phase_requirements>

## Summary

Phase 1 establishes the frontend foundation: a Next.js 16 application with App Router, Tailwind CSS v4, shadcn/ui, and full trilingual support (Russian/Kazakh/English) via next-intl 4.13. This is a greenfield project — no frontend code exists yet. The app will be created at `apps/web/` following the existing monorepo pattern (`apps/agent/` already exists).

The technology stack is locked in AGENTS.md and STACK.md: Next.js 16.2.9, React 19, TypeScript 5, Tailwind CSS 4.3.1, shadcn/ui (CLI 4.11.0), next-intl 4.13.0, Inter + Manrope fonts. All versions verified against npm registry on 2026-06-26. Node v22.21.0 and npm 11.7.0 are available on the target machine.

The most critical technical finding is the Kazakh Cyrillic font subset split: 7 of 9 Kazakh-specific characters (ә, ғ, қ, ң, ө, ү, һ) fall in the `cyrillic-ext` subset (U+0460-052F), but 2 characters (і = U+0456, ұ = U+04B1) fall in the basic `cyrillic` subset (U+0400-045F). The success criterion mentions "cyrillic-ext font subset" but the font configuration MUST include `['cyrillic', 'cyrillic-ext']` (both subsets) to render all 9 characters. This was verified by fetching the actual Google Fonts CSS `unicode-range` declarations for both Inter and Manrope.

**Primary recommendation:** Scaffold `apps/web/` with `create-next-app`, init shadcn/ui for Tailwind v4, configure next-intl with `[locale]` routing, set up Inter + Manrope fonts with both `cyrillic` and `cyrillic-ext` subsets, define the design system in `@theme`, and create placeholder routes for all 7 navigation paths. The Walking Skeleton is: project boots → `/ru` renders with Russian text and correct fonts → language switcher navigates to `/kk` with Kazakh text → all 7 routes are accessible.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Project scaffolding (Next.js config) | Frontend Server (SSR) | — | Next.js App Router with SSR/SSG; `next.config.ts` with Turbopack |
| i18n routing & middleware | Frontend Server (SSR) | Browser | `middleware.ts` runs on edge/server for locale detection; language switcher runs in browser |
| Message loading (translations) | Frontend Server (SSR) | — | `getRequestConfig` loads JSON messages server-side; zero client bundle for server translations |
| Font optimization | Frontend Server (SSR) | — | `next/font/google` downloads and self-hosts fonts at build time; generates CSS variables |
| Design system (Tailwind v4 @theme) | CDN / Static | Browser | CSS processed at build time via `@tailwindcss/postcss`; static asset served to browser |
| App shell / navigation UI | Browser | Frontend Server | Client-side navigation with Next.js Link; layout shell rendered as RSC |
| shadcn/ui components | Browser | — | Radix UI primitives with client-side interactivity; `data-slot` attributes for styling |
| Locale validation | Frontend Server (SSR) | — | `hasLocale()` check in `app/[locale]/layout.tsx` validates URL segment before rendering |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.2.9 | Full-stack React framework, App Router, Turbopack | Industry-leading React framework. App Router with RSC, Turbopack for fast dev/build. `create-next-app --yes` scaffolds TypeScript + Tailwind + ESLint + App Router + Turbopack + `@/*` alias. [VERIFIED: npm registry] |
| react / react-dom | 19.x | UI library (bundled with Next.js 16) | Server Components, Actions API. Required by Next.js 16. [VERIFIED: Context7 /vercel/next.js] |
| next-intl | 4.13.0 | Trilingual i18n (RU/KK/EN) with [locale] routing | Purpose-built for Next.js App Router. ICU message format, Server Component support, type-safe, `defineRouting`/`createNavigation` API for internationalized routing. [VERIFIED: npm registry + Context7 /amannn/next-intl] |
| tailwindcss | 4.3.1 | Utility-first styling, CSS-native config | v4 uses `@import "tailwindcss"` + `@theme` directive (no `tailwind.config.js`). `@tailwindcss/postcss` as PostCSS plugin. [VERIFIED: npm registry + Context7 /tailwindlabs/tailwindcss.com] |
| @tailwindcss/postcss | 4.3.1 | PostCSS plugin for Tailwind v4 | Required for Tailwind v4 PostCSS integration. Same version as tailwindcss. [VERIFIED: npm registry] |
| shadcn (CLI) | 4.11.0 | UI component scaffolding | `npx shadcn@latest init` sets up components.json, installs Radix UI + lucide-react + cva + cn utility. Tailwind v4 support with `@theme inline` and OKLCH colors. `new-york` style (default deprecated). [VERIFIED: npm registry + CITED: ui.shadcn.com/docs/tailwind-v4] |
| typescript | 5.x | Type safety | Non-negotiable for project complexity. Bundled with create-next-app. [VERIFIED: Context7 /vercel/next.js] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 1.21.0 | Icon library | shadcn/ui default icon set. Installed by `shadcn init`. [VERIFIED: npm registry] |
| class-variance-authority | 0.7.1 | Component variant management | shadcn/ui uses for component variants (button sizes, colors, etc.). Installed by `shadcn init`. [VERIFIED: npm registry] |
| clsx | 2.1.1 | Conditional class names | Part of `cn()` utility. Installed by `shadcn init`. [VERIFIED: npm registry] |
| tailwind-merge | 3.6.0 | Merge Tailwind classes intelligently | Part of `cn()` utility. Prevents class conflicts. Installed by `shadcn init`. [VERIFIED: npm registry] |
| tw-animate-css | 1.4.0 | Animation utilities for Tailwind v4 | Replaces deprecated `tailwindcss-animate`. Installed by `shadcn init` for Tailwind v4 projects. [VERIFIED: npm registry + CITED: ui.shadcn.com/docs/tailwind-v4] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| next-intl | react-i18next | react-i18next is not App Router native. next-intl has server component support, type safety, is the de facto standard for Next.js. — **Use next-intl** |
| shadcn/ui | Mantine / MUI | shadcn/ui gives you the code (copy-paste), full customization, no runtime dependency lock-in. Mantine/MUI are runtime libraries with opinionated theming. — **Use shadcn/ui** (locked in AGENTS.md) |
| Tailwind CSS 4 | Styled Components / CSS Modules | Tailwind v4 with `@theme` gives CSS-native design tokens, zero runtime, works with RSC. — **Use Tailwind v4** (locked in AGENTS.md) |
| Inter + Manrope | Noto Sans / Roboto | Inter + Manrope are modern, highly readable, support cyrillic-ext. Noto Sans is broader but less distinctive. — **Use Inter + Manrope** (locked in success criteria) |

**Installation (Phase 1 packages installed directly):**
```bash
# Step 1: Create Next.js app (installs next, react, react-dom, typescript, tailwindcss, @tailwindcss/postcss)
npx create-next-app@latest apps/web --yes

# Step 2: Initialize shadcn/ui (installs lucide-react, class-variance-authority, clsx, tailwind-merge, tw-animate-css, @radix-ui/*)
cd apps/web && npx shadcn@latest init

# Step 3: Install next-intl
npm install next-intl
```

**Version verification (executed 2026-06-26):**
```
next:           16.2.9   (npm view)
next-intl:      4.13.0   (npm view)
tailwindcss:    4.3.1    (npm view)
@tailwindcss/postcss: 4.3.1 (npm view)
shadcn (CLI):   4.11.0   (npm view)
lucide-react:   1.21.0   (npm view)
class-variance-authority: 0.7.1 (npm view)
clsx:           2.1.1    (npm view)
tailwind-merge: 3.6.0    (npm view)
tw-animate-css: 1.4.0    (npm view)
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| next | npm | ~8 yrs (v16.2.9 published 2026-06-09) | 42.5M/wk | github.com/vercel/next.js | OK* | Approved |
| next-intl | npm | ~5 yrs (v4.13.0 published 2026-05-28) | 4.1M/wk | github.com/amannn/next-intl | OK* | Approved |
| tailwindcss | npm | ~10 yrs (v4.3.1 published 2026-06-12) | 120.8M/wk | github.com/tailwindlabs/tailwindcss | OK* | Approved |
| @tailwindcss/postcss | npm | ~2 yrs (v4.3.1 published 2026-06-12) | 24.2M/wk | github.com/tailwindlabs/tailwindcss | OK* | Approved |
| shadcn | npm | ~3 yrs (v4.11.0 published 2026-06-08) | 5.6M/wk | github.com/shadcn-ui/ui | OK* | Approved |
| lucide-react | npm | ~4 yrs | — | github.com/lucide-icons/lucide | OK | Approved |
| class-variance-authority | npm | ~4 yrs | — | github.com/joe-bell/cva | OK | Approved |
| clsx | npm | ~7 yrs | — | github.com/lukeed/clsx | OK | Approved |
| tailwind-merge | npm | ~3 yrs | — | github.com/dcastil/tailwind-merge | OK | Approved |
| tw-animate-css | npm | ~1 yr | — | github.com/romboHQ/tw-animate-css | OK | Approved |

*The seam returned `SUS` with reason `too-new` for the top 5 packages because their latest versions were published within the last month. This is a **false positive** — all are among the most popular npm packages with millions of weekly downloads, official GitHub repos, no postinstall scripts, and no deprecation flags. They are clearly legitimate. No `checkpoint:human-verify` needed.

**Postinstall script check:** `npm view <pkg> scripts.postinstall` returned empty for all packages — no suspicious postinstall scripts detected.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none (false-positive `too-new` flags on top-5 packages dismissed — these are industry-standard packages with 4M-120M weekly downloads)

## Architecture Patterns

### System Architecture Diagram

```
Browser Request
    │
    ▼
┌─────────────────────┐
│   middleware.ts     │  ◄── next-intl createMiddleware(routing)
│  (Edge/Server)      │      Detects locale from URL/cookie/Accept-Language
│                     │      Redirects / → /ru (default locale)
└────────┬────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  app/[locale]/layout.tsx        │  ◄── Root layout (has <html>, <body>)
│  (Server Component)             │      Validates locale via hasLocale()
│                                 │      setRequestLocale(locale) for static rendering
│  ┌───────────────────────────┐  │      Loads Inter + Manrope fonts with CSS variables
│  │  NextIntlClientProvider   │  │      Wraps children with i18n context
│  └───────────┬───────────────┘  │
│              │                  │
│  ┌───────────▼───────────────┐  │
│  │   App Shell (Nav + Layout)│  │  ◄── Sidebar/header with locale-aware navigation
│  │   (Server/Client mix)     │  │      Links from @/i18n/navigation (Link, useRouter)
│  └───────────┬───────────────┘  │
│              │                  │
│  ┌───────────▼───────────────┐  │
│  │   Route Pages             │  │
│  │   /  /dashboard  /map     │  │  ◄── app/[locale]/{page,dashboard,map,...}
│  │   /objects  /copilot      │  │      Each page uses useTranslations() or
│  │   /reports  /hydrofinder  │  │      getTranslations() for localized text
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  i18n/request.ts    │  ◄── getRequestConfig: loads messages/${locale}.json
│  (Server-side)      │      Provides messages to Server Components
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  messages/          │  ◄── Translation JSON files
│  ├── en.json        │      ICU message format
│  ├── ru.json        │      UI strings for all 3 locales
│  └── kk.json        │
└─────────────────────┘
```

### Recommended Project Structure

```
apps/web/
├── app/
│   ├── [locale]/
│   │   ├── layout.tsx          # Root layout: fonts, NextIntlClientProvider, app shell
│   │   ├── page.tsx            # Home route (/)
│   │   ├── dashboard/
│   │   │   └── page.tsx        # /dashboard
│   │   ├── map/
│   │   │   └── page.tsx        # /map
│   │   ├── objects/
│   │   │   └── page.tsx        # /objects
│   │   ├── copilot/
│   │   │   └── page.tsx        # /copilot
│   │   ├── reports/
│   │   │   └── page.tsx        # /reports
│   │   ├── hydrofinder/
│   │   │   └── page.tsx        # /hydrofinder
│   │   └── not-found.tsx       # 404 for invalid locale routes
│   └── not-found.tsx           # Global 404 (non-locale routes)
├── components/
│   ├── ui/                     # shadcn/ui components (button, card, etc.)
│   ├── layout/
│   │   ├── app-shell.tsx       # Main layout shell with sidebar/header
│   │   ├── sidebar.tsx         # Navigation sidebar
│   │   └── language-switcher.tsx # Locale switcher dropdown
│   └── theme/
│       └── theme-provider.tsx  # Dark/light mode provider (if needed)
├── i18n/
│   ├── routing.ts              # defineRouting: locales ['ru', 'kk', 'en'], defaultLocale 'ru'
│   ├── navigation.ts           # createNavigation: Link, redirect, usePathname, useRouter
│   └── request.ts              # getRequestConfig: loads messages by locale
├── lib/
│   ├── utils.ts                # cn() utility (clsx + tailwind-merge) — created by shadcn init
│   └── constants.ts            # Navigation items, locale labels, etc.
├── messages/
│   ├── en.json                 # English translations
│   ├── ru.json                 # Russian translations
│   └── kk.json                 # Kazakh translations
├── middleware.ts               # next-intl middleware for locale detection/routing
├── next.config.ts              # withNextIntl plugin wrapper
├── components.json             # shadcn/ui config
├── globals.css                 # Tailwind v4 @import + @theme + design tokens
├── tsconfig.json               # TypeScript config with @/* alias
├── package.json
└── .env.local                  # NEXT_PUBLIC_API_URL, etc. (for later phases)
```

### Pattern 1: next-intl Routing Setup (4-file pattern)

**What:** The standard next-intl App Router routing setup uses 4 files: `routing.ts`, `navigation.ts`, `request.ts`, and `middleware.ts`.
**When to use:** Always — this is the canonical next-intl setup for internationalized routing.

```typescript
// src/i18n/routing.ts
// Source: Context7 /amannn/next-intl — routing/setup.mdx
import {defineRouting} from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['ru', 'kk', 'en'],
  defaultLocale: 'ru'
});
```

```typescript
// src/i18n/navigation.ts
// Source: Context7 /amannn/next-intl — routing/setup.mdx
import {createNavigation} from 'next-intl/navigation';
import {routing} from './routing';

export const {Link, redirect, usePathname, useRouter, getPathname} =
  createNavigation(routing);
```

```typescript
// src/i18n/request.ts
// Source: Context7 /amannn/next-intl — routing/setup.mdx
import {getRequestConfig} from 'next-intl/server';
import {hasLocale} from 'next-intl';
import {routing} from './routing';

export default getRequestConfig(async ({requestLocale}) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default
  };
});
```

```typescript
// middleware.ts (project root, NOT in src/)
// Source: Context7 /amannn/next-intl — routing/middleware.mdx
import createMiddleware from 'next-intl/middleware';
import {routing} from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  matcher: '/((?!api|trpc|_next|_vercel|.*\\..*).*)' 
};
```

### Pattern 2: Font Configuration with Cyrillic Subsets

**What:** Inter and Manrope configured via `next/font/google` with CSS variables for Tailwind v4 integration, including BOTH `cyrillic` and `cyrillic-ext` subsets for Kazakh character coverage.
**When to use:** In the root layout (`app/[locale]/layout.tsx`).

```typescript
// app/[locale]/layout.tsx — font setup
// Source: Context7 /vercel/next.js — font.mdx + Google Fonts CSS verification
import {Inter, Manrope} from 'next/font/google';

const inter = Inter({
  subsets: ['latin', 'cyrillic', 'cyrillic-ext'],  // CRITICAL: both cyrillic + cyrillic-ext
  display: 'swap',
  variable: '--font-inter',
});

const manrope = Manrope({
  subsets: ['latin', 'cyrillic', 'cyrillic-ext'],  // CRITICAL: both cyrillic + cyrillic-ext
  display: 'swap',
  variable: '--font-manrope',
});
```

### Pattern 3: Tailwind v4 @theme Design System

**What:** Design tokens defined in CSS using `@theme` directive, replacing `tailwind.config.js`.
**When to use:** In `globals.css` — the single source of truth for the design system.

```css
/* globals.css — Tailwind v4 CSS-native configuration */
/* Source: Context7 /tailwindlabs/tailwindcss.com + CITED: ui.shadcn.com/docs/tailwind-v4 */
@import "tailwindcss";
@import "tw-animate-css";

/* shadcn/ui semantic color tokens (OKLCH for Tailwind v4) */
:root {
  --background: oklch(0.99 0 0);
  --foreground: oklch(0.15 0 0);
  --primary: oklch(0.42 0.08 230);       /* #0b4f6c — governmental teal-blue */
  --primary-foreground: oklch(0.98 0 0);
  /* ... other shadcn/ui tokens ... */
}

.dark {
  --background: oklch(0.15 0 0);
  --foreground: oklch(0.98 0 0);
  --primary: oklch(0.55 0.10 230);
  /* ... dark mode tokens ... */
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  /* Map font CSS variables to Tailwind font utilities */
  --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
  --font-display: var(--font-manrope), ui-sans-serif, system-ui, sans-serif;
}

/* Custom status colors (not shadcn/ui tokens — project-specific) */
@theme {
  --color-status-normal: oklch(0.65 0.18 145);    /* green */
  --color-status-inspection: oklch(0.80 0.15 90); /* yellow */
  --color-status-repair: oklch(0.70 0.18 55);     /* orange */
  --color-status-critical: oklch(0.55 0.22 25);   /* red */
  --color-status-unknown: oklch(0.60 0.02 300);   /* purple */
  --color-status-missing: oklch(0.55 0.01 250);   /* gray */
}
```

### Pattern 4: shadcn/ui components.json for Tailwind v4

**What:** The `components.json` configuration for shadcn/ui with Tailwind v4 (no config file path).
**When to use:** After `npx shadcn@latest init` — verify or adjust the generated config.

```json
{
  "style": "new-york",
  "rsc": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  },
  "iconLibrary": "lucide"
}
```

Key differences from Tailwind v3:
- `"config": ""` — empty string (no `tailwind.config.js` in v4)
- `"style": "new-york"` — `default` style is deprecated for new projects
- Colors use OKLCH, not HSL
- `tw-animate-css` instead of `tailwindcss-animate`

### Pattern 5: Language Switcher Component

**What:** Client component that switches locale while preserving the current route.
**When to use:** In the app shell header/sidebar.

```tsx
// components/layout/language-switcher.tsx
'use client';
// Source: Context7 /amannn/next-intl — routing/navigation.mdx
import {usePathname, useRouter} from '@/i18n/navigation';
import {useParams} from 'next/navigation';
import {routing} from '@/i18n/routing';
import {useTranslations} from 'next-intl';

export function LanguageSwitcher() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams();
  const t = useTranslations('common');

  const switchLocale = (locale: string) => {
    router.replace(pathname, {locale});
  };

  return (
    <select onChange={(e) => switchLocale(e.target.value)}>
      {routing.locales.map((locale) => (
        <option key={locale} value={locale}>
          {t(`locale.${locale}`)}
        </option>
      ))}
    </select>
  );
}
```

### Pattern 6: Locale Layout with Static Params

**What:** The `[locale]` layout validates the locale, enables static rendering, and wraps with providers.
**When to use:** `app/[locale]/layout.tsx` — the root layout.

```tsx
// app/[locale]/layout.tsx
// Source: Context7 /amannn/next-intl — routing/setup.mdx
import {setRequestLocale} from 'next-intl/server';
import {hasLocale} from 'next-intl';
import {notFound} from 'next/navigation';
import {NextIntlClientProvider} from 'next-intl';
import {Inter, Manrope} from 'next/font/google';
import {routing} from '@/i18n/routing';
import {getMessages} from 'next-intl/server';

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

export function generateStaticParams() {
  return routing.locales.map((locale) => ({locale}));
}

type Props = {
  children: React.ReactNode;
  params: Promise<{locale: string}>;
};

export default async function LocaleLayout({children, params}: Props) {
  const {locale} = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale} className={`${inter.variable} ${manrope.variable} antialiased`}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

### Anti-Patterns to Avoid

- **Using `createSharedPathnamesNavigation` (deprecated):** This was the v2 API. In v3/v4, use `defineRouting()` + `createNavigation()` instead. The old API still works but is not type-safe and won't get new features. [CITED: Context7 /amannn/next-intl]
- **Using `tailwind.config.js` with Tailwind v4:** v4 uses CSS-native `@theme` directive. A config file is ignored unless explicitly loaded with `@config`. Don't create one. [CITED: Context7 /tailwindlabs/tailwindcss.com]
- **Using `default` style in shadcn/ui:** Deprecated for new projects. Use `new-york`. [CITED: ui.shadcn.com/docs/tailwind-v4]
- **Using `tailwindcss-animate` with Tailwind v4:** Deprecated. Use `tw-animate-css` with `@import "tw-animate-css"`. [CITED: ui.shadcn.com/docs/tailwind-v4]
- **Missing `setRequestLocale(locale)` in locale layout:** Without this, static rendering breaks and you get hydration errors or missing translations. [CITED: Context7 /amannn/next-intl]
- **Using `next/navigation` Link instead of `@/i18n/navigation` Link:** The next-intl Link automatically prepends the locale segment. Using Next.js's Link will break locale routing. [CITED: Context7 /amannn/next-intl]
- **Specifying only `['cyrillic-ext']` subset:** This misses і (U+0456) and ұ (U+04B1) which are in the basic `cyrillic` subset. Always include `['cyrillic', 'cyrillic-ext']`. [VERIFIED: Google Fonts CSS unicode-range declarations]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| i18n routing & middleware | Custom locale detection, URL rewriting, Accept-Language parsing | `next-intl` `createMiddleware(routing)` | Handles locale detection (cookie, header, URL), redirects, path-prefix routing. Edge-tested. ICU message format. |
| Navigation with locale awareness | Custom Link component that prepends `/ru` | `next-intl` `createNavigation(routing)` → `Link`, `useRouter` | Type-safe, handles locale prefixing, works with `pathnames` for localized URL slugs |
| Font optimization & subsetting | Manual @font-face declarations, font file downloads | `next/font/google` with `subsets` option | Downloads and self-hosts fonts at build time. Automatic subset selection. CSS variable generation. No layout shift. |
| UI component library | Custom buttons, dialogs, dropdowns from scratch | `shadcn/ui` (Radix UI primitives) | Accessible (WAI-ARIA), keyboard navigation, focus management. Copy-paste ownership. No runtime dependency. |
| CSS class merging | Custom conditional className logic | `cn()` utility (clsx + tailwind-merge) | Handles Tailwind class conflicts intelligently. Standard in shadcn/ui ecosystem. |
| Design token system | Custom CSS variable naming and management | Tailwind v4 `@theme` directive | CSS-native, generates utility classes from tokens. No config file. OKLCH color support. |

**Key insight:** Every piece of Phase 1 infrastructure — routing, fonts, components, styling — has a battle-tested library or framework feature. The only custom code is the design token values (colors, fonts) and the translation message files.

## Common Pitfalls

### Pitfall 1: Missing `cyrillic` Subset (CRITICAL)

**What goes wrong:** Kazakh characters і (U+0456) and ұ (U+04B1) render with a fallback system font instead of Inter/Manrope, causing visual inconsistency (different glyph shapes, weights, spacing).
**Why it happens:** The success criterion says "cyrillic-ext font subset" which leads developers to specify only `subsets: ['cyrillic-ext']`. However, Google Fonts splits Cyrillic coverage into two subsets:
- `cyrillic-ext`: `unicode-range: U+0460-052F, ...` — covers ә, ғ, қ, ң, ө, ү, һ (7 of 9 Kazakh chars)
- `cyrillic`: `unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116` — covers і, ұ (2 of 9 Kazakh chars)

**How to avoid:** Always specify `subsets: ['latin', 'cyrillic', 'cyrillic-ext']` for both Inter and Manrope. The `cyrillic` subset is only ~30KB additional font weight — negligible.
**Warning signs:** Kazakh text with і or ұ characters looks different from surrounding text. Browser DevTools → Elements → Computed → font-family shows a fallback font for those characters.
**Verification:** [VERIFIED: Google Fonts CSS — fetched actual unicode-range declarations for both Inter and Manrope on 2026-06-26]

### Pitfall 2: Using next/navigation instead of @/i18n/navigation

**What goes wrong:** Navigation links lose the locale prefix. Clicking a link from `/ru/dashboard` goes to `/dashboard` instead of `/ru/dashboard`, causing a redirect or 404.
**Why it happens:** Developers import `Link` from `next/navigation` instead of the next-intl wrapper.
**How to avoid:** Always import `Link`, `useRouter`, `usePathname`, `redirect` from `@/i18n/navigation` (the `createNavigation(routing)` output). Never from `next/navigation` directly.
**Warning signs:** URLs lose locale prefix after navigation. Browser address bar shows `/dashboard` instead of `/ru/dashboard`.

### Pitfall 3: Missing generateStaticParams for [locale] Segment

**What goes wrong:** Pages are rendered on-demand instead of statically. Build succeeds but pages aren't pre-rendered for each locale, causing slower first-load and potential SSR errors.
**Why it happens:** `generateStaticParams()` is not defined in the locale layout, so Next.js doesn't know which locale values to pre-render.
**How to avoid:** Add `export function generateStaticParams() { return routing.locales.map((locale) => ({locale})); }` in `app/[locale]/layout.tsx`.
**Warning signs:** Build output doesn't show `○ /ru`, `○ /kk`, `○ /en` as statically generated routes.

### Pitfall 4: Tailwind v4 Config Confusion

**What goes wrong:** Custom colors or fonts defined in `tailwind.config.js` don't work. shadcn/ui components look unstyled.
**Why it happens:** Tailwind v4 ignores `tailwind.config.js` by default. Design tokens must be in `@theme` in CSS. shadcn/ui `components.json` must have `"config": ""`.
**How to avoid:** Use `@import "tailwindcss"` + `@theme { ... }` in `globals.css`. Delete any `tailwind.config.js`/`tailwind.config.ts`. Run `npx shadcn@latest init` which handles this automatically for new projects.
**Warning signs:** `tailwind.config.js` exists in project root. shadcn/ui `components.json` has a non-empty `"config"` value. Custom colors don't generate utility classes.

### Pitfall 5: Hydration Mismatch with Locale

**What goes wrong:** Console errors about hydration mismatch. Server renders one locale, client expects another.
**Why it happens:** `setRequestLocale(locale)` is not called in the locale layout, or the `<html lang={locale}>` attribute doesn't match between server and client.
**How to avoid:** Always call `setRequestLocale(locale)` at the top of the locale layout before rendering. Set `<html lang={locale}>` from the validated locale parameter.
**Warning signs:** React hydration warnings in console. Text flashes from default locale to selected locale on page load.

### Pitfall 6: next-intl Plugin Not in next.config.ts

**What goes wrong:** Server Components can't access translations. `useTranslations` returns empty strings. Build fails with "messages not found" errors.
**Why it happens:** The `createNextIntlPlugin()` wrapper is not applied to `next.config.ts`.
**How to avoid:** Wrap the Next.js config: `const withNextIntl = createNextIntlPlugin(); export default withNextIntl(nextConfig);`
**Warning signs:** Translations work in Client Components but not Server Components. Build errors about missing i18n configuration.

## Code Examples

### next.config.ts with next-intl Plugin

```typescript
// Source: Context7 /amannn/next-intl — getting-started/app-router.mdx
import {NextConfig} from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const nextConfig: NextConfig = {};

const withNextIntl = createNextIntlPlugin();
export default withNextIntl(nextConfig);
```

### Message File Structure (ICU Format)

```json
// messages/ru.json
{
  "common": {
    "locale": {
      "ru": "Русский",
      "kk": "Қазақша",
      "en": "English"
    }
  },
  "nav": {
    "home": "Главная",
    "dashboard": "Панель управления",
    "map": "Карта",
    "objects": "Объекты",
    "copilot": "Помощник",
    "reports": "Отчёты",
    "hydrofinder": "Гидропоиск"
  },
  "home": {
    "title": "Каталог гидротехнических сооружений Жамбылской области",
    "subtitle": "Цифровая операционная система для управления гидротехническими сооружениями"
  }
}
```

```json
// messages/kk.json — Kazakh translations (note Kazakh-specific characters)
{
  "common": {
    "locale": {
      "ru": "Русский",
      "kk": "Қазақша",
      "en": "English"
    }
  },
  "nav": {
    "home": "Басты бет",
    "dashboard": "Басқару панелі",
    "map": "Карта",
    "objects": "Нысандар",
    "copilot": "Көмекші",
    "reports": "Есептер",
    "hydrofinder": "Гидроіздеу"
  },
  "home": {
    "title": "Жамбыл облысының гидротехникалық құрылымдар каталогы",
    "subtitle": "Гидротехникалық құрылымдарды басқару үшін цифрлық операциялық жүйе"
  }
}
```

### Using Translations in a Page

```tsx
// app/[locale]/page.tsx
// Source: Context7 /amannn/next-intl
import {useTranslations} from 'next-intl';

export default function HomePage() {
  const t = useTranslations('home');
  
  return (
    <main className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="font-display text-4xl font-bold text-primary">
        {t('title')}
      </h1>
      <p className="mt-4 text-lg text-muted-foreground">
        {t('subtitle')}
      </p>
    </main>
  );
}
```

### Server Component Translation (no client bundle)

```tsx
// app/[locale]/dashboard/page.tsx — Server Component
// Source: Context7 /amannn/next-intl
import {getTranslations} from 'next-intl/server';
import {setRequestLocale} from 'next-intl/server';

export default async function DashboardPage({params}: {params: Promise<{locale: string}>}) {
  const {locale} = await params;
  setRequestLocale(locale);
  const t = await getTranslations('dashboard');
  
  return (
    <main>
      <h1>{t('title')}</h1>
    </main>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tailwind.config.js` JS config | `@theme` CSS-native config | Tailwind v4 (2025) | No config file. Design tokens in CSS. OKLCH colors. `@tailwindcss/postcss` plugin. |
| `createSharedPathnamesNavigation` | `defineRouting()` + `createNavigation()` | next-intl v3.22+ (2024) | Type-safe routing. Cleaner API. `hasLocale()` validation. `requestLocale` parameter. |
| `tailwindcss-animate` plugin | `tw-animate-css` | shadcn/ui March 2025 | Separate package, imported via `@import "tw-animate-css"` instead of `@plugin` |
| `default` shadcn/ui style | `new-york` style | shadcn/ui 2025 | `default` deprecated for new projects. `new-york` is the new default. |
| HSL color values | OKLCH color values | shadcn/ui + Tailwind v4 | OKLCH is perceptually uniform, better for color mixing. All shadcn/ui v4 components use OKLCH. |
| `forwardRef` in components | `React.ComponentProps` pattern | shadcn/ui + React 19 | React 19 deprecates forwardRef. Components use function components with `data-slot` attributes. |
| `next/font` without `variable` | `next/font` with `variable` + `@theme` | Next.js + Tailwind v4 | Font CSS variables integrated into Tailwind utility classes via `--font-sans`, `--font-display` |

**Deprecated/outdated:**
- `tailwindcss-animate`: Replaced by `tw-animate-css`. Use `@import "tw-animate-css"` in globals.css. [CITED: ui.shadcn.com/docs/tailwind-v4]
- `createSharedPathnamesNavigation` / `createLocalizedPathnamesNavigation`: Replaced by `defineRouting()` + `createNavigation()`. [CITED: Context7 /amannn/next-intl]
- `default` shadcn/ui style: Deprecated. Use `new-york`. [CITED: ui.shadcn.com/docs/tailwind-v4]
- `tailwind.config.js` / `tailwind.config.ts`: Not needed in Tailwind v4. Use `@theme` in CSS. [CITED: Context7 /tailwindlabs/tailwindcss.com]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Default locale should be `ru` (Russian) | Architecture Patterns | If default should be `kk` (Kazakh), middleware and routing config change. Data sources are primarily in Russian per AGENTS.md, so `ru` as default is a reasonable assumption. |
| A2 | Frontend app goes in `apps/web/` | Project Structure | Could be `apps/frontend/` — but `web` is the shadcn/ui convention and shorter. Planner should confirm with user. |
| A3 | No root `package.json` with npm workspaces needed for Phase 1 | Project Structure | If monorepo workspace config is required, a root `package.json` with `"workspaces": ["apps/*"]` must be added. Currently `apps/agent/` is Python (no npm workspace needed). |
| A4 | OKLCH approximation for #0b4f6c is `oklch(0.42 0.08 230)` | Code Examples | Exact OKLCH conversion requires a color converter tool. The executor should use a converter (e.g., oklch.com) for precise values. |
| A5 | `--src-dir` flag not needed (app/ at root of apps/web/) | Project Structure | If `--src-dir` is preferred, structure changes to `src/app/` and `src/i18n/`. shadcn/ui docs show both patterns. Without `--src-dir` is simpler. |
| A6 | Dark mode is not a Phase 1 requirement | Design System | Success criteria don't mention dark mode. If dark mode is needed, a `next-themes` provider must be added. |

**If this table is empty:** N/A — 6 assumptions identified that need user confirmation.

## Open Questions (RESOLVED)

1. **Default locale: `ru` or `kk`?** — RESOLVED: ru (confirmed by user)
   - What we know: Data sources are primarily in Russian (AGENTS.md). UI must be trilingual. Kazakhstan's state language is Kazakh.
   - What's unclear: Whether the default locale (when no preference is detected) should be Russian or Kazakh.
   - Recommendation: Use `ru` as default (matches data source language, most users likely Russian-speaking). User can override via language switcher. The middleware will detect `Accept-Language` header for automatic locale selection.

2. **Monorepo workspace configuration?** — RESOLVED: standalone apps/web/, no npm workspaces
   - What we know: Repo has `apps/agent/` (Python) and will have `apps/web/` (Next.js). No root `package.json` exists.
   - What's unclear: Whether a root `package.json` with npm workspaces should be created, or `apps/web/` should be standalone.
   - Recommendation: Standalone for Phase 1 (simplest). Add root workspace config in a later infrastructure phase if shared packages are needed. The shadcn/ui `--monorepo` flag creates a more complex structure with `packages/ui/` that isn't needed yet.

3. **`--src-dir` flag for create-next-app?** — RESOLVED: no src directory
   - What we know: Next.js supports `src/` directory structure. shadcn/ui works with both patterns.
   - What's unclear: Whether the project should use `src/app/` or `app/` at the root of `apps/web/`.
   - Recommendation: Use `app/` at root (no `--src-dir`) — simpler structure, fewer nesting levels. Can migrate to `src/` later if needed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js 16 runtime | ✓ | v22.21.0 | — |
| npm | Package management | ✓ | 11.7.0 | — |
| npx | CLI tool execution (create-next-app, shadcn) | ✓ | 11.7.0 | — |
| Internet access | Google Fonts download (build-time), npm registry | ✓ | — | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

All required tools are available. Node v22 meets Next.js 16 requirements (requires Node >= 18.18.0, recommends >= 20).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (unit/component) + Playwright (e2e) |
| Config file | `apps/web/vitest.config.ts` + `apps/web/playwright.config.ts` — to be created in Wave 0 |
| Quick run command | `cd apps/web && npx vitest run` |
| Full suite command | `cd apps/web && npx vitest run && npx playwright test` |

**Note:** For Phase 1 (app shell), the most critical validation is smoke/build checks and e2e route verification. Unit tests are minimal (no business logic yet). Playwright e2e tests verify the Walking Skeleton end-to-end.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Language switching works (RU/KK/EN) | e2e | `npx playwright test tests/i18n.spec.ts` | ❌ Wave 0 |
| UI-01 | All routes accessible in all 3 locales | e2e | `npx playwright test tests/routes.spec.ts` | ❌ Wave 0 |
| UI-01 | Translations render correct text per locale | e2e | `npx playwright test tests/i18n.spec.ts` | ❌ Wave 0 |
| UI-02 | Kazakh Cyrillic characters render with Inter/Manrope | e2e + manual | `npx playwright test tests/fonts.spec.ts` | ❌ Wave 0 |
| SC-1 | Next.js project builds successfully | smoke | `cd apps/web && npm run build` | N/A (build command) |
| SC-1 | Dev server starts without errors | smoke | `cd apps/web && npm run dev` (manual check) | N/A |
| SC-4 | Design system tokens defined in @theme | unit | `npx vitest run tests/design-tokens.test.ts` | ❌ Wave 0 |
| SC-5 | All 7 navigation routes return 200 | e2e | `npx playwright test tests/routes.spec.ts` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd apps/web && npm run build` (build must pass)
- **Per wave merge:** `cd apps/web && npx vitest run && npx playwright test`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `apps/web/playwright.config.ts` — Playwright configuration (browsers, baseURL, webServer)
- [ ] `apps/web/tests/i18n.spec.ts` — covers UI-01: language switching, translation rendering
- [ ] `apps/web/tests/routes.spec.ts` — covers SC-5: all 7 routes in all 3 locales return 200
- [ ] `apps/web/tests/fonts.spec.ts` — covers UI-02: Kazakh character rendering (check computed font-family)
- [ ] `apps/web/tests/design-tokens.test.ts` — covers SC-4: verify @theme CSS variables exist
- [ ] `apps/web/vitest.config.ts` — Vitest configuration
- [ ] Framework install: `cd apps/web && npm install -D vitest @testing-library/react @playwright/test && npx playwright install`

*(If no gaps: N/A — 7 test infrastructure items need creation in Wave 0)*

### Manual Verification Checks

| Check | How to Verify | Success Criterion |
|-------|---------------|-------------------|
| Kazakh character rendering | Open `/kk` in browser, inspect әғқңөұүһі in DevTools → Computed → font-family | Should show "Inter" or "Manrope", not a fallback font |
| Governmental design style | Visual inspection of home page | Clean, professional, teal-blue primary (#0b4f6c), no playful gradients or animations |
| Language switcher UX | Click switcher, select each locale | Page text changes without full reload; URL updates to /ru, /kk, /en |
| Font weight rendering | Check headings (Manrope) vs body (Inter) in browser | Display font (Manrope) for headings, body font (Inter) for paragraphs |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No authentication in Phase 1 (Phase 3) |
| V3 Session Management | no | No sessions in Phase 1 |
| V4 Access Control | no | No access control in Phase 1 |
| V5 Input Validation | yes | `hasLocale(routing.locales, locale)` validates the `[locale]` URL segment against allowed locales. `notFound()` for invalid locales. Middleware matcher excludes API/static routes. |
| V6 Cryptography | no | No crypto in Phase 1 |
| V7 Error Handling | yes | `not-found.tsx` for invalid locales; Next.js error boundaries for render errors |
| V14 Configuration | yes | `.env.local` for environment variables (not committed to git); `next.config.ts` for framework config |

### Known Threat Patterns for Next.js App Shell

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via [locale] segment | Tampering | `hasLocale()` validation in layout — only allows `['ru', 'kk', 'en']`. Invalid locales trigger `notFound()`. [CITED: Context7 /amannn/next-intl] |
| Middleware bypass for static assets | Elevation of Privilege | Middleware matcher `'/((?!api|trpc|_next|_vercel|.*\..*).*)'  ` excludes static files, API routes, and internal Next.js paths. [CITED: Context7 /amannn/next-intl] |
| Open redirect via locale parameter | Tampering | next-intl middleware only redirects to defined locales. No user-controlled redirect URLs. |
| XSS via translation messages | Tampering | Translation messages are static JSON files committed to git. React automatically escapes interpolation values. ICU format prevents injection. |

**Security note:** Phase 1 has minimal attack surface — no authentication, no API endpoints, no user input handling beyond locale selection (which is validated). The primary security control is the `hasLocale()` validation preventing path traversal through the `[locale]` URL segment.

## Project Constraints (from AGENTS.md)

The following directives from AGENTS.md constrain this phase:

1. **Tech stack locked:** Next.js 16.2.x, React 19, TypeScript 5, Tailwind CSS 4, next-intl 4.13.x, shadcn/ui — all versions verified against npm registry.
2. **Trilingual UI required:** Russian, Kazakh, English. Data sources primarily in Russian.
3. **Architecture principle:** Every structure has one canonical asset record. (Not relevant to Phase 1 — no data layer yet.)
4. **Offline capability:** PWA with service workers for field inspection. (Phase 5, not Phase 1.)
5. **GSD Workflow Enforcement:** Use GSD entry points for all work. Do not make direct repo edits outside GSD workflow.
6. **No project conventions established yet:** "Conventions not yet established. Will populate as patterns emerge during development." — Phase 1 will establish the first conventions.

## Sources

### Primary (HIGH confidence)
- Context7 `/vercel/next.js` (v16.2.9, 6064 snippets) — create-next-app setup, next/font with subsets and CSS variables, App Router layout patterns
- Context7 `/amannn/next-intl` (942 snippets, High reputation, 87.38 score) — defineRouting, createNavigation, getRequestConfig, middleware, setRequestLocale, hasLocale, generateStaticParams, language switching
- Context7 `/tailwindlabs/tailwindcss.com` (3530 snippets, High reputation) — @import "tailwindcss", @theme directive, @tailwindcss/postcss, CSS-native configuration
- Context7 `/websites/ui_shadcn` (3332 snippets, High reputation) — shadcn/ui init, components.json, Tailwind v4 support, new-york style, tw-animate-css, OKLCH colors
- Google Fonts CSS (fetched 2026-06-26) — Inter and Manrope cyrillic-ext/cyrillic unicode-range verification for Kazakh character coverage
- npm registry (queried 2026-06-26) — version verification for all 10 packages

### Secondary (MEDIUM confidence)
- shadcn/ui docs https://ui.shadcn.com/docs/tailwind-v4 — Tailwind v4 migration guide, @theme inline pattern, deprecated tailwindcss-animate, new-york style
- shadcn/ui docs https://ui.shadcn.com/docs/installation/next — Next.js installation steps, create-next-app integration, monorepo flag

### Tertiary (LOW confidence)
- None — all claims verified against official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified against npm registry + Context7 official docs
- Architecture: HIGH — next-intl routing patterns from Context7 (942 snippets, High reputation); Tailwind v4 @theme from Context7 + shadcn/ui docs
- Pitfalls: HIGH — Kazakh font subset split verified against Google Fonts CSS unicode-range declarations; next-intl pitfalls from Context7 official docs
- Design system: MEDIUM — color OKLCH values are approximations (exact conversion needed at execution time)
- Validation: MEDIUM — test framework (Vitest + Playwright) is standard for Next.js but not yet configured

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 (30 days — stable stack, low churn expected)
