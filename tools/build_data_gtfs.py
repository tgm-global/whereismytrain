#!/usr/bin/env python3
"""Build site data shards from the Indian Railways community GTFS feed
(github.com/Neo2308/indianrailways-gtfs, via Mobility Database feed mdb-2867).

usage: build_data_gtfs.py GTFS_DIR OUT_DATA_DIR [OLD_META_JSON] [YYYYMMDD today]
OLD_META_JSON (optional) is the previous meta.json; used only to restore full
train names (GTFS names are cut at 15 chars)."""
import csv, json, os, re, shutil, sys, collections, datetime
src, out = sys.argv[1], sys.argv[2]
old = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
today = sys.argv[4] if len(sys.argv) > 4 else datetime.date.today().strftime('%Y%m%d')
rd = lambda f: csv.DictReader(open(os.path.join(src, f), encoding='utf-8'))
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def mins(t):
    h, m, _ = t.split(':'); return int(h) * 60 + int(m)
def title(s):
    s = re.sub(r'\s+', ' ', s.strip()).title()
    return re.sub(r'\b(Jn|Cst|Cstm|Ltt|Ndls)\b', lambda m: m.group(1).upper() if m.group(1) != 'Jn' else 'Jn', s)

ABBR = {'EXPRES': 'Express', 'EXP': 'Express', 'EX': 'Express', 'SPL': 'Special', 'SF': 'Superfast', 'SFAST': 'Superfast',
        'PASS': 'Passenger', 'PGR': 'Passenger', 'JN': 'Jn', 'FTR': 'FTR', 'MEMU': 'MEMU', 'DEMU': 'DEMU', 'EMU': 'EMU'}
def nice(name, codes):
    w = re.sub(r'\s+', ' ', name.strip()).split(' ')
    out = []
    for i, x in enumerate(w):
        u = x.upper()
        if i == 0 and len(w) > 1 and 2 <= len(u) <= 4 and u in codes and u not in ABBR and u not in ('RAJ', 'JAN', 'MAIL', 'LOCAL'): out.append(u)
        else: out.append(ABBR.get(u, x.title()))
    return ' '.join(out)

def ttype(name):
    n = name.upper().replace(' ', '')
    for k, v in [('VANDE', 'VB'), ('AMRITBHARAT', 'AB'), ('HUMSAFAR', 'Humsafar'), ('TEJAS', 'Tejas'), ('JANSHATABDI', 'Jan'),
                 ('SHATABDI', 'Shtb'), ('SHTB', 'Shtb'), ('RAJDHANI', 'Raj'), ('DURONTO', 'Drnt'), ('GARIB', 'Garib'),
                 ('RAJYARANI', 'Rajya'), ('MEMU', 'MEMU'), ('DEMU', 'DEMU'), ('EMU', 'EMU'), ('LOCAL', 'Local'), ('SUBURBAN', 'Local'),
                 ('PASS', 'Pass'), ('PGR', 'Pass'), ('MAIL', 'Mail'), ('SUPERFAST', 'SF'), ('SFAST', 'SF'), ('SPECIAL', 'Spl'), ('SPL', 'Spl')]:
        if k in n: return v
    if re.search(r'(^|\W)SF(\W|$)|SF$', name.upper()): return 'SF'
    return 'Exp'

names = {r['stop_id']: title(r['stop_name']) for r in rd('stops.txt')}
rname = {r['route_id']: r['route_long_name'] for r in rd('routes.txt')}
trip = {r['trip_id']: r for r in rd('trips.txt')}
oldname = {t[0]: t for t in old['t']} if old else {}

def service(sid):
    d, dates = sid.rsplit('_', 1)
    s, e = dates.split('-')
    return ''.join('1' if x in d.split('-') else '0' for x in DAYS), s, e

rows = collections.defaultdict(list)
for r in rd('stop_times.txt'): rows[r['trip_id']].append(r)

meta, trs, sts, used = [], collections.defaultdict(dict), collections.defaultdict(list), set()
dropped = 0
for no, tp in trip.items():
    days, s, e = service(tp['service_id'])
    span = (datetime.datetime.strptime(e, '%Y%m%d') - datetime.datetime.strptime(s, '%Y%m%d')).days
    if e < today and 0 <= span <= 31: dropped += 1; continue   # expired one-off special
    rs = sorted(rows.get(no, []), key=lambda r: int(r['stop_sequence']))
    if len(rs) < 2: continue
    stops = []
    for i, r in enumerate(rs):
        a, d = mins(r['arrival_time']), mins(r['departure_time'])
        first, last = i == 0, i == len(rs) - 1
        day = (a if last else d) // 1440 + 1
        stops.append([r['stop_id'], None if first else a % 1440, None if last else d % 1440, day, 1])
        sts[r['stop_id']].append([no, i, None if first else a, None if last else d, len(rs)])
        used.add(r['stop_id'])
    trs[no[:3]][no] = stops
    nm = rname.get(tp['route_id'], '')
    f, l = rs[0], rs[-1]
    o = oldname.get(no)   # same number and same endpoints = same train: reuse its full (untruncated) name
    nm_out = o[1] if o and o[3] == f['stop_id'] and o[4] == l['stop_id'] else nice(nm, names)
    km = int(float(l['shape_dist_traveled'] or 0))
    fmt = lambda t: '%02d:%02d' % (mins(t) // 60 % 24, mins(t) % 60)
    until = e if e < '20270601' else ''
    meta.append([no, nm_out, ttype(nm), f['stop_id'], l['stop_id'], fmt(f['departure_time']), fmt(l['arrival_time']), km, '', days, until])

ix = {t[0]: t for t in meta}
for t in meta:                       # guess return train: neighbouring number with reversed endpoints
    if not t[0].isdigit(): continue
    for d in (1, -1):
        c = ix.get(str(int(t[0]) + d).zfill(len(t[0])))
        if c and c[3] == t[4] and c[4] == t[3]: t[8] = c[0]; break
meta.sort()
shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/tr'); os.makedirs(out + '/st')
dump = lambda p, o: open(p, 'w', encoding='utf-8').write(json.dumps(o, separators=(',', ':'), ensure_ascii=False))
fi = next(rd('feed_info.txt'))
dump(out + '/meta.json', {'s': {c: names.get(c, c) for c in used}, 't': meta,
     'v': {'feed': fi['feed_version'], 'built': today, 'source': 'Neo2308/indianrailways-gtfs'}})
for k, v in trs.items(): dump(f'{out}/tr/{k}.json', v)
sh = collections.defaultdict(dict)
for c, v in sts.items(): sh[c[:2].upper()][c] = v
for k, v in sh.items(): dump(f'{out}/st/{k}.json', v)
print('trains', len(meta), 'stations', len(used), 'dropped expired', dropped, 'feed', fi['feed_version'])
