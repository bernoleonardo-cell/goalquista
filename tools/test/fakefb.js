// A stand-in for the Firebase compat SDK, for tests: two pages of the same browser share one
// "database" kept in localStorage and hear each other's writes through a BroadcastChannel.
(() => {
  const KEY = 'FAKEFB', bc = new BroadcastChannel('fakefb'), listeners = [];
  // Each page keeps the tree in memory; writes are broadcast whole (localStorage alone syncs too late between pages).
  let TREE = JSON.parse(localStorage.getItem(KEY) || '{}');
  const load = () => JSON.parse(JSON.stringify(TREE));
  const save = t => { TREE = t; localStorage.setItem(KEY, JSON.stringify(t)); };
  const parts = p => String(p || '').split('/').filter(Boolean);
  const get = (t, p) => parts(p).reduce((o, k) => (o && typeof o === 'object' ? o[k] : undefined), t);
  const norm = v => {
    if (v && typeof v === 'object' && v['.sv'] === 'timestamp') return Date.now();
    if (Array.isArray(v)) { const a = v.map(norm); return a.every(x => x === null || x === undefined) ? null : a; }
    if (v && typeof v === 'object') { const o = {}; for (const k in v) { const x = norm(v[k]); if (x !== null && x !== undefined) o[k] = x; } return Object.keys(o).length ? o : null; }
    return v === undefined ? null : v;
  };
  const put = (p, v) => {
    const t = load(), ks = parts(p);
    if (!ks.length) { save(norm(v) || {}); return; }
    let o = t; ks.slice(0, -1).forEach(k => { if (!o[k] || typeof o[k] !== 'object') o[k] = {}; o = o[k]; });
    const x = norm(v); if (x === null) delete o[ks[ks.length - 1]]; else o[ks[ks.length - 1]] = x;
    save(t);
  };
  const fire = () => listeners.forEach(L => { const v = get(load(), L.path), j = JSON.stringify(v ?? null); if (j !== L.last) { L.last = j; L.cb(snap(L.path, v)); } });
  window.__fakefbN = 0; window.__fakefbE = [];
  bc.onmessage = m => { window.__fakefbN++; if (m.data && m.data.tree) TREE = m.data.tree; try { fire(); } catch (e) { window.__fakefbE.push(String(e.stack)); throw e; } };
  const changed = () => { bc.postMessage({ tree: TREE }); setTimeout(fire, 0); };
  const snap = (path, v) => ({ val: () => (v === undefined ? null : JSON.parse(JSON.stringify(v))), exists: () => v !== undefined && v !== null,
    forEach: fn => { Object.keys(v || {}).forEach(k => fn({ key: k, val: () => v[k], ref: ref(path + '/' + k) })); }, key: parts(path).pop() });
  const lag = () => new Promise(r => setTimeout(r, 30));
  const disc = [];
  window.addEventListener('pagehide', () => { disc.forEach(p => put(p, null)); bc.postMessage({ tree: TREE }); });
  function ref(path) {
    return {
      path,
      async set(v) {
        await lag();
        if (/^rooms\/[A-Z]{4}$/.test(path) && v && get(load(), path)) throw new Error('PERMISSION_DENIED');
        put(path, v); changed();
      },
      async update(o) { await lag(); Object.keys(o).forEach(k => put(path + '/' + k, o[k])); changed(); },
      async remove() { await lag(); put(path, null); changed(); },
      async once() { await lag(); return snap(path, get(load(), path)); },
      on(ev, cb) { const L = { path, cb, last: undefined }; listeners.push(L); setTimeout(() => { const v = get(load(), path); L.last = JSON.stringify(v ?? null); cb(snap(path, v)); }, 10); return cb; },
      off(ev, cb) { const i = listeners.findIndex(L => L.path === path && L.cb === cb); if (i >= 0) listeners.splice(i, 1); },
      onDisconnect() { return { remove() { disc.push(path); return Promise.resolve(); }, cancel() { const i = disc.indexOf(path); if (i >= 0) disc.splice(i, 1); return Promise.resolve(); } }; },
      orderByChild() { const me = this; return { endAt(x) { return { once: async () => { const v = get(load(), path) || {}, o = {}; Object.keys(v).forEach(k => { if ((v[k].created || 0) <= x) o[k] = v[k]; }); return snap(path, o); } }; } }; },
    };
  }
  let uid = sessionStorage.getItem('fakeuid'); if (!uid) { uid = 'u' + Math.random().toString(36).slice(2, 9); sessionStorage.setItem('fakeuid', uid); }
  const auth = { currentUser: null, async signInAnonymously() { await lag(); auth.currentUser = { uid }; } };
  const db = { ref };
  const fb = { apps: [], initializeApp() { fb.apps.push({}); }, auth: () => auth, database: () => db };
  fb.database.ServerValue = { TIMESTAMP: { '.sv': 'timestamp' } };
  window.firebase = fb;
  window.__fakefbReset = () => { TREE = {}; localStorage.removeItem(KEY); bc.postMessage({ tree: TREE }); };
  window.__fakefbDump = () => load(); window.__fakefbL = listeners;
})();
