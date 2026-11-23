"""Two simulated phones play an online challenge against each other through the fake Firebase."""
import functools, http.server, json, os, sys, threading, time
from playwright.sync_api import sync_playwright

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/gqt'
SHOTS = '/tmp/mpshots'
FAKE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakefb.js')).read()
os.makedirs(SHOTS, exist_ok=True)

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT))
srv.RequestHandlerClass.log_message = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = 'http://127.0.0.1:8765/'

HELP = """window.__C = () => { const el = document.querySelector('.rk-felt'); if (!el) return null; const k = Object.keys(el).find(k => k.startsWith('__reactFiber')); let f = el[k]; while (f && !(f.stateNode && f.stateNode.logic && f.stateNode.logic.mpVals)) f = f.return; return f && f.stateNode.logic; };
window.__atk = (lvl, free) => { const c = __C(); for (const id of Object.keys(c.state.rk.G.own)) { if (free && c.state.rk.G.own[id] !== null) continue; c.rAttack(id, lvl); if (c.__host) {} } return null; };"""
fails = []
def check(name, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + name + (' ' + str(extra) if extra and not cond else ''))
    if not cond: fails.append(name)

with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 400, 'height': 860}, service_workers='block')
    ctx.route('**/vendor/firebase-app-compat.js', lambda r: r.fulfill(body=FAKE, content_type='text/javascript'))
    ctx.route('**/vendor/firebase-auth-compat.js', lambda r: r.fulfill(body='', content_type='text/javascript'))
    ctx.route('**/vendor/firebase-database-compat.js', lambda r: r.fulfill(body='', content_type='text/javascript'))
    ctx.add_init_script("localStorage.setItem('fr-tutorial-done','1'); localStorage.setItem('fr-tips-done','1'); localStorage.setItem('fr-lang','it');" + HELP)
    errs = []; rerrs = []
    ctx.on('console', lambda m: rerrs.append(m.text) if m.type == 'error' and 'Expected' not in m.text and '404' not in m.text else None)
    A = ctx.new_page(); A.on('pageerror', lambda e: errs.append('A ' + str(e)))
    A.goto(URL); A.evaluate("localStorage.removeItem('FAKEFB')")
    A.wait_for_timeout(800)
    ev = lambda pg, js: pg.evaluate(js)
    st = lambda pg: pg.evaluate("(() => { const c = __C(), rk = c.state.rk; return { screen: c.state.screen, phase: rk && rk.phase, turn: rk && rk.mp && rk.mp.turn, seq: rk && rk.mp && rk.mp.seq, round: rk && rk.G.round, note: rk && rk.note, own: rk && Object.entries(rk.G.own).filter(([k,v]) => v).map(([k,v]) => k + ':' + v).join(' '), myPts: rk && rk.G.myPts, cpuPts: rk && rk.G.cpuPts, missions: rk && rk.G.missions }; })()")

    # Home: the button is there; the menu takes a name typed in the field.
    check('home shows the challenge button', A.get_by_text('Sfida un amico').count() >= 1)
    A.screenshot(path=f'{SHOTS}/01-home.png')
    A.get_by_text('Sfida un amico').first.click(); A.wait_for_timeout(300)
    A.get_by_role('button', name='Crea la sfida').click(); A.wait_for_timeout(300)
    check('empty name is refused', A.get_by_text('Scrivi il tuo nome').count() == 1)
    A.locator('input').first.fill('Leo')
    A.screenshot(path=f'{SHOTS}/02-menu.png')
    A.get_by_role('button', name='Crea la sfida').click(); A.wait_for_timeout(900)
    code = ev(A, "__C().state.mpM && __C().state.mpM.code")
    check('lobby shows a 4-letter code', bool(code) and len(code) == 4, code)
    A.screenshot(path=f'{SHOTS}/03-lobby.png')

    B = ctx.new_page(); B.on('pageerror', lambda e: errs.append('B ' + str(e)))
    B.goto(URL + '?sfida=WXYZ'); B.wait_for_timeout(800)
    check('link opens the join screen with the code', ev(B, "__C().state.mpM.code") == 'WXYZ')
    B.locator('input').first.fill('Marco')
    B.get_by_role('button', name='Entra').click(); B.wait_for_timeout(600)
    check('wrong code is reported', B.get_by_text('Nessuna sfida con questo codice').count() == 1)
    B.locator('input').nth(1).fill(code.lower())
    B.get_by_role('button', name='Entra').click(); B.wait_for_timeout(1500)
    sa, sb = st(A), st(B)
    check('both phones are in the game', sa['screen'] == 'risk' and sb['screen'] == 'risk', (sa, sb))
    check('both start on the mission cards', sa['phase'] == 'mission' and sb['phase'] == 'mission')
    check('scoreboard shows the friend\'s name', 'Marco 0' in A.inner_text('body') and 'Leo 0' in B.inner_text('body'), A.inner_text('body')[:300])
    offers = ev(A, "__C().state.rk.mOffer.concat(['|'], [])"), ev(B, "__C().state.rk.mOffer")
    check('mission offers do not overlap', not set(offers[0]) & set(offers[1]), offers)

    for pg in (A, B): ev(pg, "__C().rPickMission(0)"); pg.wait_for_timeout(100); ev(pg, "__C().rMissionOk()")
    A.wait_for_timeout(400)
    check('host picks a base first', st(A)['phase'] == 'setup' and st(B)['phase'] == 'wait', (st(A)['phase'], st(B)['phase']))
    B.screenshot(path=f'{SHOTS}/04-guest-waits.png')

    # Host kicks off in Spain with a level 2 question, answered right; the guest watches it live.
    ev(A, "__C().rStartAt('ESP', 2)"); A.wait_for_timeout(1500)
    check('guest sees the host\'s kick-off question live', ev(B, "__C().mpVals().hasQ") is True)
    B.screenshot(path=f'{SHOTS}/05-guest-watches.png')
    ev(A, "__C().rPick(__C().state.rk.q.a)"); A.wait_for_timeout(700)
    check('guest sees the host\'s answer', ev(B, "__C().state.rk.mpLive && __C().state.rk.mpLive.p") >= 0)
    B.screenshot(path=f'{SHOTS}/06-guest-sees-answer.png')
    ev(A, "__C().rContinue()"); A.wait_for_timeout(700)
    sa, sb = st(A), st(B)
    check('after the host\'s base the guest picks', sa['phase'] == 'wait' and sb['phase'] == 'setup', (sa, sb))
    check('guest board shows the host in Spain', 'ESP:cpu' in sb['own'], sb['own'])
    ev(B, "__C().rStartAt('FRA', 2)"); B.wait_for_timeout(200)
    check('guest cannot start next to the host', st(B)['phase'] == 'setup' and 'Troppo vicino' in (st(B)['note'] or ''))
    ev(B, "__C().rStartAt('TUR', 3)"); B.wait_for_timeout(300)
    ev(B, "__C().rPick(__C().state.rk.q.a)"); B.wait_for_timeout(300); ev(B, "__C().rContinue()"); B.wait_for_timeout(800)
    sa, sb = st(A), st(B)
    check('the host plays first', sa['phase'] == 'map' and sb['phase'] == 'wait', (sa, sb))
    check('both boards agree', sorted(sa['own'].replace('me', 'X').replace('cpu', 'Y').split()) == sorted(sb['own'].replace('cpu', 'X').replace('me', 'Y').split()), (sa['own'], sb['own']))
    check('missions are known to both', sa['missions']['cpu'] == sb['missions']['me'] and sb['missions']['cpu'] == sa['missions']['me'], (sa['missions'], sb['missions']))
    A.screenshot(path=f'{SHOTS}/07-host-map.png')

    # Host attacks a free neighbour, right answer.
    tgt = ev(A, "__C().riskVals().targetChips.length ? null : null")
    tgt = ev(A, "(() => { const c = __C(), G = c.state.rk.G; return Object.keys(G.own).find(id => G.own[id] === null && c.riskVals().targetChips.some(t => t.label === (c.lang() === 'it' ? id : id))); })()")
    tgt = ev(A, "(() => { const c = __C(), G = c.state.rk.G; for (const id of Object.keys(G.own)) { if (G.own[id] !== null) continue; c.rAttack(id, 1); if (c.state.rk.phase === 'ask' || c.__pending) return id; } return null; })()")
    A.wait_for_timeout(1200)
    B.screenshot(path=f'{SHOTS}/08-guest-watches-attack.png')
    ev(A, "__C().rPick(__C().state.rk.q.a)"); A.wait_for_timeout(300); ev(A, "__C().rContinue()"); A.wait_for_timeout(800)
    sb = st(B)
    check('guest sees the host\'s move', sb['phase'] == 'cpu' and f'{tgt}:cpu' in sb['own'], sb)
    B.screenshot(path=f'{SHOTS}/09-guest-rival-move.png')
    ev(B, "__C().rCpuGo()"); B.wait_for_timeout(200)
    check('then it is the guest\'s turn', st(B)['phase'] == 'map')

    # Guest attacks and misses: the round ends on the guest's side.
    tgt2 = ev(B, "(() => { const c = __C(), G = c.state.rk.G; for (const id of Object.keys(G.own)) { if (G.own[id] !== null) continue; c.rAttack(id, 2); if (c.state.rk.phase === 'ask') return id; } return null; })()")
    B.wait_for_timeout(300)
    ev(B, "__C().rPick((__C().state.rk.q.a + 1) % 4)"); B.wait_for_timeout(300); ev(B, "__C().rContinue()"); B.wait_for_timeout(800)
    sa = st(A)
    check('round 2 starts after the guest\'s turn', sa['round'] == 2 and st(B)['round'] == 2, (sa['round'], st(B)['round']))
    check('host sees the guest\'s miss', sa['phase'] == 'cpu')
    ev(A, "__C().rCpuGo()"); A.wait_for_timeout(200)

    # A shot: the host gets (locally) a territory next to Turkey and attacks Turkey; the guest must save.
    ev(A, "(() => { const c = __C(), rk = c.state.rk, n = ['GRE', 'BAL', 'REU'].find(x => rk.G.own[x] === null); c.setState({ rk: { ...rk, G: { ...rk.G, own: { ...rk.G.own, [n]: 'me' }, troops: { ...rk.G.troops, [n]: 2 } } } }); })()")
    A.wait_for_timeout(200)
    pts_before = st(A)['myPts']
    ev(A, "__C().rAttack('TUR', 2)"); A.wait_for_timeout(300)
    ev(A, "__C().rPick(__C().state.rk.q.a)"); A.wait_for_timeout(300)
    check('a right answer on the rival is a shot', ev(A, "__C().state.rk.out.kind") == 'shot')
    A.screenshot(path=f'{SHOTS}/10-host-shot.png')
    ev(A, "__C().rContinue()"); A.wait_for_timeout(900)
    sb = st(B)
    check('guest must save', sb['phase'] == 'ask' and ev(B, "!!__C().state.rk.defend"), sb)
    check('board unchanged before the save', 'TUR:me' in sb['own'])
    B.screenshot(path=f'{SHOTS}/11-guest-save.png')
    ev(B, "__C().rPick((__C().state.rk.q.a + 1) % 4)"); B.wait_for_timeout(300); ev(B, "__C().rContinue()"); B.wait_for_timeout(900)
    sa, sb = st(A), st(B)
    check('missed save costs the guest tanks', ev(B, "__C().state.rk.G.troops.TUR") == 1, ev(B, "__C().state.rk.G.troops.TUR"))
    check('host is told how the save went', 'non para' in (ev(A, "__C().state.rk.mpNote") or ''), ev(A, "__C().state.rk.mpNote"))
    check('after the save the guest plays', sb['phase'] == 'map' and sa['phase'] == 'wait', (sa['phase'], sb['phase']))
    A.screenshot(path=f'{SHOTS}/12-host-note.png')
    check('host troops on Turkey agree', ev(A, "__C().state.rk.G.troops.TUR") == 1)

    # Guest passes (no attack) — the host is told.
    ev(B, "__C().rSkip()"); B.wait_for_timeout(800)
    check('host sees that the guest did not attack', st(A)['phase'] == 'cpu' and 'non ha attaccato' in A.inner_text('body'))
    ev(A, "__C().rCpuGo()"); A.wait_for_timeout(200)

    # The guest reloads the page and re-enters the code: the game picks up.
    B.reload(); B.wait_for_timeout(900)
    ev(B, "__C().mpOpen()"); B.wait_for_timeout(200)
    B.locator('input').nth(1).fill(code); B.get_by_role('button', name='Entra').click(); B.wait_for_timeout(1500)
    sb = st(B)
    check('guest rejoins in the waiting phase', sb['screen'] == 'risk' and sb['phase'] == 'wait' and sb['round'] == 3, sb)

    # Host leaves by mistake? First tap warns, second tap leaves: the guest wins.
    ev(A, "__C().mpLeave()"); A.wait_for_timeout(200)
    check('first tap only warns', st(A)['screen'] == 'risk')
    ev(A, "__C().mpLeave()"); A.wait_for_timeout(1000)
    sb = st(B)
    check('guest wins when the host leaves', sb['phase'] == 'over' and ev(B, "__C().state.rk.mpWin") == 'me', sb)
    B.screenshot(path=f'{SHOTS}/13-guest-wins.png')

    # A second game: the guest disconnects and does not come back.
    ev(A, "__C().mpOpen()"); A.wait_for_timeout(200)
    A.get_by_role('button', name='Crea la sfida').click(); A.wait_for_timeout(900)
    code2 = ev(A, "__C().state.mpM.code")
    C = ctx.new_page(); C.on('pageerror', lambda e: errs.append('C ' + str(e)))
    C.goto(URL + '?sfida=' + code2); C.wait_for_timeout(800)
    C.locator('input').first.fill('Gio'); C.get_by_role('button', name='Entra').click(); C.wait_for_timeout(1500)
    check('second game starts', st(A)['screen'] == 'risk' and st(C)['screen'] == 'risk')
    A.wait_for_timeout(800)
    C.close(run_before_unload=True); A.wait_for_timeout(1200)
    check('host sees the disconnection', ev(A, "!!__C().mpGoneAt"))
    A.screenshot(path=f'{SHOTS}/14-gone.png')
    ev(A, "__C().mpGoneAt = Date.now() - 59500"); A.wait_for_timeout(1800)
    check('host wins by forfeit after the grace time', st(A)['phase'] == 'over' and ev(A, "__C().state.rk.mpWin") == 'me')
    A.screenshot(path=f'{SHOTS}/15-forfeit.png')
    A.wait_for_timeout(500)
    check('no page errors', not errs, errs)
    check('no render errors', not rerrs, rerrs[:3])
    br.close()
srv.shutdown()
print('FAILS:', fails)
