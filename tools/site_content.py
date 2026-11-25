# -*- coding: utf-8 -*-
"""Editable page copy + SEO fields (title / description / keywords / FAQ) for every hand-written page.
{NT} {NS} {FEED} are replaced at build time (train count, station count, feed date).
Edit here, then run:  python3 tools/build_site.py
Rules of thumb: title <= 60 chars, description <= 155 chars, one H1, copy must be true (no fake 'live' data)."""

NTES = 'https://enquiry.indianrail.gov.in/ntes/'
IRCTC = 'https://www.irctc.co.in/nget/train-search'
PNR = 'https://www.indianrail.gov.in/enquiry/PNR/PnrEnquiry.html'

def ext(url, label):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, label)

# --------------------------------------------------------------------------- shared FAQ answers
FAQ_LIVE = ('Is the running status real-time?',
            'The timetable on this site comes from the open Indian Railways GTFS feed, so it shows scheduled times, routes and running days. '
            'Real-time delay and last-reported-station data is produced by the railway control system and published only on the official %s site, which we link to on every train page.' % ext(NTES, 'NTES'))

TOOLS = [
 dict(
  file='live-train-status.html', name='Live Train Status', nav='Live Status', data_page='live', schema='WebPage',
  title='Live Train Running Status – Check Train Status by Number',
  desc='Check live train running status, route, halts and full time table of {NT}+ Indian Railways trains by train number or name. Free, fast, no login.',
  kw='live train status, live train running status, train running status, train status by number, where is my train, train tracking, track train live, train live location, train enquiry, train time table, train route, train stoppages, NTES live status',
  h1='Live Train Running Status & Time Table',
  lead='Type a train number or name to see its full route, halts, running days and scheduled times – then open the official NTES page for the live position.',
  form='''<form class="f" id="f"><div><label for="train">Train number or name</label><input id="train" data-suggest="train" placeholder="Number or name, e.g. 12951" autocomplete="off" required></div><div><button class="btn" type="submit">Check train status</button></div></form>''',
  sections=[
   ('How to check train running status', '''<ol><li>Enter the 5-digit train number (for example 12951) or part of the train name in the box above.</li><li>Pick the train from the suggestions and press <b>Check train status</b>.</li><li>Read the scheduled arrival and departure at every halt, the day of journey and the days of the week the train runs.</li><li>On the day of travel, open the {NTES} link on the result for the live position and delay.</li></ol>'''),
   ('What does train running status tell you?', '''<p>A train running status answers three practical questions: <b>where is the train now</b>, <b>how late is it</b>, and <b>when will it reach my station</b>. Delays build up or shrink along the route because trains regain time at long non-stop stretches, so the expected arrival at your station matters more than the delay shown at the previous one.</p><p>This site shows the planned schedule for {NT}+ trains and {NS}+ stations. Live position and delay are available only from the railway&rsquo;s own system, so we send you to the official site instead of showing numbers we cannot verify.</p>'''),
   ('Search by train name, number or route', '''<p>Not sure of the number? Type the train name, or use <a href="trains-between-stations.html">trains between stations</a> to list every direct train from one station to another. Every train also has its own page with time table, stoppages and running days &ndash; browse them in the <a href="all-trains.html">complete train list</a>.</p>'''),
  ],
  faq=[FAQ_LIVE,
       ('How do I find the train number?', 'Search by name in the box above, or use Trains Between Stations to list trains for your route. The 5-digit number is shown next to every train name.'),
       ('Why is my train not found?', 'Check the number for typing errors. Special trains and very recent additions may not be in the timetable feed yet; the data is refreshed whenever a new feed is published.'),
       ('Can I see the running days of a train?', 'Yes. Each result shows the days of the week the train runs, shown as M T W T F S S with active days highlighted.'),
  ],
  extra='trains'),

 dict(
  file='pnr-status.html', name='PNR Status', nav='PNR', data_page='', schema='WebPage',
  title='PNR Status Check – 10-Digit PNR Enquiry & Status Codes',
  desc='Check PNR status on the official Indian Railways enquiry. Learn what CNF, RAC, GNWL, RLWL, PQWL, RQWL and CKWL mean and how chart preparation works.',
  kw='PNR status, PNR status check, PNR status online, check PNR status, IRCTC PNR status, railway PNR enquiry, PNR number, PNR meaning, 10 digit PNR, waiting list status, GNWL, RLWL, PQWL, RQWL, CKWL, RAC status, CNF meaning',
  h1='PNR Status Check',
  lead='Check your booking and berth status on the official PNR enquiry, and decode every status code on your ticket.',
  form='''<div class="card"><p>A PNR (Passenger Name Record) is a private 10-digit booking number held by the railway reservation system, so it can be checked only on official channels. We never ask for or store your PNR.</p><p><a class="btn" href="%s" target="_blank" rel="noopener">Open official PNR enquiry</a></p></div>''' % PNR,
  sections=[
   ('How to check PNR status', '''<ol><li>Keep the 10-digit PNR from your ticket or booking SMS ready.</li><li>Open the official enquiry with the button above.</li><li>Enter the PNR and the captcha, then submit.</li><li>Read the booking status, coach and berth, and the chart status.</li></ol>'''),
   ('PNR status codes explained', '''<div class="scroll"><table class="tbl"><tr><th>Code</th><th>Meaning</th></tr>
<tr><td><b>CNF</b></td><td>Confirmed &ndash; coach and berth number are allotted.</td></tr>
<tr><td><b>RAC</b></td><td>Reservation Against Cancellation &ndash; you get a seat to share and travel; a full berth is allotted if others cancel.</td></tr>
<tr><td><b>WL</b></td><td>Waiting list &ndash; no berth yet; it moves up as confirmed tickets are cancelled.</td></tr>
<tr><td><b>GNWL</b></td><td>General Waiting List &ndash; the most common waiting list, with the best chance of confirmation.</td></tr>
<tr><td><b>RLWL</b></td><td>Remote Location Waiting List &ndash; for stations away from the originating station.</td></tr>
<tr><td><b>PQWL</b></td><td>Pooled Quota Waiting List &ndash; for passengers boarding or leaving at intermediate stations that share a pooled quota.</td></tr>
<tr><td><b>RQWL</b></td><td>Request Waiting List &ndash; tickets from request-quota stations.</td></tr>
<tr><td><b>CKWL</b></td><td>Tatkal quota waiting list.</td></tr>
<tr><td><b>RSWL</b></td><td>Roadside Station Waiting List.</td></tr></table></div>
<p class="muted"><small>Quota and waiting-list rules are set by Indian Railways and can change. The final authority is the railway reservation system.</small></p>'''),
   ('Understanding chart preparation', '''<p>The reservation chart is prepared a few hours before departure and decides which waiting-list and RAC tickets get a berth. Check your PNR again after the chart is prepared: tickets that are still waitlisted at that point are normally cancelled automatically and refunded, whereas RAC passengers can still travel.</p>'''),
  ],
  faq=[('What is a PNR number?', 'PNR stands for Passenger Name Record. It is a 10-digit number printed on every reserved ticket that links all passengers on the booking to their journey, class and berth.'),
       ('Do you store my PNR?', 'No. This page never asks for your PNR; it only links to the official enquiry.'),
       ('When is the final chart prepared?', 'Charts are prepared a few hours before the train leaves its originating station. Check the official enquiry for the latest status.'),
       ('What if my ticket is still waitlisted?', 'If a waitlisted e-ticket is not confirmed after chart preparation it is cancelled and the fare is refunded automatically. RAC tickets remain valid for travel.')],
  extra=''),

 dict(
  file='trains-between-stations.html', name='Trains Between Stations', nav='Trains', data_page='between', schema='WebPage',
  title='Trains Between Stations – Direct Trains & Time Table',
  desc='Find all direct trains between two stations in India with departure, arrival, duration and running days. Search {NS}+ stations and {NT}+ trains.',
  kw='trains between stations, train between two stations, trains from one station to another, direct trains list, train search by route, train time table between stations, Indian railway train route, train departure arrival time, train running days, train duration',
  h1='Trains Between Two Stations',
  lead='Choose a start and end station to list every direct train, sorted by departure time, with duration and running days.',
  form='''<form class="f" id="f"><div><label for="from">From</label><input id="from" data-suggest="station" placeholder="Type a station" autocomplete="off" required></div><div><label for="to">To</label><input id="to" data-suggest="station" placeholder="Type a station" autocomplete="off" required></div><div style="display:flex;gap:8px"><button class="btn" type="submit">Search trains</button><button class="btn ghost" type="button" id="swap" title="Swap" aria-label="Swap stations">⇄</button></div></form>''',
  sections=[
   ('How to find trains between two stations', '''<p>Type the first letters of a station name or its code (for example <b>NDLS</b> for New Delhi or <b>HWH</b> for Howrah), pick it from the list, do the same for the destination and press <b>Search trains</b>. Only trains that stop at both stations and visit the first before the second are listed.</p><p>Each result opens the full train page with every halt, arrival and departure time and the days of the week the train runs.</p>'''),
   ('Reading the results', '''<ul class="clean"><li><b>Dep / Arr</b> &ndash; scheduled departure from your start station and arrival at your destination.</li><li><b>Duration</b> &ndash; time between those two stops; <i>+1d</i> means you arrive the next day.</li><li><b>Runs</b> &ndash; days of the week the train operates, starting from its origin.</li></ul><p>For seat or berth availability on a train you have picked, use the <a href="seat-availability.html">seat availability</a> guide.</p>'''),
  ],
  faq=[('How do I find direct trains between two cities?', 'Use the search above with the station names or codes of the two cities. For cities with several stations (such as Delhi or Mumbai) try each station, or open the popular route pages listed below.'),
       ('Does this show trains with a change of train?', 'No. Only direct trains that stop at both stations are shown.'),
       ('Are the departure times live?', 'No, they are scheduled times from the timetable. Delays are published on the official NTES site.')],
  extra='routes'),

 dict(
  file='station-live-status.html', name='Station Live Status', nav='Station', data_page='station', schema='WebPage',
  title='Station Live Status – Trains Arriving & Departing Next',
  desc='See which trains are scheduled to arrive or depart at any railway station in the next 2 to 24 hours. Station time table for {NS}+ Indian Railways stations.',
  kw='station live status, live station status, trains at station, railway station time table, station enquiry, arrival departure board, next trains at station, trains from station today, railway station code, NTES station live',
  h1='Station Live Status & Departure Board',
  lead='Pick a station and a time window to list the trains scheduled to stop there today, sorted by time.',
  form='''<form class="f" id="f"><div><label for="st">Station</label><input id="st" data-suggest="station" placeholder="Type a station" autocomplete="off" required></div><div><label for="win">Next</label><select id="win"><option value="2">2 hours</option><option value="4" selected>4 hours</option><option value="8">8 hours</option><option value="24">24 hours</option></select></div><div><button class="btn" type="submit">Show trains</button></div></form>''',
  sections=[
   ('How the station board works', '''<p>The board compares the current time on your device with the scheduled arrival and departure of every train that halts at the station and keeps only trains that run on today&rsquo;s weekday. Trains that start or end at the station are marked.</p><p>It is a planning aid: delays, cancellations and platform changes are published live on {NTES}. Every station also has its own page with the complete day-wise time table &ndash; see the <a href="all-stations.html">station list</a>.</p>'''),
   ('Useful for', '''<ul class="clean"><li>Knowing how many trains you can catch in the next few hours.</li><li>Checking trains that start from a station and the ones that terminate there.</li><li>Finding the busiest hours before heading to the station.</li></ul>'''),
  ],
  faq=[('Is this a live arrival board?', 'It is a schedule-based board. Actual arrival times can differ; use the official NTES station enquiry for live delays.'),
       ('What is a station code?', 'Every railway station has a short code, for example NDLS for New Delhi, CSMT for Mumbai CSMT and MAS for Chennai Central. You can search by name or by code.'),
       ('Which trains are listed?', 'Trains that halt at the station and run on the current weekday, taken from the timetable feed.')],
  extra='stations'),

 dict(
  file='seat-availability.html', name='Seat Availability', nav='Seats', data_page='', schema='WebPage',
  title='Train Seat Availability – Check Berth & Ticket Status',
  desc='How to check train seat and berth availability on IRCTC: class codes (SL, 3A, 2A, 1A, CC), quotas, waiting list and the advance booking period.',
  kw='train seat availability, seat availability, berth availability, train ticket availability, IRCTC seat availability, check seat availability, train ticket booking, sleeper 3A 2A 1A availability, tatkal quota, waiting list, advance reservation period',
  h1='Train Seat Availability',
  lead='Find the right train here, then check live seat and berth availability on the official IRCTC site.',
  form='''<div class="card"><p>Seat availability is live reservation data held by the railway booking system, so it is shown only on the official site. Pick your train with <a href="trains-between-stations.html">trains between stations</a>, then check availability for your date and class.</p><p><a class="btn" href="%s" target="_blank" rel="noopener">Open IRCTC train search</a></p></div>''' % IRCTC,
  sections=[
   ('How to check seat availability', '''<ol><li>Find the train number and the boarding station with the train search.</li><li>Open IRCTC and enter the From and To station, the date and the quota.</li><li>Press search and open the availability for each class (SL, 3A, 2A, 1A, CC and so on).</li><li>Check the status for the dates around yours; a status such as AVAILABLE, RAC or WL shows your chance of a berth.</li></ol>'''),
   ('Class codes', '''<div class="scroll"><table class="tbl"><tr><th>Code</th><th>Class</th></tr><tr><td>1A</td><td>First AC</td></tr><tr><td>2A</td><td>Second AC (2-tier)</td></tr><tr><td>3A</td><td>Third AC (3-tier)</td></tr><tr><td>3E</td><td>Third AC Economy</td></tr><tr><td>SL</td><td>Sleeper</td></tr><tr><td>CC</td><td>AC Chair Car</td></tr><tr><td>EC</td><td>Executive Chair Car</td></tr><tr><td>2S</td><td>Second Sitting</td></tr></table></div>'''),
   ('Quotas and booking window', '''<ul class="clean"><li><b>GN</b> &ndash; General quota. <b>TQ</b> &ndash; Tatkal. <b>PT</b> &ndash; Premium Tatkal. <b>LD</b> &ndash; Ladies. <b>SS</b> &ndash; Senior citizen / lower berth.</li><li>Advance reservation opens 60 days before the journey date (not counting the travel day) under current railway rules. Rules change, so confirm on IRCTC.</li><li>Waitlisted tickets are not guaranteed. See the <a href="pnr-status.html">PNR status codes</a> to understand GNWL, RLWL and PQWL.</li></ul>'''),
  ],
  faq=[('How can I check seat availability for a train?', 'Open the official IRCTC site, enter your stations, date and quota, and read the availability shown for each class.'),
       ('What does WL mean on a ticket?', 'WL means waiting list: no berth yet. It can still be confirmed if earlier passengers cancel. See the PNR page for details of GNWL, RLWL and PQWL.'),
       ('What is the difference between General and Tatkal quota?', 'General quota opens for advance booking weeks ahead. Tatkal opens one day before the journey at a higher fare for last-minute travel.')],
  extra=''),

 dict(
  file='coach-position.html', name='Coach Position', nav='', data_page='', schema='WebPage',
  title='Train Coach Position – Coach Order, Engine & S1 B1 A1 Guide',
  desc='Find your train coach position before it arrives: how coach codes S1, B1, A1, H1, C1 and D1 work, where the engine sits and how to use NTES.',
  kw='train coach position, coach position of train, coach order, train coach indicator, train rake composition, S1 coach position, B1 coach, A1 coach, H1 first AC coach, general coach position, engine position, where will my coach stop, coach position NTES',
  h1='Train Coach Position',
  lead='Know where your coach stops on the platform before the train comes in.',
  form='''<div class="card"><p>Coach composition changes by rake and day and is published live by the railway. Use NTES or the coach display board on the platform to see exactly where your coach stops.</p><p><a class="btn" href="%s" target="_blank" rel="noopener">Open NTES</a></p></div>''' % NTES,
  sections=[
   ('How to find coach position', '''<ol><li>Open NTES and choose the train enquiry for coach composition (rake position).</li><li>Enter the train number and, if asked, the boarding station.</li><li>Read the coach order from the engine to the last coach and locate your coach number.</li><li>At the station, check the coach indicator board on the platform &ndash; it lists the coach order for the next trains.</li></ol>'''),
   ('What the coach codes mean', '''<div class="scroll"><table class="tbl"><tr><th>Code</th><th>Coach type</th></tr><tr><td>S1, S2 &hellip;</td><td>Sleeper class</td></tr><tr><td>B1, B2 &hellip;</td><td>Third AC (3A)</td></tr><tr><td>A1, A2 &hellip;</td><td>Second AC (2A)</td></tr><tr><td>H1</td><td>First AC (1A)</td></tr><tr><td>C1, C2 &hellip;</td><td>AC chair car</td></tr><tr><td>D1, D2 &hellip;</td><td>Non-AC chair car</td></tr><tr><td>EOG / SLR</td><td>Generator or luggage-and-guard coach at the ends</td></tr></table></div>
<p class="muted"><small>Some trains use different codes; the order shown for your train on NTES is the one to follow.</small></p>'''),
   ('Tips for boarding', '''<ul class="clean"><li>Reach the platform early so you can walk to your coach before the train arrives.</li><li>The engine side is the front of the train; coach numbers normally increase away from it, but check the indicator board.</li><li>Rakes can be swapped at short notice, so re-check on the day of travel.</li></ul>'''),
  ],
  faq=[('How do I find my coach position?', 'Use the NTES coach composition enquiry for your train, or read the coach indicator board on the platform.'),
       ('Is the coach position the same every day?', 'Not always. Rakes can be swapped or coaches added, so the composition can change on any day.'),
       ('Where does the engine stop on the platform?', 'It depends on the station layout and the direction the train arrives from; check the indicator board.')],
  extra=''),

 dict(
  file='train-schedule.html', name='Train Schedule', nav='', data_page='schedule', schema='WebPage',
  title='Train Schedule & Time Table – Route, Halts & Running Days',
  desc='Get the full train schedule: every stop with arrival and departure time, day of journey and running days for {NT}+ Indian Railways trains.',
  kw='train schedule, train time table, train timetable, railway time table, train route, train stoppages, train halts, train running days, train arrival departure time, Indian railway time table, train number search',
  h1='Train Schedule & Time Table',
  lead='Search a train to see its complete schedule: every stop with arrival, departure, day of journey and the days it runs.',
  form='''<form class="f" id="f"><div><label for="train">Train number or name</label><input id="train" data-suggest="train" placeholder="Number or name, e.g. 12951" autocomplete="off" required></div><div><button class="btn" type="submit">Get schedule</button></div></form>''',
  sections=[
   ('What the schedule shows', '''<p>For each train you get the origin and destination, total distance, the number of halts, and a stop-by-stop table with scheduled arrival, scheduled departure and the day of the journey (day 1, day 2&hellip;). The running-day strip shows which weekdays the train operates; days highlighted in blue are running days.</p>'''),
   ('Tips for reading a time table', '''<ul class="clean"><li>Times use the 24-hour clock, so 18:30 is 6:30 pm.</li><li>A &ldquo;Day&rdquo; value of 2 means the stop is on the second calendar day of the journey.</li><li>Running days are given for the day the train leaves its origin; at later stations the weekday may be one or more days after.</li></ul><p>Looking for a route rather than a train? Use <a href="trains-between-stations.html">trains between stations</a>.</p>'''),
  ],
  faq=[('How do I check the time table of a train?', 'Enter the train number or name above. The full stop-by-stop schedule opens with all arrival and departure times.'),
       ('Which days does a train run?', 'The running-day strip shows the weekdays on which the train leaves its origin. Special trains also show the date until which the schedule is valid.'),
       FAQ_LIVE],
  extra='trains'),

 dict(
  file='platform-locator.html', name='Platform Locator', nav='', data_page='', schema='WebPage',
  title='Train Platform Number – How to Find Your Platform',
  desc='Find your train platform number: how platforms are assigned, where to see the platform on NTES and station boards, and why platforms can change.',
  kw='train platform number, platform number of train, find platform, railway platform locator, which platform will my train come, platform number NTES, platform change, station platform enquiry, arrival platform',
  h1='Train Platform Number',
  lead='Find the platform for your train and avoid last-minute changes.',
  form='''<div class="card"><p>Platform numbers are assigned by the station control room on the day and can change at short notice. Check NTES or the station announcements for the latest platform.</p><p><a class="btn" href="%s" target="_blank" rel="noopener">Open NTES</a></p></div>''' % NTES,
  sections=[
   ('How to find the platform', '''<ol><li>Open NTES and choose the station enquiry for the station where you board.</li><li>Look for your train in the list of arrivals and departures and read the platform column.</li><li>Confirm on the large display boards at the station; they are updated as platforms change.</li><li>Listen for the announcement before the train arrives.</li></ol>'''),
   ('Why platforms change', '''<p>Platforms are allotted by the station controller depending on which platforms are free, other trains running late and track work. A train that normally uses platform 1 may therefore be sent to a different platform on a busy day, so re-check about 30 minutes before the scheduled arrival.</p>'''),
   ('Before you go', '''<ul class="clean"><li>Look up your train&rsquo;s time on its <a href="train-schedule.html">schedule page</a> and reach the station early.</li><li>Check the <a href="coach-position.html">coach position</a> so you can wait at the right end of the platform.</li></ul>'''),
  ],
  faq=[('How do I know the platform number of my train?', 'Use the NTES station enquiry, the display boards or the station announcements. Platform numbers are assigned on the day.'),
       ('Can the platform change after it is announced?', 'Yes. Platform changes can happen at short notice, so keep checking until the train arrives.')],
  extra=''),

 dict(
  file='download-app.html', name='Get the App', nav='App', data_page='app', schema='WebPage',
  title='Where Is My Train App – Free Train App for Android & iPhone',
  desc='Install the free Where Is My Train app on Android, iPhone or laptop in seconds. Fast train time table, route and station search that also works offline.',
  kw='where is my train app, train app download, live train status app, free train app, railway app, PNR status app, install train app, train timetable app offline, train enquiry app, PWA train app',
  h1='Get the Where Is My Train App',
  lead='Install it in seconds. It opens full screen, works from your home screen and keeps the core pages available offline.',
  form='''<div class="card"><button class="btn" id="installBtn" style="display:none">Install now</button><p class="muted" id="hint">If the button is hidden, use the steps below for your device.</p></div>''',
  sections=[
   ('Install on your device', '''<div class="two"><div><h3 style="margin-top:0">Android (Chrome)</h3><ol><li>Open this site in Chrome.</li><li>Tap the ⋮ menu.</li><li>Choose <b>Install app</b> or <b>Add to Home screen</b>.</li></ol>
<h3>iPhone / iPad (Safari)</h3><ol><li>Open this site in Safari.</li><li>Tap the Share icon.</li><li>Choose <b>Add to Home Screen</b>.</li></ol>
<h3>Laptop (Chrome / Edge)</h3><ol><li>Click the install icon at the right of the address bar.</li><li>Confirm <b>Install</b>.</li></ol></div>
<div><h3 style="margin-top:0">What you get</h3><ul class="clean"><li>Full-screen app experience</li><li>Faster repeat visits</li><li>Offline access to core pages</li><li>Automatic updates &ndash; no app store needed</li><li>Tiny download compared with a store app</li></ul></div></div>'''),
   ('Why a web app?', '''<p>Where Is My Train is a progressive web app. It installs from your browser, uses very little storage, updates itself and works on Android, iPhone, Windows, Mac and Linux with the same link.</p>'''),
  ],
  faq=[('Is the app free?', 'Yes. There is no charge, no account and no advertising-based sign-up.'),
       ('Do I need the Play Store or App Store?', 'No. Install it directly from your browser using the steps above.'),
       ('Does it work offline?', 'The core pages are cached after your first visit, so they open without a connection. Timetable searches need the data files to have been loaded once.')],
  extra=''),

 dict(
  file='features.html', name='Features', nav='', data_page='', schema='WebPage',
  title='Features – Train Status, PNR, Timetable & Station Tools',
  desc='All tools in one free train app: train time table, trains between stations, station boards, PNR and seat guides, coach position and platform help.',
  kw='train app features, train enquiry tools, train time table tool, station board, trains between stations tool, PNR status guide, coach position guide, free railway tools, Indian railways information',
  h1='Features',
  lead='A complete travel companion for train passengers.',
  form='', sections=[], faq=[], extra='tiles'),

 dict(
  file='about.html', name='About', nav='', data_page='', schema='AboutPage',
  title='About Where Is My Train – Free Train Information Project',
  desc='Where Is My Train is an independent train information site by TGM Global using open Indian Railways timetable data for {NT}+ trains and {NS}+ stations.',
  kw='about where is my train, TGM Global, train information website, open data railway timetable, GTFS Indian Railways, independent train enquiry site',
  h1='About Where Is My Train',
  lead='An independent, free train information project.',
  form='', extra='',
  sections=[
   ('Who we are', '''<p>Where Is My Train is an independent train information project by TGM Global. It is not the official app of any railway, and it is not affiliated with any railway operator or ticketing company.</p><p>Our goal is simple: help travellers find the right train, platform and coach with a fast interface in the language they are comfortable with.</p>'''),
   ('Where the data comes from', '''<p>Timetable tools use the Indian Railways community GTFS feed (unofficial, version {FEED}) with {NT}+ trains, {NS}+ stations and running days, published through the <a href="https://mobilitydatabase.org/" target="_blank" rel="noopener">Mobility Database</a>. The feed is converted into small static files, so every search runs in your browser and nothing you type is sent to a server.</p><p>Because Indian Railways offers no free public live-data feed, live status, PNR, seats, coach position and platforms link to the official NTES and IRCTC sites.</p>'''),
   ('Keeping the timetable fresh', '''<p>When a newer feed is published the site data and every train, station and route page are rebuilt from it, so the schedule stays as current as the open data allows.</p><p>Questions or corrections? Visit <a href="contact.html">Contact</a> or the <a href="faq.html">FAQ</a>.</p>'''),
  ],
  faq=[]),

 dict(
  file='faq.html', name='FAQ', nav='', data_page='', schema='FAQPage',
  title='FAQ – Train Status, Timetable, PNR & App Questions',
  desc='Answers about live train status, train time table accuracy, PNR status, seat availability, coach position, languages and installing the app.',
  kw='train status FAQ, how to check train running status, how to check PNR status, train time table accuracy, is this app official, where is my train questions, free train app help',
  h1='Frequently Asked Questions',
  lead='Quick answers about train status, timetables and this site.',
  form='', sections=[], extra='',
  faq=[
   ('Is the data real-time?', 'No. Timetables come from a community GTFS feed of the Indian Railways schedule (version {FEED}, unofficial) and can change at short notice. Live status, PNR and seats are available on the official NTES and IRCTC sites, which we link to.'),
   ('How do I check live train running status?', 'Search the train on our Live Train Status page to get its route and schedule, then open the official NTES link for the live position and delay on the day of travel.'),
   ('How do I check the time table of a train?', 'Enter the train number or name on the Train Schedule page. Every train also has its own page listing all halts, arrival and departure times and running days.'),
   ('How do I find trains between two stations?', 'Use the Trains Between Stations tool, or open one of the popular route pages. Both list direct trains with departure, arrival, duration and running days.'),
   ('How do I check PNR status?', 'PNR data is private booking data, so use the official PNR enquiry linked on our PNR Status page. That page also explains codes such as CNF, RAC, GNWL, RLWL and PQWL.'),
   ('Where can I check seat availability?', 'On the official IRCTC site. Our Seat Availability page explains class codes and quotas and links to it.'),
   ('How do I find my coach position?', 'Use the NTES coach composition enquiry or the coach indicator board at the station. See our Coach Position guide for what the codes mean.'),
   ('How accurate are the running days and timings?', 'They are as accurate as the open feed. Railways revise timetables during the year and run special trains, so confirm on NTES before travel.'),
   ('How does the language feature work?', 'On your first visit the page opens in your device language using browser translation. Tap the flashing orange button to go back to English, or pick any language from the header.'),
   ('Do I need to create an account?', 'No. There is no sign-up and no login.'),
   ('Can I install it as an app?', 'Yes. See the Get the App page for Android, iPhone and laptop steps.'),
   ('Do you store my PNR or searches?', 'No. We never ask for your PNR and searches run in your browser against static data files.'),
   ('Is this an official railway app?', 'No. It is an independent project and is not affiliated with any railway operator.'),
   ('How often is the timetable updated?', 'Whenever a new version of the open GTFS feed is published and loaded into the site, all train, station and route pages are rebuilt.'),
  ]),

 dict(
  file='contact.html', name='Contact', nav='', data_page='contact', schema='ContactPage',
  title='Contact Where Is My Train – Feedback & Corrections',
  desc='Report a wrong train timing, suggest a feature or send feedback to the Where Is My Train team. Messages open as an issue on our public GitHub project.',
  kw='contact where is my train, report wrong train timing, train app feedback, suggest feature, TGM Global contact',
  h1='Contact Us',
  lead='Send feedback, report a wrong timing or suggest a feature. Your message opens as an issue on our public GitHub project.',
  form='''<div class="card"><form id="f" style="display:grid;gap:12px"><div><label for="name">Your name</label><input id="name" required></div><div><label for="subj">Subject</label><input id="subj" required></div><div><label for="msg">Message</label><textarea id="msg" rows="5" required></textarea></div><div><button class="btn" type="submit">Continue on GitHub</button></div></form>
<p class="muted">A free GitHub account is needed to submit. Please do not post personal or ticket details.</p></div>''',
  sections=[], faq=[], extra=''),

 dict(
  file='privacy-policy.html', name='Privacy Policy', nav='', data_page='', schema='WebPage',
  title='Privacy Policy | Where Is My Train',
  desc='Privacy policy of Where Is My Train: no accounts, no stored searches, language preference in your browser and hosting on GitHub Pages.',
  kw='where is my train privacy policy, train app privacy, no login train app, data privacy',
  h1='Privacy Policy', lead='', form='', faq=[], extra='', legal=True,
  sections=[('What we collect', '<p>We do not require accounts and we do not store the trains or stations you search. Searches run in your browser against static data files.</p>'),
            ('Language and cookies', '<p>We store your language choice in your browser (local storage) and use a translation cookie so pages open in your language. When a non-English language is active, the page loads Google Translate, which is subject to Google&rsquo;s own privacy policy.</p>'),
            ('Hosting', '<p>This site is hosted on GitHub Pages, which may log standard technical data such as IP address for security and operations.</p>'),
            ('Your choices', '<p>Select English from the header or the orange button at any time. Clear your browser data to remove stored preferences.</p>'),
            ('Contact', '<p>Use the <a href="contact.html">contact page</a> for privacy questions.</p>')]),

 dict(
  file='terms.html', name='Terms of Use', nav='', data_page='', schema='WebPage',
  title='Terms of Use | Where Is My Train',
  desc='Terms of use for Where Is My Train: information is for general guidance, the site is independent and not endorsed by any railway operator.',
  kw='where is my train terms, terms of use, train information terms',
  h1='Terms of Use', lead='', form='', faq=[], extra='', legal=True,
  sections=[('Acceptance', '<p>By using this site you agree to these terms.</p>'),
            ('Use of information', '<p>Information is provided for general guidance only and may be delayed or incomplete. Do not rely on it as your only source for travel decisions.</p>'),
            ('Independence', '<p>This is an independent project and is not endorsed by any railway operator. Names and trademarks belong to their owners.</p>'),
            ('Liability', '<p>To the extent permitted by law, we are not liable for losses arising from use of the site.</p>'),
            ('Changes', '<p>We may update these terms; continued use means you accept the updated version.</p>')]),

 dict(
  file='disclaimer.html', name='Disclaimer', nav='', data_page='', schema='WebPage',
  title='Disclaimer | Where Is My Train',
  desc='Disclaimer: timetables come from an unofficial open GTFS feed. Always verify train timings, platforms and bookings with official railway sources.',
  kw='where is my train disclaimer, train timetable disclaimer, unofficial railway data',
  h1='Disclaimer', lead='', form='', faq=[], extra='', legal=True,
  sections=[('Timetable data', '<p>Timetables come from the Indian Railways community GTFS feed (unofficial, version {FEED}) distributed through the Mobility Database. Timings, routes, halts, running days and train numbers may be incomplete or out of date. Only halting stations are included.</p>'),
            ('Verify before travel', '<p>Always confirm train timings, platforms and bookings with official railway sources such as NTES and IRCTC, and with station announcements.</p>'),
            ('No affiliation', '<p>This project is not affiliated with, or endorsed by, any railway or ticketing organisation.</p>')]),
]

HOME = dict(
  title='Where Is My Train – Live Train Status, PNR & Time Table',
  desc='Check live train running status, train time table, PNR status, trains between stations, seat availability and coach position for {NT}+ Indian Railways trains.',
  kw='where is my train, live train status, live train running status, train running status, train time table, train schedule, PNR status, PNR status check, trains between stations, train seat availability, coach position, train platform number, station live status, Indian Railways train enquiry, train enquiry, train route and stoppages, train running days',
  h1='Where Is My Train – Live Train Status, Time Table & PNR',
  lead='Search {NT}+ Indian Railways trains and {NS}+ stations for routes, halts, timings and running days, with one-tap links to official live data. Opens in your own language.',
  faq=[FAQ_LIVE,
       ('How do I check my train time table?', 'Type the train number or name in the search box on this page, or open the complete train list and pick your train. You get every halt with arrival and departure times and the running days.'),
       ('How do I find trains between two stations?', 'Use the Trains Between Stations tool or one of the popular route pages below; both list direct trains with duration and running days.'),
       ('How do I check PNR status and seat availability?', 'Both are private reservation data that only the railway systems hold. Our PNR and seat pages explain every status code and link to the official enquiry.'),
       ('Is Where Is My Train free?', 'Yes. It is free, needs no login and can be installed as an app on your phone or laptop.')],
)

TOOL_ORDER = ['live-train-status.html', 'pnr-status.html', 'trains-between-stations.html', 'station-live-status.html', 'seat-availability.html',
              'coach-position.html', 'train-schedule.html', 'platform-locator.html', 'download-app.html']
TILES = {
 'live-train-status.html': ('🚆', 'Train Status & Timetable', 'Train details and full timetable for {NT}+ trains.'),
 'pnr-status.html': ('🎫', 'PNR Status', 'Open the official PNR enquiry and decode status codes.'),
 'trains-between-stations.html': ('🔎', 'Trains Between Stations', 'Find direct trains between {NS}+ stations.'),
 'station-live-status.html': ('🏟️', 'Station Live Status', 'Scheduled trains stopping at any station in the next hours.'),
 'seat-availability.html': ('💺', 'Seat Availability', 'Check availability on the official IRCTC site.'),
 'coach-position.html': ('🧭', 'Coach Position', 'Find coach position using the official NTES.'),
 'train-schedule.html': ('🗓️', 'Train Schedule', 'Full route, timings and running days.'),
 'platform-locator.html': ('📍', 'Platform Locator', 'Find platform info using the official NTES.'),
 'download-app.html': ('📱', 'Get the App', 'Install the free app on your phone or laptop.'),
}
