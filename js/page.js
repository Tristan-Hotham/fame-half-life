/* The half-life of fame: an interactive decay chart (median attention by months since death, by group) and a small
 * MapLibre world map of median attention two to three years after death by country of citizenship.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const small = matchMedia('(max-width:700px)').matches;
  const root = document.documentElement;
  const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  // fixed colour per group (never by rank); light and dark steps
  const COL = {
    'family:Performers': ['#B3202A', '#F07C78'], 'family:Sport': ['#2F7FB8', '#7DB7E3'], 'family:Politics and law': ['#D08A1E', '#E8B25C'],
    'family:Science and academia': ['#3B8B5A', '#79C496'], 'family:Writers and artists': ['#7A4FA0', '#B597D6'], 'family:Journalism and media': ['#C2577F', '#E596B4'],
    'family:Religion': ['#2E9C9C', '#6CCACA'], 'family:Business': ['#8A6A3B', '#C9A673'], 'family:Military': ['#55606B', '#A3AEBA'], 'family:Other': ['#9A9283', '#C9C2B4'],
    'ageb:under 50': ['#7F1D22', '#F2A39C'], 'ageb:50 to 64': ['#B3202A', '#E77B73'], 'ageb:65 to 79': ['#D3735F', '#C9604D'], 'ageb:80 to 89': ['#2F7FB8', '#7DB7E3'], 'ageb:90 and over': ['#173B5C', '#B3CBE0'],
    'sex2:men': ['#2F7FB8', '#7DB7E3'], 'sex2:women': ['#B3202A', '#F07C78'],
    'lang:English-speaking': ['#B3202A', '#F07C78'], 'lang:other': ['#2F7FB8', '#7DB7E3']
  };
  const GROUPS = {
    family: ['Performers', 'Sport', 'Politics and law', 'Science and academia', 'Writers and artists', 'Journalism and media', 'Religion', 'Business', 'Military', 'Other'],
    ageb: ['under 50', '50 to 64', '65 to 79', '80 to 89', '90 and over'], sex2: ['men', 'women'], lang: ['English-speaking', 'other']
  };
  const DEF = { family: ['Performers', 'Sport', 'Politics and law', 'Science and academia'], ageb: ['under 50', '65 to 79', '90 and over'], sex2: ['men', 'women'], lang: ['English-speaking', 'other'] };
  const NAMES = { 'English-speaking': 'English-speaking country', other: 'other country' };
  const MAXON = 5;
  let S = null, dim = 'family', scale = 'log', win = 60, on = {};
  for (const d in DEF) on[d] = DEF[d].slice();
  const col = k => (COL[k] || ['#888', '#aaa'])[isDark() ? 1 : 0];
  document.getElementById('theme').addEventListener('click', () => { root.dataset.theme = isDark() ? 'light' : 'dark'; draw(); });

  // ---------------- chart
  const plot = document.getElementById('plot'), tip = document.getElementById('tip');
  const NS = 'http://www.w3.org/2000/svg';
  const el = (n, a, p) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  function chips() {
    const c = document.getElementById('chips'); c.innerHTML = '';
    GROUPS[dim].forEach(g => {
      const k = dim + ':' + g, st = S.groups[k]; if (!st) return;
      const b = document.createElement('button'); b.className = 'chip'; b.style.setProperty('--c', col(k));
      b.setAttribute('aria-pressed', on[dim].includes(g)); b.innerHTML = `<i></i>${esc(NAMES[g] || g)} <span style="color:var(--muted)">${fmt(st.n)}</span>`;
      b.addEventListener('click', () => {
        const a = on[dim], i = a.indexOf(g);
        if (i >= 0) a.splice(i, 1); else { a.push(g); if (a.length > MAXON) a.shift(); }
        chips(); draw(); table();
      });
      c.appendChild(b);
    });
  }
  function table() {
    const t = document.getElementById('gtab');
    let h = '<tr><th>Group</th><th>People</th><th>Median peak</th><th>A year on</th><th>2 to 3 years on</th><th class="xs">Above before</th><th class="xs">Slow half-life</th></tr>';
    const row = (lab, s) => `<tr><td>${lab}</td><td>${fmt(s.n)}</td><td>${s.peak.toFixed(1)}x</td><td>${s.y1.toFixed(2)}</td><td>${s.lr.toFixed(2)} <span class="xs" style="color:var(--muted)">(${s.lr_lo.toFixed(2)} to ${s.lr_hi.toFixed(2)})</span></td><td class="xs">${Math.round(s.above)}%</td><td class="xs">${s.hl == null ? 'n/a' : s.hl.toFixed(1) + ' mo'}</td></tr>`;
    GROUPS[dim].forEach(g => { const s = S.groups[dim + ':' + g]; if (s) h += row(`<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:${col(dim + ':' + g)};margin-right:5px"></span>${esc(NAMES[g] || g)}`, s); });
    const A = S.all; h += row('Everyone', { n: A.n, peak: A.peak, y1: A.y1, lr: A.lr, lr_lo: A.lr_lo, lr_hi: A.lr_hi, above: A.above, hl: A.hl });
    t.innerHTML = h;
  }
  function draw() {
    if (!S) return;
    plot.querySelectorAll('svg').forEach(s => s.remove());
    const W = plot.clientWidth, H = plot.clientHeight, m = { l: 46, r: small ? 44 : 150, t: 10, b: 34 };
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Median attention by months since death' }); plot.insertBefore(svg, tip);
    const k0 = -12, k1 = win;
    const keys = on[dim].map(g => dim + ':' + g).filter(k => S.curves[k]);
    const all = S.curves['All'];
    let ymax = 1.5, ymin = 0.75;
    [...keys, 'All'].forEach(k => { const c = S.curves[k]; c.k.forEach((kk, i) => { if (kk >= k0 && kk <= k1) { ymax = Math.max(ymax, c.m[i]); ymin = Math.min(ymin, c.m[i]); } }); });
    ymax *= scale === 'log' ? 1.25 : 1.06; ymin = scale === 'log' ? Math.min(0.75, ymin * 0.95) : 0;
    const x = k => m.l + (k - k0) / (k1 - k0) * (W - m.l - m.r);
    const ly = v => Math.log(Math.max(v, 0.01));
    const y = scale === 'log' ? v => m.t + (ly(ymax) - ly(v)) / (ly(ymax) - ly(ymin)) * (H - m.t - m.b) : v => m.t + (ymax - v) / (ymax - ymin) * (H - m.t - m.b);
    const g = el('g', { class: 'grid' }, svg), ax = el('g', { class: 'ax' }, svg);
    let ticks = scale === 'log' ? [0.8, 1, 1.5, 2, 3, 5, 10, 20, 50, 100, 200].filter(t => t >= ymin && t <= ymax) : [];
    if (scale === 'lin') { const st = ymax > 60 ? 20 : ymax > 25 ? 10 : ymax > 8 ? 2 : 1; for (let t = 0; t <= ymax; t += st) ticks.push(t); }
    ticks.forEach(t => { el('line', { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t) }, g); const tx = el('text', { x: m.l - 6, y: y(t) + 4, 'text-anchor': 'end' }, ax); tx.textContent = t + 'x'; });
    el('line', { x1: m.l, x2: W - m.r, y1: y(1), y2: y(1), stroke: 'var(--fg)', 'stroke-dasharray': '4 3', 'stroke-width': 1 }, svg);
    const xt = win === 12 ? [-12, -6, 0, 3, 6, 9, 12] : [-12, 0, 12, 24, 36, 48, 60];
    xt.forEach(t => { const tx = el('text', { x: x(t), y: H - m.b + 16, 'text-anchor': 'middle' }, ax); tx.textContent = t; });
    const xl = el('text', { x: x(0) + 4, y: H - 2, 'text-anchor': 'start' }, ax); xl.textContent = 'months since death';
    el('line', { x1: x(0), x2: x(0), y1: m.t, y2: H - m.b, stroke: 'var(--muted)', 'stroke-width': 0.8 }, svg);
    const path = (c, k) => c.k.map((kk, i) => kk >= k0 && kk <= k1 ? `${x(kk).toFixed(1)},${y(c[k][i]).toFixed(1)}` : null).filter(Boolean);
    // band for the first group
    if (keys.length) { const c = S.curves[keys[0]]; const up = path(c, 'hi'), dn = path(c, 'lo').reverse(); el('polygon', { points: up.concat(dn).join(' '), fill: col(keys[0]), opacity: 0.16 }, svg); }
    el('polyline', { points: path(all, 'm').join(' '), fill: 'none', stroke: isDark() ? '#6B6156' : '#C9C2B4', 'stroke-width': 2 }, svg);
    const ends = [];
    keys.forEach(k => {
      const c = S.curves[k]; el('polyline', { points: path(c, 'm').join(' '), fill: 'none', stroke: col(k), 'stroke-width': 2.2, 'stroke-linejoin': 'round' }, svg);
      const i = c.k.indexOf(k1); ends.push({ k, y: y(c.m[i]), v: c.m[i] });
    });
    { const i = all.k.indexOf(k1); ends.push({ k: 'All', y: y(all.m[i]), v: all.m[i] }); }
    ends.sort((a, b) => a.y - b.y);
    const gap = 15, lo = m.t + 6, hiY = H - m.b + 4;
    for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + gap);
    const over = ends.length ? ends[ends.length - 1].y - hiY : 0;
    if (over > 0) { ends[ends.length - 1].y -= over; for (let i = ends.length - 2; i >= 0; i--) ends[i].y = Math.min(ends[i].y, ends[i + 1].y - gap); }
    ends.forEach(e => { const nm = e.k === 'All' ? 'everyone' : e.k.split(':')[1]; const lab = NAMES[nm] || nm;
      const t = el('text', { x: W - m.r + 6, y: e.y + 4, class: 'lbl', fill: e.k === 'All' ? 'var(--muted)' : 'var(--fg)' }, svg);
      t.textContent = small ? e.v.toFixed(2) : (lab.length > 18 ? lab.slice(0, 17) + '.' : lab); });
    // hover
    const cross = el('line', { y1: m.t, y2: H - m.b, stroke: 'var(--fg)', 'stroke-width': 1, opacity: 0 }, svg);
    const hit = el('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent' }, svg);
    const move = ev => {
      const r = svg.getBoundingClientRect(), px = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left;
      const kk = Math.max(k0, Math.min(k1, Math.round(k0 + (px - m.l) / (W - m.l - m.r) * (k1 - k0))));
      cross.setAttribute('x1', x(kk)); cross.setAttribute('x2', x(kk)); cross.setAttribute('opacity', 0.5);
      let h = `<b>${kk === 0 ? 'Month of death' : kk < 0 ? (-kk) + ' month' + (kk < -1 ? 's' : '') + ' before' : kk + ' month' + (kk > 1 ? 's' : '') + ' after'}</b>`;
      [...keys, 'All'].forEach(k => { const c = S.curves[k], i = c.k.indexOf(kk); if (i < 0) return; const nm = k === 'All' ? 'everyone' : k.split(':')[1];
        h += `<div><span class="sw" style="background:${k === 'All' ? '#C9C2B4' : col(k)}"></span>${esc(NAMES[nm] || nm)}: <b>${c.m[i].toFixed(2)}x</b> <span style="color:var(--muted)">n ${fmt(c.n[i])}</span></div>`; });
      tip.innerHTML = h; tip.style.display = 'block';
      const tw = tip.offsetWidth; let lx = x(kk) + 12; if (lx + tw > W) lx = x(kk) - tw - 12; tip.style.left = Math.max(0, lx) + 'px'; tip.style.top = '8px';
    };
    hit.addEventListener('mousemove', move); hit.addEventListener('touchstart', move, { passive: true }); hit.addEventListener('touchmove', move, { passive: true });
    hit.addEventListener('mouseleave', () => { tip.style.display = 'none'; cross.setAttribute('opacity', 0); });
  }
  const seg = (id, attr, set) => document.querySelectorAll(`#${id} button`).forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll(`#${id} button`).forEach(x => x.setAttribute('aria-pressed', x === b)); set(b.dataset[attr]); chips(); draw(); table(); }));
  seg('dim', 'd', v => dim = v); seg('scale', 's', v => scale = v); seg('win', 'w', v => win = +v);
  window.addEventListener('resize', () => { clearTimeout(window.__rt); window.__rt = setTimeout(draw, 120); });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);

  fetch('data/site.json').then(r => r.json()).then(d => { S = d; chips(); draw(); table(); window.__chart = true; });

  // ---------------- map
  const DIV = ['#2F6A9E', '#8FB0CF', '#E5E0D6', '#E3A58F', '#B4442E'];
  const SCALES = { lr: { t: 'Two to three years on', s: [0.8, 0.9, 1, 1.1, 1.2], e: ['0.8', '1 = as before', '1.2'] },
                   y1: { t: 'A year on', s: [0.85, 0.95, 1.05, 1.15, 1.25], e: ['0.85', '1.05', '1.25'] },
                   pk: { t: 'Median peak', s: [8, 12, 16, 22, 30], e: ['8x', '16x', '30x'] } };
  let map = null, mm = 'lr';
  function fill() {
    const s = SCALES[mm].s;
    return ['case', ['has', 'n'], ['interpolate', ['linear'], ['get', mm], s[0], DIV[0], s[1], DIV[1], s[2], DIV[2], s[3], DIV[3], s[4], DIV[4]], '#C4C0B8'];
  }
  function key() {
    document.getElementById('keyTitle').textContent = SCALES[mm].t;
    document.getElementById('keyBar').style.background = `linear-gradient(90deg,${DIV.join(',')})`;
    document.getElementById('keyEnds').innerHTML = SCALES[mm].e.map(x => `<span>${x}</span>`).join('');
    document.querySelectorAll('.mchip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mm));
  }
  function popup(p, ll) {
    let h = `<b class="t">${esc(p.lab || p.name)}</b>`;
    if (p.n == null) h += '<p class="nt">Fewer than 30 people with this citizenship in the sample, so no estimate.</p>';
    else {
      h += `<table><tr><td>People</td><td><b>${fmt(p.n)}</b></td></tr>`;
      h += `<tr><td>2 to 3 years on</td><td><b>${(+p.lr).toFixed(2)}</b> (95%: ${(+p.lo).toFixed(2)} to ${(+p.hi).toFixed(2)})</td></tr>`;
      h += `<tr><td>A year on</td><td>${(+p.y1).toFixed(2)}</td></tr><tr><td>Median peak</td><td>${(+p.pk).toFixed(1)}x</td></tr>`;
      h += `<tr><td>Above before</td><td>${Math.round(p.ab)}% of people</td></tr><tr><td>Women</td><td>${Math.round(p.wo)}%</td></tr>`;
      h += `<tr><td>Largest group</td><td>${esc(p.tf)}</td></tr></table>`;
      h += '<p class="nt">Medians of each person\'s English Wikipedia attention against their own year before death. Country of citizenship from Wikidata (one sampled per person).</p>';
    }
    new maplibregl.Popup({ maxWidth: '300px' }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function initMap() {
    if (!window.maplibregl) return;
    map = new maplibregl.Map({ container: 'map', style: 'https://tiles.openfreemap.org/styles/positron', center: [15, 25], zoom: small ? 0.2 : 1.1, minZoom: 0, maxZoom: 7, attributionControl: { compact: true }, cooperativeGestures: small, renderWorldCopies: false });
    window.__map = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => {
      document.getElementById('nojs').remove();
      document.querySelectorAll('.maplibregl-compact-show').forEach(e => e.classList.remove('maplibregl-compact-show'));
      map.addSource('c', { type: 'geojson', data: 'data/countries.geojson', attribution: 'Natural Earth; Wikipedia pageviews (Wikimedia, CC0); Wikidata (CC0)' });
      const firstSym = map.getStyle().layers.find(l => l.type === 'symbol');
      const before = firstSym ? firstSym.id : undefined;
      map.addLayer({ id: 'cg', type: 'fill', source: 'c', filter: ['!', ['has', 'n']], paint: { 'fill-color': '#C4C0B8', 'fill-opacity': 0.85 } }, before);
      map.addLayer({ id: 'pts', type: 'fill', source: 'c', filter: ['has', 'n'], paint: { 'fill-color': fill(), 'fill-opacity': 0.92 } }, before);
      map.addLayer({ id: 'co', type: 'line', source: 'c', paint: { 'line-color': '#FBF5E4', 'line-width': 0.7 } }, before);
      ['pts', 'cg'].forEach(l => { map.on('click', l, e => popup(e.features[0].properties, e.lngLat)); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
      const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
      btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
      document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
      const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
      const base = map.getStyle().layers.filter(l => !['cg', 'pts', 'co'].includes(l.id) && l.type !== 'background').map(l => l.id);
      document.getElementById('lyC').addEventListener('change', e => vis(['pts'], e.target.checked));
      document.getElementById('lyG').addEventListener('change', e => vis(['cg'], e.target.checked));
      document.getElementById('lyB').addEventListener('change', e => vis(base, e.target.checked));
      document.getElementById('lyO').addEventListener('change', e => vis(['co'], e.target.checked));
      document.querySelectorAll('.mchip[data-m]').forEach(b => b.addEventListener('click', () => { mm = b.dataset.m; map.setPaintProperty('pts', 'fill-color', fill()); key(); }));
      key();
    });
  }
  initMap();
})();
