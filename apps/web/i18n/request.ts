import { getRequestConfig } from 'next-intl/server';

// Minimal placeholder — locale routing and message loading
// will be implemented in subsequent waves of Phase 1.
export default getRequestConfig(async () => {
  return {
    locale: 'en',
    messages: {}
  };
});
