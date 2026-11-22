# Where Is My Train

Independent, free train information website and installable PWA by TGM Global. Static site: no build step needed.

Live URL: https://tgm-global.github.io/whereismytrain/

## Pages
Home, Train Status & Timetable, PNR Status, Trains Between Stations, Station Live Status, Seat Availability, Coach Position, Train Schedule, Platform Locator, Get the App, Features, About, FAQ, Contact, Privacy, Terms, Disclaimer, Sitemap, 404. Also `sitemap.xml`, `robots.txt`, `llms.txt`, `manifest.webmanifest`, `sw.js`.

## Data
`assets/data/` holds the Indian Railways timetable (10,149 trains, 8,538 stations, with running days) from the unofficial community GTFS feed [Neo2308/indianrailways-gtfs](https://github.com/Neo2308/indianrailways-gtfs) (Mobility Database feed mdb-2867, version 2026-08-30), converted to compact JSON shards by `tools/build_data_gtfs.py`.
To refresh: download the latest GTFS zip, unzip, then `python3 tools/build_data_gtfs.py GTFS_DIR assets/data assets/data/meta.json` (bump `wimt-v2` in `sw.js` afterwards). Only halting stations are in the feed. The older 2016 Datameet build script is kept as `tools/build_data_datameet_2016.py`. Live status/PNR/seats are not available free; those pages link to NTES/IRCTC. To add live data, deploy a proxy and set `window.WIMT_API` in `assets/js/config.js`; `GET API_URL/live?train=NO` should return `{status, delayMin, updated}`.

Credit: GTFS feed by P. Radha Krishna (Neo2308). The feed states no license, so check with the author before commercial use.

## Language
Pages are English. On load the visitor's browser language is detected and the page is translated with the Google Translate widget. A flashing "View in English" button switches back; a language menu is in the header.

## Deploy
GitHub repo `tgm-global/whereismytrain` → Settings → Pages → Deploy from branch `main` / root.
