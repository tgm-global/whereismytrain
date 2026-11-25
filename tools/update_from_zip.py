#!/usr/bin/env python3
"""Refresh the whole site from a GTFS feed ZIP (stdlib only).

  python3 tools/update_from_zip.py path/to/feed.zip [--force]

1. validates the ZIP (needs stops/stop_times/trips/routes .txt)
2. converts it to assets/data/*.json with tools/build_data_gtfs.py (full train names are kept from the old meta.json)
3. refuses to continue if the new feed has less than half the old number of trains (wrong file?) unless --force
4. regenerates every page, sitemap and the service-worker cache version with tools/build_site.py
This is what the GitHub Action (.github/workflows/update-feed.yml) runs after you upload a ZIP on admin.html."""
import json, os, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'assets', 'data')
NEED = ['stops.txt', 'stop_times.txt', 'trips.txt', 'routes.txt']
WANT = NEED + ['calendar.txt', 'calendar_dates.txt', 'feed_info.txt', 'agency.txt']

def die(msg):
    print('ERROR:', msg, file=sys.stderr)
    sys.exit(1)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    if len(args) != 1:
        die('usage: update_from_zip.py feed.zip [--force]')
    if not zipfile.is_zipfile(args[0]):
        die('%s is not a valid ZIP file' % args[0])
    zf = zipfile.ZipFile(args[0])
    names = zf.namelist()
    base = None
    for n in names:
        if n == 'stops.txt' or n.endswith('/stops.txt'):
            base = n[:-len('stops.txt')]
            break
    if base is None:
        die('stops.txt not found in the ZIP - this does not look like a GTFS feed')
    missing = [f for f in NEED if base + f not in names]
    if missing:
        die('GTFS files missing from the ZIP: ' + ', '.join(missing))
    tmp = tempfile.mkdtemp(prefix='gtfs_')
    try:
        src = os.path.join(tmp, 'src')
        os.makedirs(src)
        for f in WANT:
            if base + f in names:
                with zf.open(base + f) as i, open(os.path.join(src, f), 'wb') as o:
                    shutil.copyfileobj(i, o)
        old_meta = os.path.join(DATA, 'meta.json')
        old_n = len(json.load(open(old_meta, encoding='utf-8'))['t']) if os.path.exists(old_meta) else 0
        out = os.path.join(tmp, 'out')
        cmd = [sys.executable, os.path.join(HERE, 'build_data_gtfs.py'), src, out, old_meta if os.path.exists(old_meta) else '-']
        print('> converting feed ...')
        if subprocess.call(cmd) != 0:
            die('feed conversion failed')
        new_n = len(json.load(open(os.path.join(out, 'meta.json'), encoding='utf-8'))['t'])
        print('trains: old %d -> new %d' % (old_n, new_n))
        if new_n == 0:
            die('the feed produced 0 trains')
        if old_n and new_n < old_n * 0.5 and not force:
            die('new feed has less than half the old trains (%d vs %d). Wrong file? Re-run with --force if this is intended.' % (new_n, old_n))
        shutil.rmtree(DATA, ignore_errors=True)
        shutil.copytree(out, DATA)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('> rebuilding pages ...')
    if subprocess.call([sys.executable, os.path.join(HERE, 'build_site.py')]) != 0:
        die('page generation failed')
    print('Done. Commit and push to publish.')

if __name__ == '__main__':
    main()
