/* Admin: validate a GTFS zip in the browser, upload it to the GitHub repo, and let the GitHub Action rebuild the site.
   Nothing is sent anywhere except api.github.com. The token stays in this browser (sessionStorage unless "remember" is ticked). */
(function () {
  'use strict';
  var $ = function (s) { return document.querySelector(s); };
  var form = $('#af'); if (!form) return;
  var logBox = $('#log'), zipInfo = $('#zipinfo'), file = null, checked = null;
  var WF = 'update-feed.yml', TARGET = 'feed/gtfs.zip';

  function log(msg, cls) { var d = document.createElement('div'); d.className = cls || ''; d.textContent = msg; logBox.appendChild(d); logBox.scrollTop = logBox.scrollHeight; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function store(k, v, persist) { try { (persist ? localStorage : sessionStorage).setItem(k, v); } catch (e) {} }
  function load(k) { try { return localStorage.getItem(k) || sessionStorage.getItem(k) || ''; } catch (e) { return ''; } }

  /* ---------- saved settings ---------- */
  $('#repo').value = load('wimt_repo') || form.getAttribute('data-repo') || '';
  $('#branch').value = load('wimt_branch') || 'main';
  $('#token').value = load('wimt_token');
  $('#remember').checked = !!(function () { try { return localStorage.getItem('wimt_token'); } catch (e) { return ''; } })();

  /* ---------- minimal ZIP reader (central directory + deflate-raw via DecompressionStream) ---------- */
  var u16 = function (v, o) { return v.getUint16(o, true); }, u32 = function (v, o) { return v.getUint32(o, true); };
  async function readZip(f) {
    var tl = Math.min(f.size, 65557 + 22);
    var tail = new DataView(await f.slice(f.size - tl).arrayBuffer()), e = -1;
    for (var i = tl - 22; i >= 0; i--) { if (tail.getUint32(i, true) === 0x06054b50) { e = i; break; } }
    if (e < 0) throw new Error('This is not a valid ZIP file.');
    var total = u16(tail, e + 10), cdSize = u32(tail, e + 12), cdOff = u32(tail, e + 16);
    if (cdOff === 0xFFFFFFFF || total === 0xFFFF) throw new Error('ZIP64 archives cannot be checked in the browser. You can still upload; the server-side build will check it.');
    var cd = new DataView(await f.slice(cdOff, cdOff + cdSize).arrayBuffer()), p = 0, dec = new TextDecoder(), entries = {};
    for (var n = 0; n < total; n++) {
      if (cd.getUint32(p, true) !== 0x02014b50) throw new Error('The ZIP directory is corrupt.');
      var nl = u16(cd, p + 28), el = u16(cd, p + 30), cl = u16(cd, p + 32);
      entries[dec.decode(new Uint8Array(cd.buffer, p + 46, nl))] = { method: u16(cd, p + 10), csize: u32(cd, p + 20), usize: u32(cd, p + 24), off: u32(cd, p + 42) };
      p += 46 + nl + el + cl;
    }
    return { file: f, entries: entries };
  }
  function find(zip, base) { return Object.keys(zip.entries).filter(function (n) { return n === base || n.slice(-(base.length + 1)) === '/' + base; })[0]; }
  async function readEntry(zip, name, max) {
    var e = zip.entries[name], lh = new DataView(await zip.file.slice(e.off, e.off + 30).arrayBuffer());
    var start = e.off + 30 + u16(lh, 26) + u16(lh, 28), blob = zip.file.slice(start, start + e.csize);
    if (e.method === 0) return blob.text();
    if (e.method === 8) {
      if (typeof DecompressionStream === 'undefined') throw new Error('This browser cannot read ZIP contents. Use a current Chrome, Edge, Firefox or Safari.');
      return new Response(blob.stream().pipeThrough(new DecompressionStream('deflate-raw'))).text();
    }
    throw new Error('Unsupported ZIP compression method ' + e.method);
  }
  function csvRow(text) {
    var lines = text.replace(/^﻿/, '').split(/\r?\n/), split = function (l) { var o = [], c = '', q = false; for (var i = 0; i < l.length; i++) { var ch = l[i]; if (ch === '"') { if (q && l[i + 1] === '"') { c += '"'; i++; } else q = !q; } else if (ch === ',' && !q) { o.push(c); c = ''; } else c += ch; } o.push(c); return o; };
    if (lines.length < 2) return {}; var h = split(lines[0]), v = split(lines[1]), r = {}; h.forEach(function (k, i) { r[k.trim()] = v[i]; }); return r;
  }
  function lineCount(t) { return Math.max(0, t.split('\n').filter(function (x) { return x.trim(); }).length - 1); }

  async function inspect(f) {
    zipInfo.innerHTML = '<p class="muted">Checking the ZIP…</p>'; checked = null;
    var rows = [], ok = true;
    try {
      var zip = await readZip(f), need = ['stops.txt', 'stop_times.txt', 'trips.txt', 'routes.txt'];
      need.forEach(function (n) { var has = !!find(zip, n); if (!has) ok = false; rows.push('<li>' + (has ? '✅' : '❌') + ' <code>' + n + '</code>' + (has ? ' <small class="muted">' + Math.round(zip.entries[find(zip, n)].usize / 1024).toLocaleString() + ' KB</small>' : ' is missing') + '</li>'); });
      var extra = '';
      var fi = find(zip, 'feed_info.txt');
      if (fi) { var r = csvRow(await readEntry(zip, fi)); extra += '<p><b>Feed version:</b> ' + esc(r.feed_version || '–') + ' &nbsp; <b>Valid:</b> ' + esc(r.feed_start_date || '–') + ' → ' + esc(r.feed_end_date || '–') + (r.feed_publisher_name ? ' &nbsp; <b>Publisher:</b> ' + esc(r.feed_publisher_name) : '') + '</p>'; }
      if (ok) {
        var tr = lineCount(await readEntry(zip, find(zip, 'trips.txt'))), st = lineCount(await readEntry(zip, find(zip, 'stops.txt')));
        extra += '<p><b>Trips:</b> ' + tr.toLocaleString() + ' &nbsp; <b>Stops:</b> ' + st.toLocaleString() + '</p>';
      }
      zipInfo.innerHTML = '<ul class="clean" style="list-style:none;padding-left:0">' + rows.join('') + '</ul>' + extra + (ok ? '<p><span class="pill ok">Looks like a valid GTFS feed</span></p>' : '<p><span class="pill bad">Not a GTFS feed – required files are missing</span></p>');
      checked = ok;
    } catch (err) {
      zipInfo.innerHTML = '<p><span class="pill warn">' + esc(err.message) + '</span></p>'; checked = null;
    }
    if (f.size > 50 * 1024 * 1024) zipInfo.innerHTML += '<p class="note">This file is larger than 50 MB. GitHub accepts uploads up to 100 MB through this method; for bigger feeds use the feed URL option below.</p>';
  }

  $('#zip').addEventListener('change', function (e) {
    file = e.target.files[0] || null;
    $('#fname').textContent = file ? file.name + ' (' + (file.size / 1048576).toFixed(1) + ' MB)' : '';
    if (file) inspect(file); else zipInfo.innerHTML = '';
  });

  /* ---------- GitHub API ---------- */
  function cfg() {
    var repo = $('#repo').value.trim().replace(/^https?:\/\/github\.com\//, '').replace(/\.git$/, '').replace(/\/$/, ''), token = $('#token').value.trim(), branch = $('#branch').value.trim() || 'main';
    if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) throw new Error('Enter the repository as owner/name, for example tgm-global/whereismytrain.');
    if (!token) throw new Error('Enter your GitHub token.');
    store('wimt_repo', repo, true); store('wimt_branch', branch, true);
    try { localStorage.removeItem('wimt_token'); sessionStorage.removeItem('wimt_token'); } catch (e) {}
    store('wimt_token', token, $('#remember').checked);
    return { repo: repo, token: token, branch: branch };
  }
  async function gh(c, path, opt) {
    var r = await fetch('https://api.github.com' + path, Object.assign({}, opt, { headers: Object.assign({ Authorization: 'Bearer ' + c.token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' }, (opt && opt.headers) || {}) }));
    var j = null; try { j = await r.json(); } catch (e) {}
    if (!r.ok && r.status !== 404) throw new Error('GitHub said ' + r.status + ': ' + ((j && j.message) || r.statusText));
    return { status: r.status, json: j };
  }
  function b64(f) { return new Promise(function (res, rej) { var fr = new FileReader(); fr.onload = function () { res(String(fr.result).split(',')[1]); }; fr.onerror = function () { rej(new Error('Could not read the file.')); }; fr.readAsDataURL(f); }); }
  function busy(b) { $('#go').disabled = b; $('#go2').disabled = b; }

  async function watch(c, since) {
    log('Waiting for the site rebuild to start…');
    for (var i = 0; i < 90; i++) {
      await new Promise(function (r) { setTimeout(r, 8000); });
      var r;
      try { r = await gh(c, '/repos/' + c.repo + '/actions/workflows/' + WF + '/runs?per_page=5'); } catch (e) { log('Cannot read workflow status (' + e.message + '). Check the Actions tab on GitHub.', 'warn'); return; }
      var run = ((r.json && r.json.workflow_runs) || []).filter(function (x) { return new Date(x.created_at).getTime() >= since - 60000; })[0];
      if (!run) { if (i > 8) { log('No rebuild run found yet. Open the Actions tab on GitHub to check.', 'warn'); return; } continue; }
      if (run.status === 'completed') {
        if (run.conclusion === 'success') log('✅ Rebuild finished. GitHub Pages will publish the new data within a minute or two: ' + run.html_url, 'ok');
        else log('❌ Rebuild ' + run.conclusion + '. See the log: ' + run.html_url, 'bad');
        return;
      }
      if (i % 3 === 0) log('Rebuild is ' + run.status + '… (' + run.html_url + ')');
    }
    log('Still running after 12 minutes – check the Actions tab.', 'warn');
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault(); logBox.innerHTML = '';
    try {
      if (!file) throw new Error('Choose the GTFS .zip file first.');
      if (checked === false) throw new Error('This ZIP is missing required GTFS files, so it was not uploaded.');
      var c = cfg(); busy(true);
      log('Checking repository access…');
      var rp = await gh(c, '/repos/' + c.repo);
      if (rp.status === 404) throw new Error('Repository not found, or the token has no access to it.');
      if (rp.json && rp.json.permissions && !rp.json.permissions.push) throw new Error('The token can read but not write to this repository.');
      var cur = await gh(c, '/repos/' + c.repo + '/contents/' + TARGET + '?ref=' + encodeURIComponent(c.branch));
      log('Encoding ' + (file.size / 1048576).toFixed(1) + ' MB…');
      var content = await b64(file), since = Date.now();
      log('Uploading to ' + TARGET + ' …');
      var body = { message: 'Upload new GTFS feed (' + file.name + ')', content: content, branch: c.branch };
      if (cur.status === 200 && cur.json && cur.json.sha) body.sha = cur.json.sha;
      var up = await gh(c, '/repos/' + c.repo + '/contents/' + TARGET, { method: 'PUT', body: JSON.stringify(body) });
      if (up.status === 404) throw new Error('Upload failed: branch or path not found.');
      log('✅ Uploaded. The GitHub Action now converts the feed and rebuilds every page.', 'ok');
      await watch(c, since);
    } catch (err) { log('❌ ' + err.message, 'bad'); } finally { busy(false); }
  });

  $('#go2').addEventListener('click', async function () {
    logBox.innerHTML = '';
    try {
      var url = $('#feedurl').value.trim(); if (!/^https:\/\//.test(url)) throw new Error('Paste a direct https:// link to the feed .zip.');
      var c = cfg(); busy(true);
      var since = Date.now();
      var r = await gh(c, '/repos/' + c.repo + '/actions/workflows/' + WF + '/dispatches', { method: 'POST', body: JSON.stringify({ ref: c.branch, inputs: { feed_url: url } }) });
      if (r.status === 404) throw new Error('Workflow ' + WF + ' not found on this branch. Upload the project files including .github/workflows first.');
      log('✅ Rebuild requested. GitHub downloads the feed and updates the site.', 'ok');
      await watch(c, since);
    } catch (err) { log('❌ ' + err.message, 'bad'); } finally { busy(false); }
  });
})();
