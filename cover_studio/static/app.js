(function () {
  'use strict';

  var SRC_W = 1200, SRC_H = 800, OUT_W = 450, OUT_H = 800, MAX_OVERLAY = 120;
  var COLORS = ['#e53935', '#43a047', '#1e88e5'];
  var BANDS = ['red', 'green', 'blue'];
  var API = '/api/v1/projects';

  function token(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function $(id) { return document.getElementById(id); }
  var el = {
    title: $('title'), overlay: $('overlay'), count: $('overlay-count'),
    xr: $('focal-x-range'), xn: $('focal-x-num'),
    yr: $('focal-y-range'), yn: $('focal-y-num'),
    save: $('save'), status: $('status'), error: $('error'), errorText: $('error-text'),
    reload: $('reload'), list: $('project-list'), newBtn: $('new-project'),
    form: $('editor'), readout: $('crop-readout'),
    preview: $('preview'), overview: $('overview'), stage: $('stage'), marker: $('marker'),
    titleErr: $('title-err'), overlayErr: $('overlay-err'),
    xErr: $('focal-x-err'), yErr: $('focal-y-err')
  };

  var state = {
    id: null, version: null, focalX: 0.5, focalY: 0.5,
    dirty: false, saving: false, projects: [], conflict: null, edits: 0
  };

  // Source image drawn locally once.
  var source = document.createElement('canvas');
  source.width = SRC_W; source.height = SRC_H;
  (function () {
    var c = source.getContext('2d');
    for (var i = 0; i < 3; i++) {
      c.fillStyle = COLORS[i];
      c.fillRect(i * 400, 0, 400, SRC_H);
    }
  })();

  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
  function cropX() { return clamp(Math.floor(state.focalX * SRC_W - OUT_W / 2 + 0.5), 0, SRC_W - OUT_W); }
  function pct(v) { return Math.floor(v * 100 + 0.5); }

  function bandsDescription(x) {
    var parts = [];
    for (var i = 0; i < 3; i++) {
      var lo = Math.max(x, i * 400), hi = Math.min(x + OUT_W, (i + 1) * 400);
      if (hi > lo) parts.push(BANDS[i] + ' ' + (hi - lo) + 'px');
    }
    return parts.join(', ');
  }

  function setStatus(text) { el.status.textContent = text; }

  function clearFieldErrors() {
    el.titleErr.textContent = ''; el.overlayErr.textContent = '';
    el.xErr.textContent = ''; el.yErr.textContent = '';
  }
  function showError(msg, withReload) {
    el.errorText.textContent = msg;
    el.reload.hidden = !withReload;
    el.error.hidden = false;
  }
  function clearError() {
    el.error.hidden = true; el.errorText.textContent = ''; el.reload.hidden = true;
    state.conflict = null;
  }

  function updateSaveEnabled() { el.save.disabled = state.saving; }

  function markDirty() {
    state.edits += 1;
    state.dirty = true;
    if (!state.saving) setStatus('Unsaved changes');
  }

  function wrapLines(ctx, text, maxW) {
    var words = text.split(' '), lines = [], line = '';
    function pushLong(w) {
      var chunk = '';
      for (var k = 0; k < w.length; k++) {
        if (ctx.measureText(chunk + w[k]).width > maxW && chunk) { lines.push(chunk); chunk = ''; }
        chunk += w[k];
      }
      return chunk;
    }
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (!w) continue;
      var test = line ? line + ' ' + w : w;
      if (ctx.measureText(test).width <= maxW) { line = test; continue; }
      if (line) lines.push(line);
      line = ctx.measureText(w).width > maxW ? pushLong(w) : w;
    }
    if (line) lines.push(line);
    return lines;
  }

  function drawPreview() {
    var x = cropX(), ctx = el.preview.getContext('2d');
    ctx.clearRect(0, 0, OUT_W, OUT_H);
    ctx.drawImage(source, x, 0, OUT_W, OUT_H, 0, 0, OUT_W, OUT_H);
    var text = el.overlay.value;
    if (text) {
      var size = 40, lh = 48;
      ctx.font = 'bold ' + size + 'px system-ui, Arial, sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      var lines = wrapLines(ctx, text, OUT_W - 48);
      ctx.fillStyle = token('--on-media');
      ctx.shadowColor = 'rgba(0,0,0,0.85)'; ctx.shadowBlur = 8;
      ctx.shadowOffsetX = 2; ctx.shadowOffsetY = 2;
      var y = OUT_H - 40 - (lines.length - 1) * lh;
      for (var i = 0; i < lines.length; i++) ctx.fillText(lines[i], OUT_W / 2, y + i * lh);
      ctx.shadowBlur = 0; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0;
    }
    el.preview.setAttribute('aria-label', 'Preview of crop at x ' + x + ', 450 by 800. Bands: ' +
      bandsDescription(x) + (text ? '. Overlay text: ' + text : '. No overlay text'));
  }

  function drawOverview() {
    var x = cropX(), ctx = el.overview.getContext('2d');
    ctx.drawImage(source, 0, 0);
    ctx.fillStyle = token('--scrim');
    ctx.fillRect(0, 0, x, SRC_H);
    ctx.fillRect(x + OUT_W, 0, SRC_W - x - OUT_W, SRC_H);
    ctx.strokeStyle = token('--on-media'); ctx.lineWidth = 6;
    ctx.strokeRect(x + 3, 3, OUT_W - 6, SRC_H - 6);
    el.overview.setAttribute('aria-label', 'Source overview 1200 by 800 with crop rectangle at x ' + x +
      ', width 450. Bands in crop: ' + bandsDescription(x));
  }

  function render() {
    var x = cropX();
    var px = pct(state.focalX), py = pct(state.focalY);
    if (document.activeElement !== el.xn) el.xn.value = px;
    if (document.activeElement !== el.yn) el.yn.value = py;
    el.xr.value = px; el.yr.value = py;
    el.marker.style.left = (state.focalX * 100) + '%';
    el.marker.style.top = (state.focalY * 100) + '%';
    el.marker.setAttribute('aria-valuenow', px);
    el.marker.setAttribute('aria-valuetext', 'X ' + px + ' percent, Y ' + py + ' percent');
    el.readout.textContent = 'crop x=' + x + ' y=0 w=' + OUT_W + ' h=' + OUT_H;
    el.count.textContent = el.overlay.value.length + ' / ' + MAX_OVERLAY;
    drawPreview();
    drawOverview();
  }

  function setFocal(axis, pctValue) {
    if (typeof pctValue !== 'number' || !isFinite(pctValue)) return;
    var v = clamp(Math.floor(pctValue + 0.5), 0, 100) / 100;
    if (axis === 'x') state.focalX = v; else state.focalY = v;
    markDirty();
    render();
  }

  function onNumberInput(axis, input) {
    var raw = input.value;
    if (raw === '') return;
    setFocal(axis, Number(raw));
  }

  function stepKey(e, axis, getPct) {
    var d = 0;
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') d = 1;
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') d = -1;
    else if (e.key === 'PageUp') d = 10;
    else if (e.key === 'PageDown') d = -10;
    else return false;
    e.preventDefault();
    setFocal(axis, getPct(axis) + d);
    return true;
  }
  function curPct(axis) { return pct(axis === 'x' ? state.focalX : state.focalY); }

  // Range / number page keys (arrows are native for these, only add paging).
  [[el.xr, 'x'], [el.xn, 'x'], [el.yr, 'y'], [el.yn, 'y']].forEach(function (p) {
    p[0].addEventListener('keydown', function (e) {
      if (e.key === 'PageUp' || e.key === 'PageDown') stepKey(e, p[1], curPct);
    });
  });
  el.xr.addEventListener('input', function () { setFocal('x', Number(el.xr.value)); });
  el.yr.addEventListener('input', function () { setFocal('y', Number(el.yr.value)); });
  el.xn.addEventListener('input', function () { onNumberInput('x', el.xn); });
  el.yn.addEventListener('input', function () { onNumberInput('y', el.yn); });
  el.xn.addEventListener('blur', render);
  el.yn.addEventListener('blur', render);

  // Marker: keyboard and pointer.
  el.marker.addEventListener('keydown', function (e) {
    var d = 0, axis = 'x';
    switch (e.key) {
      case 'ArrowRight': d = 1; break;
      case 'ArrowLeft': d = -1; break;
      case 'ArrowUp': d = -1; axis = 'y'; break;
      case 'ArrowDown': d = 1; axis = 'y'; break;
      case 'PageUp': d = -10; axis = 'y'; break;
      case 'PageDown': d = 10; axis = 'y'; break;
      default: return;
    }
    if (e.shiftKey && (e.key === 'PageUp' || e.key === 'PageDown')) { axis = 'x'; d = -d; }
    e.preventDefault();
    setFocal(axis, curPct(axis) + d);
  });

  function pointerFocal(e) {
    var r = el.overview.getBoundingClientRect();
    if (!r.width || !r.height) return;
    setFocal('x', ((e.clientX - r.left) / r.width) * 100);
    setFocal('y', ((e.clientY - r.top) / r.height) * 100);
  }
  var dragging = false;
  el.stage.addEventListener('pointerdown', function (e) {
    if (e.button !== undefined && e.button !== 0) return;
    dragging = true;
    try { el.stage.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    el.marker.focus();
    pointerFocal(e);
    e.preventDefault();
  });
  el.stage.addEventListener('pointermove', function (e) { if (dragging) pointerFocal(e); });
  function endDrag() { dragging = false; }
  el.stage.addEventListener('pointerup', endDrag);
  el.stage.addEventListener('pointercancel', endDrag);

  el.title.addEventListener('input', markDirty);
  el.overlay.addEventListener('input', function () { markDirty(); render(); });

  // API
  function api(method, url, body) {
    var opts = { method: method, headers: { 'Accept': 'application/json' }, credentials: 'same-origin' };
    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (res) {
      return res.text().then(function (t) {
        var data = null;
        try { data = t ? JSON.parse(t) : null; } catch (e) { data = null; }
        if (!res.ok) {
          var err = new Error((data && data.error && data.error.message) || ('Request failed (' + res.status + ')'));
          err.status = res.status;
          err.error = data && data.error ? data.error : null;
          throw err;
        }
        return data;
      });
    });
  }

  function applyProject(p) {
    state.id = p.id; state.version = p.version;
    state.focalX = p.focal_x; state.focalY = p.focal_y;
    el.title.value = p.title;
    el.overlay.value = p.overlay_text;
    state.dirty = false;
    clearFieldErrors();
    render();
    renderList();
  }

  function newProject() {
    state.id = null; state.version = null;
    state.focalX = 0.5; state.focalY = 0.5;
    el.title.value = ''; el.overlay.value = '';
    state.dirty = false;
    clearFieldErrors(); clearError();
    setStatus('New project, not saved');
    render(); renderList();
    el.title.focus();
  }

  function renderList() {
    while (el.list.firstChild) el.list.removeChild(el.list.firstChild);
    if (!state.projects.length) {
      var li0 = document.createElement('li');
      li0.textContent = 'No projects yet';
      el.list.appendChild(li0);
      return;
    }
    state.projects.forEach(function (p) {
      var li = document.createElement('li');
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = p.title;
      b.setAttribute('data-project-id', String(p.id));
      if (p.id === state.id) b.setAttribute('aria-current', 'true');
      b.addEventListener('click', function () { openProject(p.id); });
      li.appendChild(b);
      el.list.appendChild(li);
    });
  }

  function loadList() {
    return api('GET', API).then(function (d) { state.projects = d.projects || []; renderList(); });
  }

  function confirmDiscard() {
    return !state.dirty || window.confirm('Discard unsaved changes?');
  }

  function openProject(id) {
    if (id === state.id && !state.dirty) return;
    if (!confirmDiscard()) return;
    clearError();
    setStatus('Loading');
    api('GET', API + '/' + id).then(function (p) {
      applyProject(p); setStatus('Saved');
    }).catch(function (e) { showError('Could not load project: ' + e.message, false); setStatus('Load failed'); });
  }

  function showFieldErrors(fields) {
    clearFieldErrors();
    if (!fields) return;
    if (fields.title) el.titleErr.textContent = String(fields.title);
    if (fields.overlay_text) el.overlayErr.textContent = String(fields.overlay_text);
    if (fields.focal_x) el.xErr.textContent = String(fields.focal_x);
    if (fields.focal_y) el.yErr.textContent = String(fields.focal_y);
  }

  function save() {
    if (state.saving) return;
    clearError(); clearFieldErrors();
    var title = el.title.value.trim();
    if (!title) {
      el.titleErr.textContent = 'Title is required';
      showError('Title is required.', false);
      el.title.focus();
      return;
    }
    var body = {
      title: title, overlay_text: el.overlay.value, preset: 'reel_9_16',
      focal_x: state.focalX, focal_y: state.focalY
    };
    var isNew = state.id === null;
    var req;
    if (isNew) req = api('POST', API, body);
    else { body.version = state.version; req = api('PUT', API + '/' + state.id, body); }
    var sentEdits = state.edits;
    state.saving = true; updateSaveEnabled(); setStatus('Saving');
    req.then(function (p) {
      state.saving = false; updateSaveEnabled();
      if (state.edits !== sentEdits) {
        // Edits were typed while saving: keep them, adopt only id and version.
        state.id = p.id; state.version = p.version;
        state.dirty = true;
        setStatus('Saved earlier version; newer edits are unsaved');
        return loadList();
      }
      applyProject(p);
      setStatus('Saved');
      return loadList();
    }).catch(function (e) {
      state.saving = false; updateSaveEnabled();
      setStatus('Unsaved changes');
      if (e.status === 409 && e.error && e.error.details && e.error.details.current) {
        state.conflict = e.error.details.current;
        showError('Version conflict: the stored project is now "' + String(state.conflict.title) +
          '" (version ' + state.conflict.version + '). Your edits were not saved.', true);
      } else if (e.status === 400 && e.error && e.error.details) {
        showFieldErrors(e.error.details.fields);
        showError(e.message, false);
      } else {
        showError('Save failed: ' + e.message, false);
      }
    });
  }

  el.form.addEventListener('submit', function (e) { e.preventDefault(); save(); });
  el.newBtn.addEventListener('click', function () { if (confirmDiscard()) newProject(); });
  el.reload.addEventListener('click', function () {
    var cur = state.conflict;
    function done(p) { clearError(); applyProject(p); setStatus('Saved'); loadList(); }
    if (cur) { done(cur); return; }
    api('GET', API + '/' + state.id).then(done).catch(function (e) { showError('Reload failed: ' + e.message, false); });
  });

  window.addEventListener('beforeunload', function (e) {
    if (state.dirty) { e.preventDefault(); e.returnValue = ''; }
  });

  // Init
  render();
  loadList().then(function () {
    if (state.projects.length) {
      return api('GET', API + '/' + state.projects[0].id).then(function (p) { applyProject(p); setStatus('Saved'); });
    }
    newProject();
  }).catch(function (e) {
    showError('Could not load projects: ' + e.message, false);
    setStatus('Load failed');
  });
})();
