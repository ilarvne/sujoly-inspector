import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const nextConfig: NextConfig = {
  output: 'standalone',
  turbopack: {
    root: __dirname,
  },
  async rewrites() {
    const apiTarget = process.env.API_INTERNAL_URL || 'http://localhost:8000';
    const agentTarget = process.env.AGENT_INTERNAL_URL || 'http://localhost:5555';
    return [
      {
        source: '/api/v1/chat/stream',
        destination: `${agentTarget}/api/v1/chat/stream`,
      },
      {
        source: '/api/v1/models',
        destination: `${agentTarget}/api/v1/models`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${apiTarget}/api/v1/:path*`,
      },
    ];
  },
};

const withNextIntl = createNextIntlPlugin();
export default withNextIntl(nextConfig);
