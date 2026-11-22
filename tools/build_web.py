"""Build the standalone web version of Goalquista from the Claude Design page.

The page in Claude Design (project/Football Quiz.dc.html) stays the single source: this script
removes the iPhone mock-up frame, makes the game full-screen, loads React from local files,
and adds what a website needs (installable app manifest, offline cache, share preview,
privacy and credits page). Run it after every change, then publish the repository.
"""
import json, os, re, shutil, sys

# Usage: python3 tools/build_web.py "Football Quiz.dc.html" [questions-extra.json]
# Writes index.html, sw.js, manifest.webmanifest (and questions-extra.json if given) at the repository root.
import datetime
SRC = sys.argv[1]
EXTRA = sys.argv[2] if len(sys.argv) > 2 else None
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
VERSION = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M')
cname = os.path.join(OUT, 'CNAME')
SITE_URL = ('https://' + open(cname).read().strip() + '/') if os.path.exists(cname) else 'https://bernoleonardo-cell.github.io/goalquista/'

s = open(SRC, encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, a[:80])
    s = s.replace(a, b)

# 1. Full-screen game instead of the phone mock-up.
rep('<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;padding:40px 20px;box-sizing:border-box;background:#cdbf9f">',
    '<div class="gq-shell" style="min-height:100dvh;display:flex;justify-content:center;background:#0f2a1f">')
rep('<x-import component-from-global-scope="IOSDevice" from="./ios-frame.jsx" dark="{{ true }}" hint-size="402px,874px">\n', '')
rep('</div>\n</x-import>\n<span style="font:500 12px Rubik,sans-serif;color:#6b5a3e">Goalquista prototype</span>\n</div>\n</x-dc>',
    '</div>\n</div>\n</x-dc>')
rep('<div class="rk-felt" style="position:relative;height:874px;color:#f3ead2;overflow:hidden">',
    '<div class="rk-felt" style="position:relative;height:100dvh;width:100%;max-width:480px;color:#f3ead2;overflow:hidden">')
rep('body{margin:0;background:#cdbf9f;', 'body{margin:0;background:#0f2a1f;overscroll-behavior:none;')

# Fonts served from the site itself (no requests to Google: simpler for privacy).
FONTS = "".join(f"@font-face{{font-family:'Alfa Slab One';font-weight:400;font-display:swap;src:url(fonts/alfa-slab-one-{sub}-400-normal.woff2) format('woff2');{rng}}}" for sub, rng in [('latin', ''), ('latin-ext', 'unicode-range:U+0100-02AF,U+1E00-1EFF;')])
FONTS += "".join(f"@font-face{{font-family:Rubik;font-weight:{w};font-display:swap;src:url(fonts/rubik-{sub}-{w}-normal.woff2) format('woff2');{rng}}}" for w in (400, 500, 600, 700) for sub, rng in [('latin', ''), ('latin-ext', 'unicode-range:U+0100-02AF,U+1E00-1EFF;')])
rep('<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Alfa+Slab+One&amp;family=Rubik:wght@400;500;600;700&amp;display=swap" rel="stylesheet"><style>\n',
    '<style>\n' + FONTS + '\n')
# A link to the privacy and credits page, under the home screen.
rep('<span style="font:500 12px/1.4 Rubik,sans-serif;color:#cfe0cc;opacity:.85">{{ t.updated }}</span>',
    '<span style="font:500 12px/1.4 Rubik,sans-serif;color:#cfe0cc;opacity:.85">{{ t.updated }}</span>\n    <a href="privacy.html" style="font:500 12px/1.4 Rubik,sans-serif;color:#e3b341">Privacy · Credits</a>')

# The daily-challenge share message links to the website, not to the Claude prototype.
rep('\\nhttps://claude.ai/artifact/8xqnt9EnkKj4psw8hquAxF`;', '\\n' + SITE_URL + '`;')

# 2. Head: React from local files (no CDN at start-up), app manifest, share preview.
desc_it = 'Conquista l’Europa una domanda di calcio alla volta: un gioco di strategia e quiz sul calcio europeo, in italiano e in inglese.'
head = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Goalquista</title>
<meta name="description" content="{desc_it}">
<meta name="theme-color" content="#0f2a1f">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta property="og:type" content="website">
<meta property="og:title" content="Goalquista">
<meta property="og:description" content="{desc_it}">
<meta property="og:image" content="{SITE_URL}icons/og.jpg">
<meta property="og:url" content="{SITE_URL}">
<meta name="twitter:card" content="summary_large_image">
<script src="vendor/react.production.min.js"></script>
<script src="vendor/react-dom.production.min.js"></script>
<script src="./support.js"></script>'''
rep('''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Goalquista</title>
<script src="./support.js"></script>''', head)

# 3. Offline cache (service worker) and a link to privacy and credits.
rep('</body>\n</html>', f'''<script>
if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {{}}));
</script>
</body>
</html>''')

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(s)
if EXTRA:
    data = json.load(open(EXTRA, encoding='utf-8'))  # must be valid JSON
    json.dump(data, open(os.path.join(OUT, 'questions-extra.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

json.dump({
    'name': 'Goalquista', 'short_name': 'Goalquista', 'lang': 'it',
    'description': desc_it, 'start_url': './', 'scope': './', 'display': 'standalone', 'orientation': 'portrait',
    'background_color': '#0f2a1f', 'theme_color': '#0f2a1f',
    'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
              {'src': 'icons/icon-512-maskable.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}],
}, open(os.path.join(OUT, 'manifest.webmanifest'), 'w'), indent=1)

files = ['./', 'index.html', 'support.js', 'vendor/react.production.min.js', 'vendor/react-dom.production.min.js',
         'questions-extra.json', 'audio/goal-cheer.mp3', 'audio/crowd-oooh.mp3', 'manifest.webmanifest', 'icons/icon.svg', 'icons/icon-192.png',
         'fonts/alfa-slab-one-latin-400-normal.woff2', 'fonts/rubik-latin-400-normal.woff2', 'fonts/rubik-latin-500-normal.woff2', 'fonts/rubik-latin-600-normal.woff2', 'privacy.html']
open(os.path.join(OUT, 'sw.js'), 'w').write(f'''// Offline cache for Goalquista. A new version name makes phones fetch the new files.
const CACHE = 'goalquista-{VERSION}';
const FILES = {json.dumps(files)};
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
// The game's own files: network first, so updates show at once; the cache when offline.
self.addEventListener('fetch', e => {{
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (u.origin === location.origin) {{
    e.respondWith(fetch(e.request).then(r => {{ const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return r; }}).catch(() => caches.match(e.request, {{ ignoreSearch: true }})));
  }}
}});
''')
assert '<title>Goalquista</title>' in s and 'support.js' in s
print('built', OUT, 'version', VERSION)
