// Offline cache for Goalquista. A new version name makes phones fetch the new files.
const CACHE = 'goalquista-202611231702';
const FILES = ["./", "index.html", "support.js", "vendor/react.production.min.js", "vendor/react-dom.production.min.js", "questions-extra.json", "audio/goal-cheer.mp3", "audio/crowd-oooh.mp3", "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "fonts/alfa-slab-one-latin-400-normal.woff2", "fonts/rubik-latin-400-normal.woff2", "fonts/rubik-latin-500-normal.woff2", "fonts/rubik-latin-600-normal.woff2", "privacy.html"];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
// The game's own files: network first, so updates show at once; the cache when offline.
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (u.origin === location.origin) {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return r; }).catch(() => caches.match(e.request, { ignoreSearch: true })));
  }
});
