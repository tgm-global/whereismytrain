# Where Is My Train

Independent, free train information website and installable PWA by TGM Global. Static site, hosted on GitHub Pages.
Live URL: https://tgm-global.github.io/whereismytrain/

## What is generated (SEO)
`python3 tools/build_site.py` writes the whole site from `assets/data/`:

| Output | Count (feed 2026-08-30) | Notes |
|---|---|---|
| Main + tool + info pages | 18 | copy, titles, descriptions, keywords and FAQs live in `tools/site_content.py` |
| `train/<no>-<name>.html` | ~10,100 | time table, route, halts, running days, FAQ, TrainTrip schema |
| `station/<name>-<code>.html` | ~6,400 | stations with 5+ trains: all trains, first/last, busiest hour, FAQ |
| `route/...html` | 3,000 | most-served direct routes ("trains from A to B") |
| hubs | ~130 | `all-trains`, `all-stations`, `popular-routes` (+ A-Z / number pages) so every page is crawlable |
| `sitemap.xml` + `sitemaps/*.xml`, `robots.txt`, `llms.txt`, `404.html`, `sw.js` | | sitemap index with ~19,700 URLs |

Every page has: unique `<title>`, meta description, meta keywords, canonical, Open Graph / Twitter card, JSON-LD (BreadcrumbList, FAQPage, TrainTrip / TrainStation / WebApplication) and a single H1.
Settings (site URL, Google / Bing verification codes, page limits) are in `tools/site.json`.

## Update the timetable (3 ways)
1. **Admin page (no coding):** open `https://<your-site>/admin.html`, choose the feed ZIP downloaded from
   https://mobilitydatabase.org/feeds/gtfs/mdb-2867, press *Upload and rebuild*. The ZIP is committed to `feed/gtfs.zip` and the
   GitHub Action `.github/workflows/update-feed.yml` converts it, regenerates every page and republishes (3-8 min).
   You can also paste a direct feed URL instead of uploading. One-time setup: a fine-grained GitHub token for this repo with
   *Contents* and *Actions* read/write.
2. **Command line:** `python3 tools/update_from_zip.py path/to/feed.zip` then commit and push.
3. **Monthly automatic:** add a repository variable `FEED_URL` (direct link to the feed ZIP) and the workflow refreshes on the 1st of each month.

The converter refuses a feed that has less than half the old number of trains (wrong file) unless run with `--force`.

## After the first deploy
1. Google Search Console: add the property, paste the verification code into `tools/site.json` (`google_site_verification`), rebuild, submit `sitemap.xml`.
2. Bing Webmaster Tools: same with `bing_site_verification`, or import the site from Search Console.
3. GitHub Pages serves `robots.txt` only from the domain root. On a `github.io/whereismytrain` project URL crawlers ignore it, so submit the sitemap manually (step 1-2). A custom domain removes this limit (change `site_url` in `tools/site.json` and rebuild).

## Data
`assets/data/` holds the Indian Railways timetable (running days included) from the unofficial community GTFS feed
[Neo2308/indianrailways-gtfs](https://github.com/Neo2308/indianrailways-gtfs) (Mobility Database feed mdb-2867), converted to compact JSON shards by `tools/build_data_gtfs.py`.
Only halting stations are in the feed. Live status / PNR / seats are not available free; those pages link to NTES / IRCTC.
To add live data, deploy a proxy and set `window.WIMT_API` in `assets/js/config.js`; `GET API_URL/live?train=NO` should return `{status, delayMin, updated}`.
Credit: GTFS feed by P. Radha Krishna (Neo2308). The feed states no license, so check with the author before commercial use.

## Language
Pages are English. On load the visitor's browser language is detected and the page is translated with the Google Translate widget. A flashing "View in English" button switches back; a language menu is in the header.

## Deploy
GitHub repo `tgm-global/whereismytrain` -> Settings -> Pages -> Deploy from branch `main` / root.
Settings -> Actions -> General -> Workflow permissions: *Read and write* (needed so the Action can commit the rebuilt pages).
