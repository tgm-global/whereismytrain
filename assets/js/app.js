(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  /* ---------- Language / auto-translate (Google Translate widget) ---------- */
  var LANGS = [['en', 'English'], ['hi', 'हिन्दी'], ['bn', 'বাংলা'], ['ta', 'தமிழ்'], ['te', 'తెలుగు'], ['mr', 'मराठी'], ['gu', 'ગુજરાતી'], ['kn', 'ಕನ್ನಡ'], ['ml', 'മലയാളം'], ['pa', 'ਪੰਜਾਬੀ'], ['ur', 'اردو'], ['or', 'ଓଡ଼ିଆ'], ['as', 'অসমীয়া'], ['ne', 'नेपाली'], ['ar', 'العربية'], ['fr', 'Français'], ['es', 'Español'], ['de', 'Deutsch'], ['pt', 'Português'], ['ru', 'Русский'], ['zh-CN', '中文'], ['ja', '日本語']];
  function detectLang() {
    var saved = null;
    try { saved = localStorage.getItem('wimt_lang'); } catch (e) {}
    if (saved) return saved;
    var n = ((navigator.languages && navigator.languages[0]) || navigator.language || 'en').replace('_', '-');
    var base = n.split('-')[0].toLowerCase();
    if (n.toLowerCase() === 'zh-tw' || n.toLowerCase() === 'zh-hk') return 'zh-TW';
    if (base === 'zh') return 'zh-CN';
    if (base === 'nb' || base === 'nn') return 'no';
    if (base === 'iw') return 'he';
    return base;
  }
  function setCookie(v) {
    var exp = v ? '' : ';expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'googtrans=' + (v || '') + ';path=/' + exp;
    document.cookie = 'googtrans=' + (v || '') + ';path=/;domain=' + location.hostname + exp;
  }
  function chooseLang(code) {
    try { localStorage.setItem('wimt_lang', code); } catch (e) {}
    setCookie(code === 'en' ? '' : '/en/' + code);
    location.reload();
  }
  var target = detectLang();
  var translated = target !== 'en';
  document.documentElement.lang = 'en';
  if (translated) {
    setCookie('/en/' + target);
    window.gtInit = function () {
      new google.translate.TranslateElement({ pageLanguage: 'en', autoDisplay: false }, 'gt_el');
    };
    var gs = document.createElement('script');
    gs.src = 'https://translate.google.com/translate_a/element.js?cb=gtInit';
    gs.async = true;
    document.head.appendChild(gs);
  } else { setCookie(''); }

  document.addEventListener('DOMContentLoaded', function () {
    var sel = $('#langSel');
    if (sel) {
      sel.innerHTML = LANGS.map(function (l) { return '<option value="' + l[0] + '">' + l[1] + '</option>'; }).join('');
      sel.value = LANGS.some(function (l) { return l[0] === target; }) ? target : 'en';
      sel.addEventListener('change', function () { chooseLang(sel.value); });
    }
    var en = $('#toEn');
    if (en) {
      if (translated) en.classList.add('show');
      en.addEventListener('click', function () { chooseLang('en'); });
    }
    var mb = $('#menuBtn'), nav = $('#mainNav');
    if (mb && nav) mb.addEventListener('click', function () { nav.classList.toggle('open'); });
    initPage();
  });

  /* ---------- PWA ---------- */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      var base = document.documentElement.getAttribute('data-base') || '';
      navigator.serviceWorker.register(base + 'sw.js').catch(function () {});
    });
  }
  var deferred = null;
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault(); deferred = e;
    var b = $('#installBtn'); if (b) b.style.display = 'inline-block';
  });

  /* ---------- data helpers (real open timetable data) ---------- */
  var BASE = document.documentElement.getAttribute('data-base') || '';
  var jc = {};
  function getJSON(p) { return jc[p] || (jc[p] = fetch(BASE + p).then(function (r) { if (!r.ok) throw new Error(p); return r.json(); }).catch(function () { return null; })); }
  function meta() { return getJSON('assets/data/meta.json').then(function (m) { if (m && !m._ix) { m._ix = {}; m.t.forEach(function (t) { m._ix[t[0]] = t; }); } return m; }); }
  function trainStops(no) { return getJSON('assets/data/tr/' + no.slice(0, 3) + '.json').then(function (o) { return o && o[no]; }); }
  function stationRows(code) { return getJSON('assets/data/st/' + code.slice(0, 2).toUpperCase() + '.json').then(function (o) { return (o && o[code]) || []; }); }
  function mm(m) { return m == null ? '--' : ('0' + Math.floor(m / 60) % 24).slice(-2) + ':' + ('0' + m % 60).slice(-2); }
  function dur(m) { return Math.floor(m / 60) + 'h ' + (m % 60) + 'm'; }
  var DN = ['M', 'T', 'W', 'T', 'F', 'S', 'S'], DF = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  function daysHtml(b) { b = b || '1111111'; return '<span class="dys" title="' + (b === '1111111' ? 'Daily' : DF.filter(function (d, i) { return b[i] === '1'; }).join(', ')) + '">' + DN.map(function (d, i) { return '<i class="' + (b[i] === '1' ? 'on' : '') + '">' + d + '</i>'; }).join('') + '</span>'; }
  function until(t) { var u = t[10]; return u ? '<p class="muted"><small>Schedule in the feed is valid until ' + u.slice(6) + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+u.slice(4, 6) - 1] + ' ' + u.slice(0, 4) + ' (special/limited run or feed window). Verify on NTES.</small></p>' : ''; }
  function qp(k) { return new URLSearchParams(location.search).get(k) || ''; }
  var TYPES = { Raj: 'Rajdhani', Shtb: 'Shatabdi', SF: 'Superfast', Exp: 'Express', Mail: 'Mail', Pass: 'Passenger', Drnt: 'Duronto', Garib: 'Garib Rath', Jan: 'Jan Shatabdi', Humsafar: 'Humsafar', Rajya: 'Rajya Rani', VB: 'Vande Bharat', AB: 'Amrit Bharat', Tejas: 'Tejas', MEMU: 'MEMU', DEMU: 'DEMU', EMU: 'EMU', Local: 'Local', Spl: 'Special' };
  function typeName(t) { return TYPES[t] || t; }
  var NOTE = '<p class="note">Timetable: Indian Railways community GTFS feed (unofficial), version 30 Aug 2026. Timings, halts and running days can change at short notice, so confirm with <a href="https://enquiry.indianrail.gov.in/ntes/" target="_blank" rel="noopener">NTES</a> before travel. Only halting stations are listed.</p>';
  var LIVE_NOTE = '<p class="note">Live running position, PNR, seat and platform data are not connected because Indian Railways has no free public data feed. Use the official <a href="https://enquiry.indianrail.gov.in/ntes/" target="_blank" rel="noopener">NTES</a> site for live information.</p>';
  function stName(m, c) { return (m.s[c] || c); }
  function sOpt(m, c) { return stName(m, c) + ' (' + c + ')'; }
  function parseTrain(m, q) { var x = (q || '').match(/\d{5}/); if (x && m._ix[x[0]]) return m._ix[x[0]]; q = (q || '').trim().toLowerCase(); return q.length > 2 ? m.t.filter(function (t) { return t[1].toLowerCase() === q; })[0] : null; }
  function parseStation(m, q) {
    q = (q || '').trim(); var x = q.match(/\(([A-Za-z0-9]+)\)\s*$/); if (x) return x[1].toUpperCase();
    var u = q.toUpperCase(); if (m.s[u]) return u;
    var k = Object.keys(m.s).filter(function (c) { return m.s[c].toLowerCase() === q.toLowerCase(); }); return k[0] || null;
  }
  function suggest() {
    meta().then(function (m) {
      if (!m) return;
      document.querySelectorAll('input[data-suggest]').forEach(function (inp) {
        var dl = document.createElement('datalist'); dl.id = 'dl-' + inp.id; document.body.appendChild(dl); inp.setAttribute('list', dl.id);
        var kind = inp.getAttribute('data-suggest'), keys = kind === 'station' ? Object.keys(m.s) : null;
        inp.addEventListener('input', function () {
          var q = inp.value.trim().toLowerCase(); if (q.length < 2) { dl.innerHTML = ''; return; }
          var out = [];
          if (kind === 'station') {
            keys.forEach(function (c) { if (out.length < 12 && (c.toLowerCase().indexOf(q) === 0 || m.s[c].toLowerCase().indexOf(q) > -1)) out.push(sOpt(m, c)); });
          } else {
            for (var i = 0; i < m.t.length && out.length < 12; i++) { var t = m.t[i]; if (t[0].indexOf(q) === 0 || t[1].toLowerCase().indexOf(q) > -1) out.push(t[0] + ' - ' + t[1]); }
          }
          dl.innerHTML = out.map(function (v) { return '<option value="' + esc(v) + '">'; }).join('');
        });
      });
    });
  }
  function trainLink(t) { return '<a href="live-train-status.html?train=' + t[0] + '"><b>' + t[0] + '</b> ' + esc(t[1]) + '</a>'; }
  var API = window.WIMT_API || '';

  /* ---------- page controllers ---------- */
  function initPage() {
    var page = document.body.getAttribute('data-page'); suggest();
    var fn = { live: live, between: between, station: station, schedule: schedule, app: appPage, contact: contact }[page];
    if (fn) fn();
  }
  function timetable(m, t, stops, all) {
    var rows = stops.map(function (s, i) { return { s: s, i: i }; }).filter(function (r) { return all || r.s[4]; });
    return '<div class="scroll"><table class="tbl"><tr><th>#</th><th>Station</th><th>Arr</th><th>Dep</th><th>Day</th></tr>' + rows.map(function (r, k) {
      return '<tr' + (r.s[4] ? '' : ' class="muted"') + '><td>' + (k + 1) + '</td><td>' + esc(stName(m, r.s[0])) + ' <small class="muted">' + r.s[0] + '</small></td><td>' + mm(r.s[1]) + '</td><td>' + mm(r.s[2]) + '</td><td>' + r.s[3] + '</td></tr>'; }).join('') + '</table></div>';
  }
  function trainView(out, extra) {
    var tin = $('#train');
    return meta().then(function (m) {
      if (!m) { out.innerHTML = '<div class="card empty">Data could not be loaded. Check your connection.</div>'; return; }
      var t = parseTrain(m, tin.value); if (!t) { out.innerHTML = '<div class="card empty">Train not found. Try a 5-digit number such as 12951.</div>'; return; }
      return trainStops(t[0]).then(function (stops) {
        if (!stops) { out.innerHTML = '<div class="card empty">Schedule not available.</div>'; return; }
        var halts = stops.filter(function (s) { return s[4]; }).length;
        out.innerHTML = '<div class="card"><h2 style="margin-top:0">' + t[0] + ' ' + esc(t[1]) + ' <span class="pill">' + esc(typeName(t[2])) + '</span></h2>' +
          '<p>' + esc(stName(m, t[3])) + ' (' + t[5] + ') → ' + esc(stName(m, t[4])) + ' (' + t[6] + ') · ' + t[7] + ' km · ' + halts + ' halts' + (t[8] ? ' · Return train <a href="live-train-status.html?train=' + t[8] + '">' + t[8] + '</a>' : '') + '</p>' +
          '<p><b>Runs on:</b> ' + daysHtml(t[9]) + '</p>' + until(t) + '<div id="xtra"></div>' + (halts < stops.length ? '<label style="display:flex;gap:8px;align-items:center;font-weight:600"><input type="checkbox" id="allst" style="width:auto"> Show passing stations (' + stops.length + ')</label>' : '') + '<div id="tt">' + timetable(m, t, stops, false) + '</div>' + NOTE +
          '<p><a class="btn ghost" href="coach-position.html">Coach position</a> <a class="btn ghost" href="seat-availability.html">Seats</a> <a class="btn ghost" href="pnr-status.html">PNR</a></p></div>';
        if ($('#allst')) $('#allst').addEventListener('change', function (e) { $('#tt').innerHTML = timetable(m, t, stops, e.target.checked); });
        if (extra) extra(t, $('#xtra'));
      });
    });
  }
  function live() {
    var out = $('#out');
    $('#f').addEventListener('submit', function (e) { e.preventDefault(); run(); });
    function run() {
      trainView(out, function (t, box) {
        if (!API) { box.innerHTML = LIVE_NOTE; return; }
        box.innerHTML = '<p class="muted">Fetching live position…</p>';
        fetch(API.replace(/\/$/, '') + '/live?train=' + t[0]).then(function (r) { return r.json(); }).then(function (j) {
          box.innerHTML = '<p><span class="pill ' + (j.delayMin > 5 ? 'warn' : 'ok') + '">' + (j.delayMin > 5 ? 'Late ' + j.delayMin + ' min' : 'On time') + '</span> ' + esc(j.status || '') + (j.updated ? ' <small class="muted">Updated ' + esc(j.updated) + '</small>' : '') + '</p>';
        }).catch(function () { box.innerHTML = LIVE_NOTE; });
      });
    }
    if (qp('train')) { $('#train').value = qp('train'); run(); }
  }
  function schedule() {
    var out = $('#out');
    $('#f').addEventListener('submit', function (e) { e.preventDefault(); run(); });
    function run() { trainView(out); }
    if (qp('train')) { $('#train').value = qp('train'); run(); }
  }
  function between() {
    var out = $('#out');
    function run() {
      out.innerHTML = '<div class="card empty">Searching…</div>';
      meta().then(function (m) {
        if (!m) { out.innerHTML = '<div class="card empty">Data could not be loaded.</div>'; return; }
        var a = parseStation(m, $('#from').value), b = parseStation(m, $('#to').value);
        if (!a || !b || a === b) { out.innerHTML = '<div class="card empty">Pick two different stations from the suggestions.</div>'; return; }
        Promise.all([stationRows(a), stationRows(b)]).then(function (r) {
          var bm = {}; r[1].forEach(function (x) { bm[x[0]] = x; });
          var rs = r[0].filter(function (x) { return bm[x[0]] && bm[x[0]][1] > x[1]; }).map(function (x) {
            var y = bm[x[0]], dep = x[3] != null ? x[3] : x[2], arr = y[2] != null ? y[2] : y[3];
            return { t: m._ix[x[0]], dep: dep % 1440, arr: arr % 1440, d: Math.floor(arr / 1440) - Math.floor(dep / 1440), m: arr - dep };
          }).filter(function (x) { return x.t && x.m > 0; }).sort(function (p, q) { return p.dep - q.dep; });
          out.innerHTML = '<div class="card"><h2 style="margin-top:0">' + esc(stName(m, a)) + ' → ' + esc(stName(m, b)) + ' (' + rs.length + ' trains)</h2>' +
            (rs.length ? '<div class="scroll"><table class="tbl"><tr><th>Train</th><th>Type</th><th>Runs</th><th>Dep</th><th>Arr</th><th>Duration</th></tr>' + rs.map(function (x) {
              return '<tr><td>' + trainLink(x.t) + '</td><td>' + esc(typeName(x.t[2])) + '</td><td>' + daysHtml(x.t[9]) + '</td><td>' + mm(x.dep) + '</td><td>' + mm(x.arr) + (x.d ? ' <small>(+' + x.d + 'd)</small>' : '') + '</td><td>' + dur(x.m) + '</td></tr>'; }).join('') + '</table></div>' : '<p class="empty">No direct trains found in the dataset for this pair.</p>') + NOTE + '</div>';
        });
      });
    }
    $('#f').addEventListener('submit', function (e) { e.preventDefault(); run(); });
    $('#swap').addEventListener('click', function () { var x = $('#from').value; $('#from').value = $('#to').value; $('#to').value = x; });
    if (qp('from') && qp('to')) { meta().then(function (m) { $('#from').value = sOpt(m, qp('from')); $('#to').value = sOpt(m, qp('to')); run(); }); }
  }
  function station() {
    var out = $('#out');
    $('#f').addEventListener('submit', function (e) {
      e.preventDefault(); out.innerHTML = '<div class="card empty">Loading…</div>';
      meta().then(function (m) {
        if (!m) { out.innerHTML = '<div class="card empty">Data could not be loaded.</div>'; return; }
        var c = parseStation(m, $('#st').value); if (!c) { out.innerHTML = '<div class="card empty">Pick a station from the suggestions.</div>'; return; }
        var hrs = +$('#win').value, d = new Date(), now = d.getHours() * 60 + d.getMinutes();
        stationRows(c).then(function (rows) {
          var rs = rows.map(function (x) { var tm = x[3] != null ? x[3] : x[2], diff = tm == null ? 9999 : (tm % 1440 - now + 1440 + 15) % 1440 - 15; return { x: x, tm: tm, diff: diff }; })
            .filter(function (r) {
              if (r.tm == null || r.diff > hrs * 60) return false;
              var t = m._ix[r.x[0]]; if (!t || !t[9]) return true;
              var ev = new Date(d.getTime() + r.diff * 60000); ev.setHours(0, 0, 0, 0);
              var st = new Date(ev.getTime() - Math.floor(r.tm / 1440) * 86400000);   /* date the train started its journey */
              return t[9][(st.getDay() + 6) % 7] === '1';
            }).sort(function (p, q) { return p.diff - q.diff; });
          out.innerHTML = '<div class="card"><h2 style="margin-top:0">' + esc(stName(m, c)) + ' – scheduled in next ' + hrs + ' h <small class="muted">(trains running today)</small></h2>' + (rs.length ? '<div class="scroll"><table class="tbl"><tr><th>Train</th><th>Arr</th><th>Dep</th><th></th></tr>' + rs.map(function (r) {
            var t = m._ix[r.x[0]]; if (!t) return ''; return '<tr><td>' + trainLink(t) + '</td><td>' + mm(r.x[2]) + '</td><td>' + mm(r.x[3]) + '</td><td>' + (r.x[1] === 0 ? '<small>starts</small>' : r.x[1] === r.x[4] - 1 ? '<small>ends</small>' : '') + '</td></tr>'; }).join('') + '</table></div>' : '<p class="empty">No scheduled trains in this window.</p>') +
            '<p class="note">Scheduled times of trains that stop here; only trains running on the day are listed, and delays are not shown. For live arrivals use <a href="https://enquiry.indianrail.gov.in/ntes/" target="_blank" rel="noopener">NTES</a>.</p></div>';
        });
      });
    });
  }
  function appPage() {
    var b = $('#installBtn');
    if (b) b.addEventListener('click', function () { if (deferred) { deferred.prompt(); deferred = null; b.style.display = 'none'; } });
  }
  function contact() {
    $('#f').addEventListener('submit', function (e) {
      e.preventDefault();
      var body = 'Name: ' + $('#name').value + '\n\n' + $('#msg').value;
      window.open('https://github.com/tgm-global/whereismytrain/issues/new?title=' + encodeURIComponent($('#subj').value) + '&body=' + encodeURIComponent(body), '_blank', 'noopener');
    });
  }
})();
