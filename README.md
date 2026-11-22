# Where Is My Train

Independent, free train information website and installable PWA by TGM Global. Static site: no build step needed.

Live URL: https://tgm-global.github.io/whereismytrain/

## Pages
Home, Train Status & Timetable, PNR Status, Trains Between Stations, Station Live Status, Seat Availability, Coach Position, Train Schedule, Platform Locator, Get the App, Features, About, FAQ, Contact, Privacy, Terms, Disclaimer, Sitemap, 404. Also `sitemap.xml`, `robots.txt`, `llms.txt`, `manifest.webmanifest`, `sw.js`.

## Data
`assets/data/` holds an open timetable dataset (5,208 trains, 7,397 stations) from [datameet/railways](https://github.com/datameet/railways) (about 2016), converted to compact JSON shards by `build_data.py`. Live status/PNR/seats are not available free; those pages link to NTES/IRCTC. To add live data, deploy a proxy and set `window.WIMT_API` in `assets/js/config.js`; `GET API_URL/live?train=NO` should return `{status, delayMin, updated}`.

Credit: dataset by Sanjay Bhangar and Sajjad Anwar (Datameet). Check the dataset's terms before commercial use.

## Language
Pages are English. On load the visitor's browser language is detected and the page is translated with the Google Translate widget. A flashing "View in English" button switches back; a language menu is in the header.

## Deploy
GitHub repo `tgm-global/whereismytrain` → Settings → Pages → Deploy from branch `main` / root.
