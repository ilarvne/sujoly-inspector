const CACHE_NAME = 'sujoly-v1';
const OFFLINE_CACHE = 'sujoly-offline-v1';

if (self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1') {
  self.addEventListener('install', (event) => {
    event.waitUntil(
      Promise.all([
        caches.keys().then((keys) =>
          Promise.all(keys.map((k) => caches.delete(k)))
        ),
        self.registration.unregister(),
      ]).then(() => self.clients.matchAll()).then((clients) => {
        clients.forEach((c) => c.navigate(c.url));
      })
    );
  });
  self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
  });
  self.addEventListener('fetch', (event) => {
    return;
  });
} else {

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(OFFLINE_CACHE).then(async (cache) => {
      try {
        await cache.addAll(['/ru/offline', '/kk/offline', '/en/offline', '/manifest.json', '/icon.svg']);
      } catch (_e) {
      }
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== OFFLINE_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          const cache = await caches.open(OFFLINE_CACHE);
          const keys = await cache.keys();
          const offlineKey = keys.find((k) => k.url.includes('/offline'));
          if (offlineKey) {
            const offlineResponse = await cache.match(offlineKey);
            if (offlineResponse) return offlineResponse;
          }
          return new Response(
            '<html><body><h1>Offline</h1><p>No cached content available.</p></body></html>',
            { status: 503, headers: { 'Content-Type': 'text/html' } }
          );
        })
    );
    return;
  }

  if (request.destination === 'image' || request.destination === 'style' || request.destination === 'script' || request.destination === 'font') {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached || Response.error());
      })
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
}

}
