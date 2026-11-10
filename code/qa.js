// QA: serve the studies folder, open index.html at desktop and phone widths, log console errors and save screenshots to qa/.
// Usage: node code/qa.js [maplibre dist dir]. OpenFreeMap tiles live; Google Fonts and site-nav skipped.
const fs = require('fs'), path = require('path'), http = require('http');
const { chromium } = require(process.env.PW || 'playwright');
const ROOT = path.resolve(__dirname, '..'), STUDIES = path.dirname(ROOT), SLUG = path.basename(ROOT);
const ML = process.argv[2] || '/tmp/ml/node_modules/maplibre-gl/dist';
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.geojson': 'application/json', '.css': 'text/css', '.jpg': 'image/jpeg' };
const PORT = 8800 + Math.floor(Math.random() * 90);
const srv = http.createServer((q, s) => { const f = path.join(STUDIES, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, b) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); s.end(b); }); }).listen(PORT);
const PAGE = `http://localhost:${PORT}/${SLUG}/index.html`;
const SHOTS = [
  { out: 'qa/desktop.jpg', w: 1280, h: 900 },
  { out: 'qa/desktop_age.jpg', w: 1280, h: 900, eval: "document.querySelector('#dim button[data-d=ageb]').click(); const r=document.querySelector('#plot rect').getBoundingClientRect(); document.querySelector('#plot rect').dispatchEvent(new MouseEvent('mousemove',{clientX:r.left+r.width*0.3,clientY:r.top+50,bubbles:true}))" },
  { out: 'qa/desktop_map.jpg', w: 1280, h: 900, eval: "document.getElementById('mapWrap').scrollIntoView(); window.__map.fire('click',{lngLat:{lng:-100,lat:40},point:window.__map.project([-100,40]),features:window.__map.queryRenderedFeatures(window.__map.project([-100,40]),{layers:['pts']})})" },
  { out: 'qa/desktop_layers.jpg', w: 1280, h: 900, eval: "document.getElementById('mapWrap').scrollIntoView(); document.getElementById('lyrBtn').click(); document.querySelector('.mchip[data-m=pk]').click()" },
  { out: 'qa/phone.jpg', w: 390, h: 844, dpr: 2 },
  { out: 'qa/phone_map.jpg', w: 390, h: 844, dpr: 2, eval: "document.getElementById('mapWrap').scrollIntoView()" },
  { out: 'qa/phone_full.jpg', w: 390, h: 844, dpr: 1, full: true }
];
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const errors = [];
  for (const s of SHOTS) {
    const ctx = await browser.newContext({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: s.dpr || 1 });
    const page = await ctx.newPage();
    await page.route(/cdn\.jsdelivr\.net\/npm\/maplibre-gl@4\.7\.1\/dist\/(.*)/, r => { const f = path.join(ML, r.request().url().split('/dist/')[1]); r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' }); });
    await page.route(/fonts\.(googleapis|gstatic)\.com|maps\.tristanhotham\.com\/assets/, r => r.abort());
    page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(`[${s.out}] ${m.text().slice(0, 300)}`); });
    page.on('pageerror', e => errors.push(`[${s.out}] pageerror ${e.message}`));
    await page.goto(PAGE, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__chart && window.__map && window.__map.getLayer('pts'), null, { timeout: 120000 });
    await page.evaluate(() => new Promise(res => { const m = window.__map; m.once('idle', () => setTimeout(res, 1200)); setTimeout(res, 30000); }));
    if (s.eval) { await page.evaluate(s.eval); await page.waitForTimeout(2500); }
    const info = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, w: innerWidth, fs: document.querySelectorAll('.mfs-btn').length, popup: !!document.querySelector('.maplibregl-popup'), lines: document.querySelectorAll('#plot polyline').length }));
    await page.screenshot({ path: path.join(ROOT, s.out), type: 'jpeg', quality: 70, fullPage: !!s.full, timeout: 120000 });
    console.log('ok', s.out, JSON.stringify(info));
    await ctx.close();
  }
  await browser.close(); srv.close();
  console.log('ERRORS:', errors.length); errors.forEach(e => console.log(e));
  process.exit(0);
})();
