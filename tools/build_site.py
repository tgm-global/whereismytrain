#!/usr/bin/env python3
"""Generate the complete, SEO-ready static site from assets/data/*.json (stdlib only).

  python3 tools/build_site.py

Writes (all with title, meta description, keywords, canonical, Open Graph, Twitter card, JSON-LD):
  * main pages (index + tools + info pages)       - copy lives in tools/site_content.py
  * train/<no>-<name>.html          one page per train   (timetable, route, running days, FAQ)
  * station/<name>-<code>.html      one page per station (all trains, first/last, busiest hour, FAQ)
  * route/<a>-to-<b>.html           popular direct-train routes
  * hub pages: all-trains, all-stations, popular-routes (+ A-Z / number sub-pages), sitemap.html
  * sitemap.xml (index) + sitemaps/*.xml, robots.txt, llms.txt, 404.html, sw.js
Settings: tools/site.json (site URL, verification codes, limits).
Run it again after every timetable data refresh (tools/update_from_zip.py does that for you)."""
import collections, datetime, glob, html, json, os, re, shutil, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import site_content as C

CFG = json.load(open(os.path.join(HERE, 'site.json')))
SITE = CFG['site_url'].rstrip('/')
BASEPATH = urlparse(SITE).path.rstrip('/')          # '/whereismytrain' (or '' on a custom domain)
BRAND = CFG['brand']
TODAY = datetime.date.today()
DATA = os.path.join(ROOT, 'assets', 'data')
GEN_DIRS = ['train', 'station', 'route', 'trains-by-number', 'stations-a-z', 'routes-a-z', 'sitemaps']

esc = lambda s: html.escape(str(s), quote=True)

# ----------------------------------------------------------------------------------------------- data
meta = json.load(open(os.path.join(DATA, 'meta.json'), encoding='utf-8'))
S = meta['s']
V = meta.get('v', {})
m = re.match(r'(\d{4})-(\d{2})-(\d{2})', V.get('feed', '') or '')
FEED_DATE = datetime.date(int(m[1]), int(m[2]), int(m[3])) if m else TODAY
FEED_ISO = FEED_DATE.isoformat()
FEED_TXT = FEED_DATE.strftime('%d %b %Y').lstrip('0')

CARGO = re.compile(r'cargo|parcel', re.I)           # freight-type entries get no public page
ALL = {t[0]: t for t in meta['t']}
TR = {}
for f in glob.glob(os.path.join(DATA, 'tr', '*.json')):
    TR.update(json.load(open(f, encoding='utf-8')))
ST = {}
for f in glob.glob(os.path.join(DATA, 'st', '*.json')):
    ST.update(json.load(open(f, encoding='utf-8')))

PUB = {no: t for no, t in ALL.items() if not CARGO.search(t[1]) and no in TR}
NT = '{:,}'.format(len(PUB) // 500 * 500)
NS = '{:,}'.format(len(S) // 500 * 500)

TYPES = {'Raj': 'Rajdhani', 'Shtb': 'Shatabdi', 'SF': 'Superfast', 'Exp': 'Express', 'Mail': 'Mail', 'Pass': 'Passenger', 'Drnt': 'Duronto',
         'Garib': 'Garib Rath', 'Jan': 'Jan Shatabdi', 'Humsafar': 'Humsafar', 'Rajya': 'Rajya Rani', 'VB': 'Vande Bharat', 'AB': 'Amrit Bharat',
         'Tejas': 'Tejas', 'MEMU': 'MEMU', 'DEMU': 'DEMU', 'EMU': 'EMU', 'Local': 'Local', 'Spl': 'Special'}
DN = 'MTWTFSS'
DF = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def fill(s):
    return (s.replace('{NTES}', C.ext(C.NTES, 'NTES')).replace('{NT}', NT).replace('{NS}', NS).replace('{FEED}', FEED_TXT))

def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')[:60]
    return s.strip('-')

def mm(x):
    return '--' if x is None else '%02d:%02d' % (x // 60 % 24, x % 60)

def dur(x):
    return '%dh %dm' % (x // 60, x % 60) if x >= 60 else '%d min' % x

def sname(c):
    n = S.get(c, c)
    return re.sub(r'\bJn\b', 'Junction', n)

def tname(t):
    w = t[1].split(' ')
    if len(w) >= 2 and re.fullmatch(r'[A-Z]{2,5}', w[0]) and w[0] in S:
        w[0] = sname(w[0])
    if len(w) >= 2 and w[-1] == 'Raj':
        w[-1] = 'Rajdhani'
    return ' '.join(w)

def tytxt(t):
    return TYPES.get(t[2], t[2])

def days_text(b):
    b = b or '1111111'
    if b == '1111111':
        return 'daily'
    on = [DF[i] for i in range(7) if b[i] == '1']
    return 'on ' + ', '.join(on) if on else 'on selected days'

def rot(b, k):
    k %= 7
    return ''.join(b[(j - k) % 7] for j in range(7))

def dshort(b):
    b = b or '1111111'
    if b == '1111111':
        return 'Daily'
    on = [i for i in range(7) if b[i] == '1']
    if not on:
        return '–'
    if on == list(range(on[0], on[-1] + 1)) and len(on) > 2:
        return '%s–%s' % (DF[on[0]], DF[on[-1]])
    return ' '.join(DF[i] for i in on)

def dys(b):
    b = b or '1111111'
    title = 'Daily' if b == '1111111' else ', '.join(DF[i] for i in range(7) if b[i] == '1')
    return '<span class="dys" title="%s">%s</span>' % (title, ''.join('<i class="%s">%s</i>' % ('on' if b[i] == '1' else '', DN[i]) for i in range(7)))

def until_txt(t):
    u = t[10]
    return '%d %s %s' % (int(u[6:]), MON[int(u[4:6]) - 1], u[:4]) if u else ''

def train_url(no):
    return 'train/%s-%s.html' % (no, slug(ALL[no][1]))

def station_url(c):
    return 'station/%s-%s.html' % (slug(S.get(c, c)), c.lower())

def route_url(a, b):
    return 'route/%s-%s-to-%s-%s.html' % (slug(S.get(a, a)), a.lower(), slug(S.get(b, b)), b.lower())

# --------------------------------------------------------------------------- station / route indexes
SROWS = {}                                           # station -> rows of public trains
for c, rows in ST.items():
    r = [x for x in rows if x[0] in PUB]
    if r:
        SROWS[c] = r
STATION_PAGES = {c for c, r in SROWS.items() if len(r) >= CFG['min_station_trains']}

def build_routes():
    hubs = {c for c, r in SROWS.items() if len(r) >= CFG['route_hub_min_trains']}
    bytrain = collections.defaultdict(list)
    for c in hubs:
        for no, idx, arr, dep, n in SROWS[c]:
            bytrain[no].append((idx, c, arr, dep))
    pairs = collections.defaultdict(list)
    for no, lst in bytrain.items():
        lst.sort()
        for i in range(len(lst)):
            a = lst[i]
            da = a[3] if a[3] is not None else a[2]
            if da is None:
                continue
            for j in range(i + 1, len(lst)):
                b = lst[j]
                ab = b[2] if b[2] is not None else b[3]
                if ab is None or ab <= da:
                    continue
                pairs[(a[1], b[1])].append((no, da, ab))
    cand = sorted(((k, v) for k, v in pairs.items() if len(v) >= CFG['min_route_trains']), key=lambda kv: (-len(kv[1]), kv[0]))
    per, out = collections.Counter(), {}
    for (a, b), v in cand:
        if len(out) >= CFG['max_routes']:
            break
        if per[a] >= 25 or a not in STATION_PAGES or b not in STATION_PAGES:
            continue
        per[a] += 1
        out[(a, b)] = v
    return out

ROUTES = build_routes()
ROUTES_FROM = collections.defaultdict(list)
for (a, b), v in ROUTES.items():
    ROUTES_FROM[a].append((b, len(v)))
BY_OD = collections.defaultdict(list)
for no, t in PUB.items():
    BY_OD[(t[3], t[4])].append(no)

# ------------------------------------------------------------------------------------------ writers
written = []                                          # (path, kind, lastmod)

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or '.', exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)

def ld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

def crumb_ld(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + '/' + p} for i, (n, p) in enumerate(items)]}

def faq_ld(faq):
    return {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', a)}} for q, a in faq]}

NAV = [('index.html', 'Home'), ('live-train-status.html', 'Live Status'), ('pnr-status.html', 'PNR'), ('trains-between-stations.html', 'Trains'),
       ('station-live-status.html', 'Station'), ('seat-availability.html', 'Seats'), ('download-app.html', 'App')]
FOOT = [('about.html', 'About'), ('features.html', 'Features'), ('all-trains.html', 'All Trains'), ('all-stations.html', 'All Stations'), ('faq.html', 'FAQ'),
        ('contact.html', 'Contact'), ('privacy-policy.html', 'Privacy'), ('terms.html', 'Terms'), ('disclaimer.html', 'Disclaimer'), ('sitemap.html', 'Sitemap')]

def page(path, title, desc, kw, body, *, schema=None, data_page='', og_type='website', noindex=False, kind='main', lastmod=None, nav_on=None, base=None):
    depth = path.count('/')
    rel = '../' * depth
    canon = SITE + '/' + ('' if path == 'index.html' else path)
    robots = 'noindex,nofollow' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1'
    img = SITE + '/assets/img/og-image.png'
    nav = ''.join('<a href="%s%s" class="%s">%s</a>' % (rel, h, 'on' if h == (nav_on or path) else '', n) for h, n in NAV)
    foot = ''.join('<a href="%s%s">%s</a>' % (rel, h, n) for h, n in FOOT)
    ver = ''
    if CFG.get('google_site_verification'):
        ver += '<meta name="google-site-verification" content="%s">' % esc(CFG['google_site_verification'])
    if CFG.get('bing_site_verification'):
        ver += '<meta name="msvalidate.01" content="%s">' % esc(CFG['bing_site_verification'])
    graph = {'@context': 'https://schema.org', '@graph': schema or []}
    out = ('<!doctype html>\n<html lang="en" data-base="%s">\n<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' % (base if base is not None else rel) +
           ('<base href="%s/">\n' % BASEPATH if base is not None else '') +
           '<title>%s</title>\n<meta name="description" content="%s">\n<meta name="keywords" content="%s">\n<meta name="robots" content="%s">\n' % (esc(title), esc(desc), esc(kw), robots) +
           '<link rel="canonical" href="%s"><meta name="theme-color" content="#0f62fe"><meta name="author" content="%s">%s\n' % (canon, esc(CFG['owner']), ver) +
           '<meta property="og:type" content="%s"><meta property="og:site_name" content="%s"><meta property="og:locale" content="en_IN"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:image" content="%s"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n' % (og_type, esc(BRAND), esc(title), esc(desc), canon, img) +
           '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="%s">\n' % img +
           '<link rel="manifest" href="%smanifest.webmanifest"><link rel="icon" href="%sassets/img/logo.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="%sassets/img/icon-192.png">\n' % (rel, rel, rel) +
           '<link rel="stylesheet" href="%sassets/css/style.css">%s</head>\n' % (rel, ld(graph) if schema else '') +
           '<body data-page="%s">\n<header class="site-header"><div class="wrap"><a class="brand notranslate" href="%sindex.html"><img src="%sassets/img/logo.svg" alt="" width="34" height="34">WhereIsMyTrain</a>\n' % (data_page, rel, rel) +
           '<button class="menu-btn" id="menuBtn" aria-label="Menu">☰</button>\n<nav class="nav" id="mainNav" aria-label="Main">%s<select class="lang notranslate" id="langSel" aria-label="Language"></select></nav></div></header>\n<div id="gt_el"></div>\n' % nav +
           '<main>%s</main>\n<button class="to-en notranslate" id="toEn" type="button">🌐 View in English</button>\n' % body +
           '<footer class="site-footer"><div class="wrap"><nav class="links" aria-label="Footer">%s</nav><span class="copy">© %d %s</span></div></footer>\n' % (foot, TODAY.year, esc(CFG['owner'])) +
           '<script src="%sassets/js/config.js"></script><script src="%sassets/js/app.js"></script></body></html>' % (rel, rel))
    write(path, out)
    if not noindex and kind:
        written.append((path, kind, lastmod or TODAY.isoformat()))

def crumbs(rel, trail):
    parts = ['<a href="%sindex.html">Home</a>' % rel]
    for n, p in trail[:-1]:
        parts.append('<a href="%s%s">%s</a>' % (rel, p, esc(n)))
    parts.append(esc(trail[-1][0]))
    return '<div class="crumbs">%s</div>' % ' › '.join(parts)

def faq_html(faq):
    return '<div class="card"><h2 style="margin-top:0">Frequently asked questions</h2>%s</div>' % ''.join(
        '<details><summary>%s</summary><p>%s</p></details>' % (esc(q), a) for q, a in faq)

def related_tools(rel, exclude=''):
    names = {f['file']: f['name'] for f in C.TOOLS}
    items = [(f, names[f]) for f in C.TOOL_ORDER if f != exclude]
    items += [('index.html', 'Home'), ('all-trains.html', 'All Trains'), ('all-stations.html', 'All Stations'), ('popular-routes.html', 'Popular Routes'), ('faq.html', 'FAQ')]
    return '<div class="card"><h3 style="margin-top:0">Related tools</h3><div class="related">%s</div></div>' % ''.join(
        '<a href="%s%s">%s</a>' % (rel, f, n) for f, n in items if f != exclude)

def pills(items):
    return '<div class="related">%s</div>' % ''.join('<a href="%s">%s</a>' % (h, esc(t)) for h, t in items)

def short(s, n=34):
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'

def trim_title(s, n=65):
    return s if len(s) <= n else s[:n - 1].rsplit(' ', 1)[0].rstrip(' &,-–:')

def pick(*cands, n=65):
    for c in cands:
        if len(c) <= n:
            return c
    return trim_title(cands[-1], n)

def trim_desc(s, n=158):
    if len(s) <= n:
        return s
    return s[:n - 1].rsplit(' ', 1)[0].rstrip(',;:-') + '…'

NOTE = ('<p class="note">Timetable: Indian Railways community GTFS feed (unofficial), version %s. Timings, halts and running days can change at short notice, '
        'so confirm with <a href="%s" target="_blank" rel="noopener">NTES</a> before travel. Live running status, PNR and seat data are not part of this feed.</p>' % (FEED_TXT, C.NTES))

# ---------------------------------------------------------------------------------- popular lists
def popular_trains():
    out, seen = [], set()
    for ty in ['Raj', 'VB', 'Shtb', 'Drnt', 'Garib', 'Tejas', 'AB', 'Humsafar']:
        c = 0
        for no in sorted(PUB):
            t = PUB[no]
            if t[2] == ty and t[9] == '1111111' and not t[10]:
                out.append(no); c += 1
                if c >= 4:
                    break
    return out

POP_TRAINS = popular_trains()
POP_STATIONS = sorted(STATION_PAGES, key=lambda c: (-len(SROWS[c]), c))[:30]
POP_ROUTES = [k for k, v in sorted(ROUTES.items(), key=lambda kv: (-len(kv[1]), kv[0]))][:24]

def train_pills(rel, nos):
    return pills([(rel + train_url(n), '%s %s' % (n, short(tname(PUB[n])))) for n in nos])

def station_pills(rel, cs):
    return pills([(rel + station_url(c), '%s (%s)' % (short(sname(c), 26), c)) for c in cs])

def route_pills(rel, rs):
    return pills([(rel + route_url(a, b), '%s → %s' % (short(sname(a), 22), short(sname(b), 22))) for a, b in rs])

# =========================================================================================== main pages
ORG = {'@type': 'Organization', '@id': SITE + '/#org', 'name': CFG['owner'], 'url': SITE + '/', 'logo': SITE + '/assets/img/icon-512.png'}
WEBSITE = {'@type': 'WebSite', '@id': SITE + '/#website', 'name': BRAND, 'url': SITE + '/', 'inLanguage': 'en', 'publisher': {'@id': SITE + '/#org'},
           'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': SITE + '/live-train-status.html?train={search_term_string}'}, 'query-input': 'required name=search_term_string'}}

def build_home():
    H = C.HOME
    faq = [(fill(q), fill(a)) for q, a in H['faq']]
    tiles = ''.join('<a class="tile" href="%s"><div class="ic">%s</div><h3>%s</h3><p>%s</p></a>' % (f, *[fill(x) for x in C.TILES[f]]) for f in C.TOOL_ORDER)
    body = ('<section class="hero"><div class="wrap"><h1>%s</h1><p>%s</p><div class="cta"><a class="btn alt" href="live-train-status.html">Track a train</a><a class="btn alt" href="trains-between-stations.html">Trains between stations</a><a class="btn alt" href="download-app.html">Install app</a></div></div></section>\n' % (esc(fill(H['h1'])), esc(fill(H['lead']))) +
            '<div class="wrap pull"><div class="card"><form class="f" action="live-train-status.html" method="get"><div><label for="q">Train number or name</label><input id="q" name="train" data-suggest="train" placeholder="e.g. 12951 or Rajdhani" required></div><div><button class="btn" type="submit">Check train status</button></div></form></div>\n' +
            '<h2>All tools</h2><div class="grid">%s</div>\n' % tiles +
            '<h2>Popular trains</h2>%s<p><a href="all-trains.html">Browse the complete list of %s+ trains →</a></p>\n' % (train_pills('', POP_TRAINS), NT) +
            '<h2>Popular train routes</h2>%s<p><a href="popular-routes.html">See all popular routes →</a></p>\n' % route_pills('', POP_ROUTES) +
            '<h2>Busiest railway stations</h2>%s<p><a href="all-stations.html">Browse all stations →</a></p>\n' % station_pills('', POP_STATIONS[:18]) +
            '<h2>How to check train running status online</h2><div class="card"><ol><li>Enter the train number or name in the search box.</li><li>Open the result to see the route, halts, scheduled times and running days.</li><li>On the day of travel, tap the official NTES link for the live position and delay.</li><li>Use <a href="trains-between-stations.html">trains between stations</a>, <a href="seat-availability.html">seat availability</a> and <a href="pnr-status.html">PNR status</a> to plan the rest of your journey.</li></ol></div>\n' +
            '<h2>Why use Where Is My Train?</h2><div class="grid">'
            '<div class="card"><h3 style="margin-top:0">⚡ Fast</h3><p>Lightweight pages that load quickly even on slow mobile networks.</p></div>'
            '<div class="card"><h3 style="margin-top:0">🌐 Your language</h3><p>Content adapts to your device language. One tap switches back to English.</p></div>'
            '<div class="card"><h3 style="margin-top:0">📲 Works like an app</h3><p>Install it to your home screen and open it any time. <a href="download-app.html">Learn how</a>.</p></div>'
            '<div class="card"><h3 style="margin-top:0">🔒 Private</h3><p>No sign-up. We do not store your searches. See our <a href="privacy-policy.html">privacy policy</a>.</p></div></div>\n' +
            faq_html(faq) +
            '<div class="card"><p class="muted" style="margin:0">Where Is My Train is an independent project and is not affiliated with Indian Railways, IRCTC or any ticketing company. Timetable data: community GTFS feed, version %s.</p></div></div>' % FEED_TXT)
    schema = [ORG, WEBSITE,
              {'@type': 'WebApplication', 'name': BRAND, 'url': SITE + '/', 'applicationCategory': 'TravelApplication', 'operatingSystem': 'Any', 'browserRequirements': 'Requires JavaScript',
               'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'INR'}, 'publisher': {'@id': SITE + '/#org'}},
              faq_ld(faq)]
    page('index.html', fill(H['title']), trim_desc(fill(H['desc'])), fill(H['kw']), body, schema=schema, data_page='home', nav_on='index.html')

def build_tool(f):
    rel = ''
    name = f['name']
    faq = [(fill(q), fill(a)) for q, a in f['faq']]
    parts = [crumbs(rel, [(name, f['file'])]), '<h1 class="page-title">%s</h1>' % esc(fill(f['h1']))]
    if f['lead']:
        parts.append('<p class="lead">%s</p>' % esc(fill(f['lead'])))
    if f['form']:
        parts.append(fill(f['form']) if f['form'].startswith('<div class="card"') else '<div class="card">%s</div>' % fill(f['form']))
    if f['data_page'] in ('live', 'between', 'station', 'schedule'):
        parts.append('<div id="out" class="res" aria-live="polite"></div>')
    for h, b in f['sections']:
        parts.append('<div class="card"><h2 style="margin-top:0">%s</h2>%s</div>' % (esc(h), fill(b)))
    ex = f.get('extra')
    if ex == 'tiles':
        parts.append('<div class="grid">%s</div><div class="card"><h2 style="margin-top:0">Built-in extras</h2><ul class="clean"><li><b>Page for every train:</b> time table, route, halts and running days for %s+ trains.</li><li><b>Page for every station:</b> all trains that stop there with first and last service.</li><li><b>Auto language:</b> pages open in your device language; the orange button returns to English.</li><li><b>Installable:</b> works as an app on phone and laptop.</li><li><b>Private:</b> no login and no stored searches.</li></ul></div>' % (
            ''.join('<a class="tile" href="%s"><div class="ic">%s</div><h3>%s</h3><p>%s</p></a>' % (k, *[fill(x) for x in C.TILES[k]]) for k in C.TOOL_ORDER), NT))
    elif ex == 'trains':
        parts.append('<div class="card"><h2 style="margin-top:0">Popular trains</h2>%s<p><a href="all-trains.html">Complete train list →</a></p></div>' % train_pills(rel, POP_TRAINS[:16]))
    elif ex == 'routes':
        parts.append('<div class="card"><h2 style="margin-top:0">Popular routes</h2>%s<p><a href="popular-routes.html">All popular routes →</a></p></div>' % route_pills(rel, POP_ROUTES))
    elif ex == 'stations':
        parts.append('<div class="card"><h2 style="margin-top:0">Popular stations</h2>%s<p><a href="all-stations.html">All stations →</a></p></div>' % station_pills(rel, POP_STATIONS[:20]))
    if f.get('legal'):
        parts.insert(2, '<p class="muted">Last updated: %s</p>' % TODAY.strftime('%d %B %Y').lstrip('0'))
    if faq:
        parts.append(faq_html(faq))
    parts.append(related_tools(rel, f['file']))
    body = '<div class="wrap">%s</div>' % ''.join(parts)
    schema = [ORG, {'@type': f['schema'] if f['schema'] != 'FAQPage' else 'WebPage', '@id': SITE + '/' + f['file'] + '#page', 'url': SITE + '/' + f['file'], 'name': fill(f['title']),
                    'description': fill(f['desc']), 'inLanguage': 'en', 'isPartOf': {'@id': SITE + '/#website'}, 'dateModified': TODAY.isoformat()},
              crumb_ld([('Home', ''), (name, f['file'])])]
    if faq:
        schema.append(faq_ld(faq))
    page(f['file'], fill(f['title']), trim_desc(fill(f['desc'])), fill(f['kw']), body, schema=schema, data_page=f['data_page'], kind='main', nav_on=f['file'])

# ====================================================================================== train pages
NUMS = sorted(PUB)

def build_trains():
    idx = {n: i for i, n in enumerate(NUMS)}
    for no in NUMS:
        t = PUB[no]
        stops = TR[no]
        rel = '../'
        A, B = t[3], t[4]
        nm = tname(t)
        n = len(stops)
        first_dep = stops[0][2]
        last = stops[-1]
        arr_abs = (last[3] - 1) * 1440 + last[1] if last[1] is not None else None
        total = arr_abs - first_dep if arr_abs is not None and first_dep is not None else None
        dtxt = dur(total) if total and total > 0 else ''
        extra_days = (last[3] - 1)
        path = train_url(no)
        title = pick('%s %s Time Table, Route & Running Days' % (no, nm), '%s %s Time Table & Running Days' % (no, nm), '%s %s Time Table' % (no, nm))
        desc = trim_desc('%s %s runs from %s to %s (%s km%s) with %d stops %s. Check time table, route, stoppages, running days and live status link.' % (
            no, nm, sname(A), sname(B), t[7], ', ' + dtxt if dtxt else '', n, days_text(t[9])))
        kw = ', '.join([no, '%s train' % no, '%s %s' % (no, nm), '%s time table' % no, '%s running status' % no, '%s live status' % no, '%s train route' % no, '%s stoppages' % no, '%s running days' % no,
                        '%s schedule' % nm, '%s train time table' % nm, 'trains from %s to %s' % (sname(A), sname(B)), '%s to %s train' % (sname(A), sname(B)), '%s %s' % (tytxt(t), 'train')])
        rows = []
        for i, s in enumerate(stops):
            code = s[0]
            lab = esc(sname(code))
            if code in STATION_PAGES:
                lab = '<a href="%s%s">%s</a>' % (rel, station_url(code), lab)
            halt = ''
            if s[1] is not None and s[2] is not None:
                h = (s[2] - s[1]) % 1440
                halt = '%d min' % h
            rows.append('<tr><td>%d</td><td>%s <small>%s</small></td><td>%s</td><td>%s</td><td>%s</td><td>%d</td></tr>' % (i + 1, lab, code, mm(s[1]), mm(s[2]), halt or '–', s[3]))
        a_l = '<a href="%s%s">%s</a>' % (rel, station_url(A), esc(sname(A))) if A in STATION_PAGES else esc(sname(A))
        b_l = '<a href="%s%s">%s</a>' % (rel, station_url(B), esc(sname(B))) if B in STATION_PAGES else esc(sname(B))
        intro = ('%s <b>%s</b> is a %s train of Indian Railways that runs from %s (%s) to %s (%s). It leaves %s at %s and reaches %s at %s%s, covering about %s km%s with %d stops on the way. '
                 'The train runs %s.' % (no, esc(nm), esc(tytxt(t)), esc(sname(A)), A, esc(sname(B)), B, esc(sname(A)), t[5], esc(sname(B)), t[6],
                                         ' (+%d day%s)' % (extra_days, 's' if extra_days > 1 else '') if extra_days > 0 else '', t[7], ' in %s' % dtxt if dtxt else '', n, days_text(t[9])))
        ret = ''
        if t[8] and t[8] in PUB:
            r = PUB[t[8]]
            ret = ' The return train is <a href="%s%s">%s %s</a>.' % (rel, train_url(t[8]), t[8], esc(tname(r)))
        if t[10]:
            ret += ' The schedule in the feed is valid until %s.' % until_txt(t)
        same = [x for x in BY_OD.get((A, B), []) if x != no][:10]
        near = [NUMS[j] for j in (idx[no] - 1, idx[no] + 1) if 0 <= j < len(NUMS)]
        faq = [
            ('What is the running status of train %s %s?' % (no, nm),
             'Live running position and delay come from the railway control system and are not part of the open timetable data. This page shows the scheduled timetable; check the official <a href="%s" target="_blank" rel="noopener">NTES</a> site for the live status of %s on the day of travel.' % (C.NTES, no)),
            ('What time does %s %s leave %s?' % (no, nm, sname(A)), 'Train %s is scheduled to depart %s at %s and reach %s at %s. It runs %s.' % (no, sname(A), t[5], sname(B), t[6], days_text(t[9]))),
            ('Which days does train %s run?' % no, 'Train %s runs %s%s.' % (no, days_text(t[9]), ' (valid until %s)' % until_txt(t) if t[10] else '')),
            ('How long does %s take from %s to %s?' % (no, sname(A), sname(B)), ('The scheduled journey time is %s for about %s km.' % (dtxt, t[7])) if dtxt else 'The distance is about %s km.' % t[7]),
            ('How many stops does train %s have?' % no, 'Train %s has %d scheduled stops including the origin and destination, for example %s.' % (no, n, ', '.join(sname(s[0]) for s in stops[1:4]) or sname(B))),
        ]
        body = ('<div class="wrap">%s<h1 class="page-title">%s %s – Time Table, Route &amp; Running Days</h1>' % (
            crumbs(rel, [('All Trains', 'all-trains.html'), ('%s %s' % (no, nm), path)]), no, esc(nm)) +
            '<p class="lead">%s → %s · %s km · %s</p>' % (esc(sname(A)), esc(sname(B)), t[7], esc(tytxt(t))) +
            '<div class="card"><h2 style="margin-top:0">%s %s <span class="pill">%s</span></h2><p>%s%s</p><p><b>Departs:</b> %s %s &nbsp; <b>Arrives:</b> %s %s</p><p><b>Runs on:</b> %s</p>' % (
                no, esc(nm), esc(tytxt(t)), intro, ret, a_l, t[5], b_l, t[6], dys(t[9])) +
            '<p><a class="btn" href="%s" target="_blank" rel="noopener">Live status on NTES</a> <a class="btn ghost" href="%slive-train-status.html?train=%s">Search tool</a> <a class="btn ghost" href="%sseat-availability.html">Seats</a> <a class="btn ghost" href="%spnr-status.html">PNR</a></p></div>' % (C.NTES, rel, no, rel, rel) +
            '<div class="card"><h2 style="margin-top:0">%s %s time table &amp; stoppages</h2><div class="scroll"><table class="tbl"><tr><th>#</th><th>Station</th><th>Arr</th><th>Dep</th><th>Halt</th><th>Day</th></tr>%s</table></div>%s</div>' % (no, esc(nm), ''.join(rows), NOTE) +
            faq_html(faq))
        if same:
            body += '<div class="card"><h3 style="margin-top:0">Other trains from %s to %s</h3>%s</div>' % (esc(sname(A)), esc(sname(B)), pills([(rel + train_url(x), '%s %s' % (x, short(tname(PUB[x])))) for x in same]))
        links = []
        if (A, B) in ROUTES:
            links.append((rel + route_url(A, B), 'All trains %s → %s' % (short(sname(A), 20), short(sname(B), 20))))
        if (B, A) in ROUTES:
            links.append((rel + route_url(B, A), 'All trains %s → %s' % (short(sname(B), 20), short(sname(A), 20))))
        for c in (A, B):
            if c in STATION_PAGES:
                links.append((rel + station_url(c), '%s station' % short(sname(c), 26)))
        links += [(rel + train_url(x), '%s %s' % (x, short(tname(PUB[x])))) for x in near]
        body += '<div class="card"><h3 style="margin-top:0">More</h3>%s</div></div>' % pills(links)
        schema = [{'@type': 'TrainTrip', 'name': '%s %s' % (no, nm), 'trainNumber': no, 'trainName': nm, 'url': SITE + '/' + path, 'departureTime': t[5], 'arrivalTime': t[6],
                   'departureStation': {'@type': 'TrainStation', 'name': sname(A), 'identifier': A}, 'arrivalStation': {'@type': 'TrainStation', 'name': sname(B), 'identifier': B}},
                  crumb_ld([('Home', ''), ('All Trains', 'all-trains.html'), ('%s %s' % (no, nm), path)]), faq_ld(faq)]
        page(path, title, desc, kw, body, schema=schema, kind='train', lastmod=FEED_ISO, nav_on='live-train-status.html')

# ===================================================================================== station pages
def build_stations():
    for c in sorted(STATION_PAGES):
        rows = SROWS[c]
        rel = '../'
        nm = sname(c)
        path = station_url(c)
        items = []
        orig = term = 0
        hours = collections.Counter()
        types = collections.Counter()
        times = []
        for no, i, arr, dep, n in rows:
            t = PUB[no]
            tm = dep if dep is not None else arr
            if i == 0:
                orig += 1
            elif i == n - 1:
                term += 1
            hours[(tm // 60) % 24] += 1
            types[tytxt(t)] += 1
            times.append(tm % 1440)
            items.append((tm % 1440, no, t, arr, dep, i, n, tm))
        items.sort(key=lambda x: (x[0], x[1]))
        through = len(rows) - orig - term
        busy = hours.most_common(1)[0][0]
        top_types = ', '.join('%d %s' % (v, k) for k, v in types.most_common(3))
        first_t, last_t = min(times), max(times)
        cap = 150
        trs = []
        for tm, no, t, arr, dep, i, n, raw in items[:cap]:
            trs.append('<tr><td><a href="%s%s"><b>%s</b> %s</a></td><td>%s → %s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                rel, train_url(no), no, esc(short(tname(t), 28)), esc(short(sname(t[3]), 14)), esc(short(sname(t[4]), 14)), mm(arr), mm(dep), dshort(rot(t[9], raw // 1440))))
        title = pick('%s (%s) Railway Station – Trains & Time Table' % (nm, c), '%s (%s) Station – Trains & Time Table' % (nm, c), '%s (%s) Railway Station' % (nm, c))
        desc = trim_desc('%s (%s) railway station: %d trains stop here, %d start and %d end their journey. See arrivals, departures, first and last train and running days.' % (nm, c, len(rows), orig, term))
        kw = ', '.join([nm, '%s railway station' % nm, '%s station code' % nm, '%s %s' % (c, 'station'), '%s station trains' % nm, '%s train time table' % nm, 'trains from %s' % nm, 'trains to %s' % nm,
                        '%s station live status' % nm, '%s arrival departure' % nm, '%s platform' % nm, '%s %s railway station code' % (nm, c)])
        outr = sorted(ROUTES_FROM.get(c, []), key=lambda x: -x[1])[:12]
        origins = [x for x in items if x[5] == 0][:5]
        faq = [
            ('What is the station code of %s?' % nm, 'The station code of %s railway station is %s.' % (nm, c)),
            ('How many trains stop at %s?' % nm, 'In the timetable feed, %d trains are scheduled at %s: %d start here, %d end here and %d stop on their way. %s.' % (len(rows), nm, orig, term, through, top_types)),
            ('What is the busiest time at %s?' % nm, 'The busiest hour is around %02d:00, with %d scheduled train events. The first scheduled train time is %s and the last is %s.' % (busy, hours[busy], mm(first_t), mm(last_t))),
        ]
        if origins:
            faq.append(('Which trains start from %s?' % nm, 'Trains starting here include %s.' % ', '.join('%s %s' % (x[1], tname(x[2])) for x in origins)))
        faq.append(('Where can I see live arrivals and platforms at %s?' % nm, 'Live arrivals, delays and platform numbers are published on the official <a href="%s" target="_blank" rel="noopener">NTES</a> site. This page lists the scheduled trains.' % C.NTES))
        intro = ('<b>%s</b> (station code <b>%s</b>) is served by <b>%d trains</b> in the Indian Railways timetable (%s). %d of them start their journey here, %d terminate here and %d stop on the way. '
                 'Scheduled train times run from %s to %s and the busiest hour is around %02d:00.' % (esc(nm), c, len(rows), esc(top_types), orig, term, through, mm(first_t), mm(last_t), busy))
        body = ('<div class="wrap">%s<h1 class="page-title">%s (%s) Railway Station – Trains &amp; Time Table</h1><p class="lead">%d trains · %d start here · %d end here</p>' % (
            crumbs(rel, [('All Stations', 'all-stations.html'), ('%s (%s)' % (nm, c), path)]), esc(nm), c, len(rows), orig, term) +
            '<div class="card"><p>%s</p><p><a class="btn" href="%s" target="_blank" rel="noopener">Live station status on NTES</a> <a class="btn ghost" href="%sstation-live-status.html">Next trains here</a></p></div>' % (intro, C.NTES, rel) +
            '<div class="card"><h2 style="margin-top:0">Trains at %s</h2><div class="scroll"><table class="tbl"><tr><th>Train</th><th>Route</th><th>Arr</th><th>Dep</th><th>Runs</th></tr>%s</table></div>%s%s</div>' % (
                esc(nm), ''.join(trs), '<p class="muted">Showing the first %d of %d trains by time of day.</p>' % (cap, len(items)) if len(items) > cap else '', NOTE) +
            faq_html(faq))
        if outr:
            body += '<div class="card"><h3 style="margin-top:0">Popular routes from %s</h3>%s</div>' % (esc(nm), pills([(rel + route_url(c, b), '%s → %s' % (short(nm, 18), short(sname(b), 22))) for b, _ in outr]))
        body += '</div>'
        schema = [{'@type': 'TrainStation', 'name': nm, 'identifier': c, 'url': SITE + '/' + path, 'description': desc},
                  crumb_ld([('Home', ''), ('All Stations', 'all-stations.html'), ('%s (%s)' % (nm, c), path)]), faq_ld(faq)]
        page(path, title, desc, kw, body, schema=schema, kind='station', lastmod=FEED_ISO, nav_on='station-live-status.html')

# ======================================================================================= route pages
def build_routes_pages():
    for (a, b), v in ROUTES.items():
        rel = '../'
        path = route_url(a, b)
        A, B = sname(a), sname(b)
        v = sorted(v, key=lambda x: (x[1] % 1440, x[0]))
        n = len(v)
        fastest = min(v, key=lambda x: x[2] - x[1])
        daily = sum(1 for no, d, r in v if PUB[no][9] == '1111111')
        title = pick('Trains from %s to %s – %d Trains, Time Table' % (A, B, n), 'Trains from %s to %s – Time Table' % (A, B), '%s to %s Trains' % (A, B))
        desc = trim_desc('%d direct trains run from %s to %s. Fastest %s takes %s. See departure, arrival, duration and running days of all trains.' % (n, A, B, fastest[0], dur(fastest[2] - fastest[1])))
        kw = ', '.join(['trains from %s to %s' % (A, B), '%s to %s trains' % (A, B), '%s to %s train time table' % (A, B), 'trains between %s and %s' % (A, B), '%s to %s train' % (A, B),
                        '%s to %s train list' % (A, B), '%s to %s fastest train' % (A, B), '%s to %s train running days' % (A, B), '%s %s train' % (a, b)])
        cap = 60
        trs = []
        for no, d, r in v[:cap]:
            t = PUB[no]
            k = r // 1440 - d // 1440
            trs.append('<tr><td><a href="%s%s"><b>%s</b> %s</a></td><td>%s</td><td>%s%s</td><td>%s</td><td>%s</td></tr>' % (
                rel, train_url(no), no, esc(short(tname(t), 28)), mm(d), mm(r), '<small>+%dd</small>' % k if k else '', dur(r - d), dshort(rot(t[9], d // 1440))))
        faq = [
            ('How many trains run from %s to %s?' % (A, B), 'There are %d direct trains from %s to %s in the timetable, of which %d run daily.' % (n, A, B, daily)),
            ('Which is the fastest train from %s to %s?' % (A, B), 'The fastest is %s %s, scheduled at %s.' % (fastest[0], tname(PUB[fastest[0]]), dur(fastest[2] - fastest[1]))),
            ('What is the first and last train from %s to %s?' % (A, B), 'The earliest departure from %s is at %s (train %s) and the latest at %s (train %s).' % (A, mm(v[0][1]), v[0][0], mm(v[-1][1]), v[-1][0])),
            ('How do I check seat availability on this route?', 'Pick a train from the list, then check availability for your date on the official <a href="%s" target="_blank" rel="noopener">IRCTC</a> site.' % C.IRCTC),
        ]
        body = ('<div class="wrap">%s<h1 class="page-title">Trains from %s to %s</h1><p class="lead">%d direct trains · fastest %s</p>' % (
            crumbs(rel, [('Popular Routes', 'popular-routes.html'), ('%s to %s' % (A, B), path)]), esc(A), esc(B), n, dur(fastest[2] - fastest[1])) +
            '<div class="card"><p>There are <b>%d direct trains from %s to %s</b>, %d of them running daily. The earliest leaves %s at %s and the last at %s. The fastest train, <a href="%s%s">%s %s</a>, takes %s.</p></div>' % (
                n, esc(A), esc(B), daily, esc(A), mm(v[0][1]), mm(v[-1][1]), rel, train_url(fastest[0]), fastest[0], esc(tname(PUB[fastest[0]])), dur(fastest[2] - fastest[1])) +
            '<div class="card"><h2 style="margin-top:0">%s to %s train time table</h2><div class="scroll"><table class="tbl"><tr><th>Train</th><th>Dep</th><th>Arr</th><th>Time</th><th>Runs</th></tr>%s</table></div>%s%s</div>' % (
                esc(A), esc(B), ''.join(trs), '<p class="muted">Showing the first %d of %d trains.</p>' % (cap, n) if n > cap else '', NOTE) +
            faq_html(faq) +
            '<div class="card"><h3 style="margin-top:0">More</h3>%s</div></div>' % pills(
                ([(rel + route_url(b, a), 'Trains %s → %s' % (short(B, 20), short(A, 20)))] if (b, a) in ROUTES else []) +
                [(rel + station_url(a), '%s station' % short(A, 26)), (rel + station_url(b), '%s station' % short(B, 26)), (rel + 'trains-between-stations.html?from=%s&to=%s' % (a, b), 'Search tool')]))
        schema = [crumb_ld([('Home', ''), ('Popular Routes', 'popular-routes.html'), ('%s to %s' % (A, B), path)]), faq_ld(faq)]
        page(path, title, desc, kw, body, schema=schema, kind='route', lastmod=FEED_ISO, nav_on='trains-between-stations.html')

# ============================================================================================== hubs
def listing(path, title, desc, kw, h1, intro, trail, groups_html, extra=''):
    rel = '../' * path.count('/')
    body = ('<div class="wrap">%s<h1 class="page-title">%s</h1><p class="lead">%s</p>%s%s</div>' % (crumbs(rel, trail), esc(h1), esc(intro), groups_html, extra))
    page(path, title, trim_desc(desc), kw, body, schema=[crumb_ld([('Home', '')] + trail)], kind='hub', nav_on=None)

def build_hubs():
    # trains by number prefix
    groups = collections.defaultdict(list)
    for no in NUMS:
        groups[no[:2]].append(no)
    cards = ''.join('<a class="tile" href="trains-by-number/%s.html"><h3>%sxxx</h3><p>%d trains</p></a>' % (g, g, len(v)) for g, v in sorted(groups.items()))
    for g, v in sorted(groups.items()):
        lst = ''.join('<li><a href="../%s">%s %s</a> <small class="muted">%s → %s</small></li>' % (train_url(no), no, esc(tname(PUB[no])), esc(short(sname(PUB[no][3]), 18)), esc(short(sname(PUB[no][4]), 18))) for no in v)
        listing('trains-by-number/%s.html' % g, 'Train Numbers %sxxx – Train List & Time Table' % g, 'List of %d Indian Railways trains numbered %sxxx with route and links to the time table, stoppages and running days of each train.' % (len(v), g),
                'train list, train numbers %sxxx, train time table, train number list, Indian railways trains' % g, 'Trains numbered %sxxx' % g, '%d trains. Open a train for its full time table, route and running days.' % len(v),
                [('All Trains', 'all-trains.html'), ('%sxxx' % g, 'trains-by-number/%s.html' % g)], '<div class="card"><ul class="clean cols">%s</ul></div>' % lst)
    listing('all-trains.html', 'All Trains – Complete Indian Railways Train List', 'Complete list of %s+ Indian Railways trains by number with time table, route, stoppages and running days. Find any train number quickly.' % NT,
            'all trains list, Indian railways train list, train number list, train time table, all train numbers, train name and number', 'All Trains', 'Browse %s+ trains by train number range.' % NT, [('All Trains', 'all-trains.html')],
            '<div class="grid">%s</div>' % cards, '<h2>Popular trains</h2>%s' % train_pills('', POP_TRAINS))
    # stations A-Z
    sg = collections.defaultdict(list)
    for c in STATION_PAGES:
        sg[(sname(c)[:1] or '#').upper()].append(c)
    letters = sorted(k for k in sg if k.isalpha())
    for L in letters:
        v = sorted(sg[L], key=lambda c: sname(c))
        lst = ''.join('<li><a href="../%s">%s (%s)</a> <small class="muted">%d trains</small></li>' % (station_url(c), esc(sname(c)), c, len(SROWS[c])) for c in v)
        listing('stations-a-z/%s.html' % L.lower(), 'Railway Stations Starting with %s – Station Codes & Trains' % L, 'Indian railway stations starting with %s with station codes and the trains that stop at each station. %d stations listed.' % (L, len(v)),
                'railway stations starting with %s, station code list, Indian railway station list, station name and code, trains at station' % L, 'Railway stations starting with %s' % L, '%d stations with their codes.' % len(v),
                [('All Stations', 'all-stations.html'), (L, 'stations-a-z/%s.html' % L.lower())], '<div class="card"><ul class="clean cols">%s</ul></div>' % lst)
    listing('all-stations.html', 'All Railway Stations – Station Codes & Train Lists', 'Browse %s+ Indian railway stations A to Z with station codes, trains stopping at each station, first and last train and busiest hours.' % NS,
            'railway station list, station code list, all railway stations India, station name and code, Indian railway stations A to Z, station time table', 'All Railway Stations', 'Browse stations by first letter.', [('All Stations', 'all-stations.html')],
            '<div class="related">%s</div>' % ''.join('<a href="stations-a-z/%s.html">%s</a>' % (L.lower(), L) for L in letters), '<h2>Busiest stations</h2>%s' % station_pills('', POP_STATIONS))
    # routes A-Z
    rg = collections.defaultdict(list)
    for (a, b), v in ROUTES.items():
        rg[(sname(a)[:1] or '#').upper()].append((a, b, len(v)))
    rl = sorted(k for k in rg if k.isalpha())
    for L in rl:
        v = sorted(rg[L], key=lambda x: (sname(x[0]), -x[2]))
        lst = ''.join('<li><a href="../%s">%s → %s</a> <small class="muted">%d trains</small></li>' % (route_url(a, b), esc(sname(a)), esc(sname(b)), k) for a, b, k in v)
        listing('routes-a-z/%s.html' % L.lower(), 'Trains from Stations Starting with %s – Popular Routes' % L, 'Popular train routes starting from stations beginning with %s. Direct trains with time table, duration and running days.' % L,
                'trains from %s, train routes, trains between stations, popular train routes, direct trains list' % L, 'Popular routes from stations starting with %s' % L, '%d routes.' % len(v),
                [('Popular Routes', 'popular-routes.html'), (L, 'routes-a-z/%s.html' % L.lower())], '<div class="card"><ul class="clean cols">%s</ul></div>' % lst)
    listing('popular-routes.html', 'Popular Train Routes – Direct Trains Between Cities', 'Popular Indian railway routes with all direct trains, departure and arrival times, duration and running days. Find trains from any city to any city.',
            'popular train routes, trains between cities, train routes India, direct trains list, trains from city to city, train route time table', 'Popular Train Routes', 'Most-searched direct train routes.', [('Popular Routes', 'popular-routes.html')],
            '<div class="related">%s</div>' % ''.join('<a href="routes-a-z/%s.html">%s</a>' % (L.lower(), L) for L in rl), '<h2>Top routes</h2>%s' % route_pills('', POP_ROUTES))

def build_sitemap_html():
    tools = ''.join('<li><a href="%s">%s</a></li>' % (f['file'], esc(f['name'])) for f in C.TOOLS)
    body = ('<div class="wrap">%s<h1 class="page-title">Sitemap</h1><div class="card"><ul class="clean"><li><a href="index.html">Home</a></li>%s<li><a href="all-trains.html">All Trains</a></li><li><a href="all-stations.html">All Stations</a></li><li><a href="popular-routes.html">Popular Routes</a></li></ul>' % (crumbs('', [('Sitemap', 'sitemap.html')]), tools) +
            '<p class="muted">Machine readable: <a href="sitemap.xml">sitemap.xml</a> · <a href="llms.txt">llms.txt</a> · <a href="robots.txt">robots.txt</a></p></div>' +
            '<div class="card"><h2 style="margin-top:0">Popular trains</h2>%s<h2>Popular routes</h2>%s<h2>Popular stations</h2>%s</div></div>' % (train_pills('', POP_TRAINS), route_pills('', POP_ROUTES), station_pills('', POP_STATIONS)))
    page('sitemap.html', 'Sitemap | Where Is My Train', 'Sitemap of Where Is My Train: all tools, train list, station list and popular routes.', 'sitemap, site map, where is my train pages, train list, station list',
         body, schema=[ORG, crumb_ld([('Home', ''), ('Sitemap', 'sitemap.html')])], kind='main')

def build_admin():
    body = """<div class="wrap"><h1 class="page-title">Update timetable data</h1>
<p class="lead">Upload a new GTFS feed and the site rebuilds itself: data files, every train, station and route page, sitemaps and the app cache.</p>
<div class="card"><h2 style="margin-top:0">How it works</h2><ol>
<li>Download the latest feed ZIP from the <a href="FEEDPAGE" target="_blank" rel="noopener">Mobility Database feed page</a> (button &ldquo;Download latest dataset&rdquo;).</li>
<li>Choose that ZIP below. It is checked in your browser first.</li>
<li>Press <b>Upload and rebuild</b>. The ZIP is committed to your GitHub repository and a GitHub Action converts it and republishes the site (usually 3 to 8 minutes).</li></ol>
<p class="muted"><small>You need a GitHub token once: GitHub &rarr; Settings &rarr; Developer settings &rarr; Fine-grained tokens &rarr; repository access: only this repo &rarr; permissions <b>Contents: Read and write</b> and <b>Actions: Read and write</b>. The token is used only to talk to api.github.com from this page.</small></p></div>
<form id="af" data-repo="REPO" class="card" autocomplete="off">
<h2 style="margin-top:0">Upload a feed ZIP</h2>
<div class="f"><div><label for="repo">GitHub repository</label><input id="repo" placeholder="owner/name"></div><div><label for="branch">Branch</label><input id="branch" placeholder="main"></div></div>
<div style="margin-top:12px"><label for="token">GitHub token</label><input id="token" type="password" placeholder="github_pat_…" autocomplete="off"><label style="font-weight:500;margin-top:6px"><input id="remember" type="checkbox" style="width:auto"> Remember the token in this browser</label></div>
<div style="margin-top:12px"><label for="zip">GTFS feed (.zip)</label><input id="zip" type="file" accept=".zip,application/zip"><small class="muted" id="fname"></small></div>
<div id="zipinfo" style="margin-top:10px"></div>
<p style="margin-top:14px"><button class="btn" id="go" type="submit">Upload and rebuild</button></p>
<hr style="border:0;border-top:1px solid var(--line);margin:18px 0">
<h3 style="margin-top:0">Or: rebuild from a direct feed link</h3>
<p class="muted">Paste the direct download link of the feed ZIP (copy it from the Mobility Database download button). GitHub downloads it itself, so you do not need to upload a large file.</p>
<div class="f"><div><label for="feedurl">Feed ZIP URL</label><input id="feedurl" type="url" placeholder="https://…/latest.zip"></div><div><button class="btn ghost" id="go2" type="button">Rebuild from link</button></div></div>
</form>
<div class="card"><h3 style="margin-top:0">Progress</h3><div id="log" class="adminlog" aria-live="polite"><span class="muted">Nothing yet.</span></div></div>
</div><script src="assets/js/admin.js"></script>""".replace('FEEDPAGE', esc(CFG['feed_page'])).replace('REPO', esc(CFG['github_repo']))
    page('admin.html', 'Update timetable data | Where Is My Train', 'Upload a new GTFS feed to refresh the timetable data.', 'admin', body, noindex=True, data_page='admin')

# ===================================================================== sitemaps, robots, llms, 404, sw
def write_sitemaps():
    os.makedirs(os.path.join(ROOT, 'sitemaps'), exist_ok=True)
    by = collections.defaultdict(list)
    for p, kind, lm in written:
        by[kind].append((p, lm))
    index = []
    for kind in ['main', 'hub', 'route', 'station', 'train']:
        items = sorted(by.get(kind, []))
        for k in range(0, len(items), 10000):
            chunk = items[k:k + 10000]
            name = 'sitemaps/sitemap-%s-%d.xml' % (kind, k // 10000 + 1)
            pr = {'main': '0.8', 'hub': '0.6', 'route': '0.6', 'station': '0.5', 'train': '0.5'}[kind]
            xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                   ''.join('<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>' % (
                       SITE + '/' + ('' if p == 'index.html' else p), lm, 'daily' if p == 'index.html' else 'weekly' if kind == 'main' else 'monthly', '1.0' if p == 'index.html' else pr) for p, lm in chunk) + '</urlset>')
            write(name, xml)
            index.append((name, max(lm for _, lm in chunk)))
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
          ''.join('<sitemap><loc>%s/%s</loc><lastmod>%s</lastmod></sitemap>' % (SITE, n, lm) for n, lm in index) + '</sitemapindex>')
    write('robots.txt', 'User-agent: *\nAllow: /\nDisallow: %s/admin.html\n\nSitemap: %s/sitemap.xml\n' % (BASEPATH, SITE))
    cnt = collections.Counter(k for _, k, _ in written)
    return cnt

def write_llms():
    L = ['# %s' % BRAND, '',
         '> Independent, free train information website and installable app: train time table, route, halts and running days for %s+ Indian Railways trains and %s+ stations, trains between stations, '
         'station boards, and guides for live running status, PNR status, seat availability, coach position and platforms. Timetable data is the community Indian Railways GTFS feed (version %s, unofficial); '
         'live data links to official NTES and IRCTC.' % (NT, NS, FEED_TXT), '', '## Main tools']
    for f in C.TOOLS[:9]:
        L.append('- [%s](%s/%s): %s' % (f['name'], SITE, f['file'], fill(f['desc'])))
    L += ['', '## Directories', '- [All Trains](%s/all-trains.html): every train by number range with its own time table page.' % SITE,
          '- [All Stations](%s/all-stations.html): every station A to Z with trains, first and last service.' % SITE,
          '- [Popular Routes](%s/popular-routes.html): direct trains between major station pairs.' % SITE, '', '## Information']
    for f in C.TOOLS[9:]:
        L.append('- [%s](%s/%s)' % (f['name'], SITE, f['file']))
    L += ['', '## Machine readable', '- [sitemap.xml](%s/sitemap.xml)' % SITE, '- [robots.txt](%s/robots.txt)' % SITE, '',
          '## Notes for AI systems', '- Not affiliated with any railway operator.', '- Timetable results are scheduled data, not live or official current data. Do not present them as real-time.']
    write('llms.txt', '\n'.join(L) + '\n')

def write_404():
    body = ('<div class="wrap"><h1 class="page-title">Page not found</h1><div class="card"><p>The page you are looking for does not exist. Try a train number search or browse the lists below.</p>'
            '<form class="f" action="live-train-status.html" method="get"><div><label for="q">Train number or name</label><input id="q" name="train" data-suggest="train" placeholder="e.g. 12951" required></div><div><button class="btn" type="submit">Search</button></div></form>'
            '<p><a class="btn" href="index.html">Go home</a> <a class="btn ghost" href="all-trains.html">All trains</a> <a class="btn ghost" href="all-stations.html">All stations</a></p></div></div>')
    page('404.html', 'Page not found | Where Is My Train', 'Page not found.', 'where is my train', body, schema=None, noindex=True, base=BASEPATH + '/')

def write_sw():
    core = ['./', 'index.html'] + [f['file'] for f in C.TOOLS] + ['all-trains.html', 'all-stations.html', 'popular-routes.html', 'sitemap.html',
            'assets/css/style.css', 'assets/js/app.js', 'assets/js/config.js', 'assets/img/logo.svg', 'manifest.webmanifest']
    ver = 'wimt-' + re.sub(r'\D', '', V.get('feed', '') or '') + '-' + TODAY.strftime('%Y%m%d')
    write('sw.js', "const C='%s';const F=%s;\n" % (ver, json.dumps(core)) +
          "self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)).then(()=>self.skipWaiting()))});\n"
          "self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});\n"
          "self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;\n"
          "e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp))}return r}).catch(()=>caches.match(e.request).then(m=>m||caches.match('index.html'))))});\n")

def main():
    for d in GEN_DIRS:
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    build_home()
    for f in C.TOOLS:
        build_tool(f)
    build_trains()
    build_stations()
    build_routes_pages()
    build_hubs()
    build_sitemap_html()
    write_404()
    build_admin()
    cnt = write_sitemaps()
    write_llms()
    write_sw()
    print('pages written:', dict(cnt), '| trains %d stations %d routes %d | feed %s' % (len(PUB), len(STATION_PAGES), len(ROUTES), FEED_ISO))

if __name__ == '__main__':
    main()
