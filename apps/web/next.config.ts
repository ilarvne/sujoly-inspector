import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
};

const withNextIntl = createNextIntlPlugin();
export default withNextIntl(nextConfig);
