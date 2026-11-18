/* Decision charts for the BI vs AI site: scatter, heatmap, dumbbell, diverging bar, line.
   Same weight sliders as dash.js; the chart redraws as weights change. SVG, no libraries.
   Colours: three decision bands (blue / yellow / red, validated for colour-blind separation;
   labels and the table view carry the meaning too), gray for context, one brief hue for magnitude. */
const VZ = { band: ['#2a78d6', '#eda100', '#e34948'], gray: '#c3c2b7', ink: '#1e1e1e', muted: '#6b6a66', grid: '#e4e3df' };
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
function fmtN(v, d = 1) { return (+v).toLocaleString('en-GB', { maximumFractionDigits: d }); }

function makeViz(cfg) {
  const root = document.getElementById(cfg.el);
  const w = cfg.weights ? cfg.weights.slice() : null;
  const groups = cfg.groups || { all: cfg.items };
  let g = Object.keys(groups)[0];
  let h = '';
  if (cfg.groups) h += `<div class="sel"><label>${cfg.groupLabel || 'View'}: <select id="${cfg.el}-g">${Object.keys(groups).map(k => `<option>${k}</option>`).join('')}</select></label></div>`;
  if (w) h += `<div class="ctrls">` + cfg.criteria.map((c, i) => `<div class="ctrl"><label for="${cfg.el}-w${i}"><span>${c}</span><span id="${cfg.el}-v${i}">${w[i]}</span></label>
     <input type="range" id="${cfg.el}-w${i}" min="0" max="100" step="5" value="${w[i]}"></div>`).join('') + `</div>`;
  h += `<div class="answer" id="${cfg.el}-a"></div><div class="vz-legend" id="${cfg.el}-l"></div><div class="vz" id="${cfg.el}-c"></div>
        <p class="note">${cfg.note || ''}${w ? ' Weights are rescaled to 100%. <button type="button" id="' + cfg.el + '-r">Reset weights</button>' : ''}</p>
        <details class="vz-table"><summary>Table view</summary><div class="scroll" id="${cfg.el}-t"></div></details>`;
  root.innerHTML = h;

  function scored() {
    const tot = w ? (w.reduce((a, b) => a + b, 0) || 1) : 1;
    return groups[g].map(it => {
      const ok = cfg.eligible ? cfg.eligible(it) : true;
      const v = ok && w ? it.s.reduce((a, s, i) => a + s * w[i], 0) / tot : (it.idx ?? null);
      return { it, ok, v };
    });
  }
  const bandOf = v => !cfg.bands ? null : (v >= cfg.bands.hi ? 0 : v <= cfg.bands.lo ? 2 : 1);
  const colOf = (x, rank) => {
    if (!x.ok) return VZ.gray;
    if (cfg.colour) return cfg.colour(x, rank);
    if (cfg.bands) return VZ.band[bandOf(x.v)];
    return rank < (cfg.highlight || 1) ? (cfg.hue || VZ.band[0]) : VZ.gray;
  };
  function legend() {
    const L = cfg.legend || (cfg.bands ? cfg.bands.labels.map((t, i) => [VZ.band[i], t]) : [[cfg.hue || VZ.band[0], cfg.hiLabel || 'Top pick'], [VZ.gray, 'Others']]);
    document.getElementById(cfg.el + '-l').innerHTML = L.map(([c, t]) => `<span><i style="background:${c}"></i>${esc(t)}</span>`).join('');
  }
  function table(rows) {
    const cols = cfg.tableCols || [];
    document.getElementById(cfg.el + '-t').innerHTML = `<table><thead><tr><th>#</th><th>Item</th>${cols.map(c => `<th>${c[0]}</th>`).join('')}${w ? '<th>Index</th>' : ''}${cfg.bands ? '<th>Decision</th>' : ''}</tr></thead><tbody>` +
      rows.map((x, i) => `<tr><td>${x.ok ? i + 1 : '–'}</td><td>${esc(cfg.label(x.it))}</td>${cols.map(c => `<td>${c[1](x.it)}</td>`).join('')}${w ? `<td>${x.ok && x.v != null ? x.v.toFixed(1) : 'n/a'}</td>` : ''}${cfg.bands ? `<td>${x.ok ? cfg.bands.labels[bandOf(x.v)] : 'not ranked'}</td>` : ''}</tr>`).join('') + '</tbody></table>';
  }

  // ---------- chart types ----------
  function scatter(rows) {
    const W = 900, Hh = cfg.height || 460, m = { l: 70, r: 24, t: 16, b: 52 };
    const pts = rows.filter(x => cfg.x(x.it) != null && cfg.y(x.it) != null);
    const tx = cfg.xLog ? Math.log10 : (v => v), ty = cfg.yLog ? Math.log10 : (v => v);
    const xs = pts.map(x => tx(Math.max(cfg.xLog ? 1e-9 : -1e18, cfg.x(x.it)))), ys = pts.map(x => ty(cfg.y(x.it)));
    let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys, cfg.refY != null ? ty(cfg.refY.v) : Infinity), y1 = Math.max(...ys, cfg.refY != null ? ty(cfg.refY.v) : -Infinity);
    const px = (x1 - x0) * 0.06 || 1, py = (y1 - y0) * 0.08 || 1; x0 -= px; x1 += px; y0 -= py; y1 += py;
    const X = v => m.l + (tx(v) - x0) / (x1 - x0) * (W - m.l - m.r), Y = v => Hh - m.b - (ty(v) - y0) / (y1 - y0) * (Hh - m.t - m.b);
    const ticks = (a, b, log) => { if (log) { const out = []; for (let e = Math.floor(a); e <= Math.ceil(b); e++) [1, 2, 5].forEach(k => { const v = k * 10 ** e; if (Math.log10(v) >= a && Math.log10(v) <= b) out.push(v); }); return out; }
      const step = 10 ** Math.floor(Math.log10((b - a) / 4)); const s2 = [1, 2, 5, 10].map(k => k * step).find(s => (b - a) / s <= 6); const out = []; for (let v = Math.ceil(a / s2) * s2; v <= b; v += s2) out.push(+v.toFixed(10)); return out; };
    let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(cfg.title || 'Scatter chart')}">`;
    ticks(x0, x1, cfg.xLog).forEach(v => { s += `<line x1="${X(v)}" x2="${X(v)}" y1="${m.t}" y2="${Hh - m.b}" stroke="${VZ.grid}"/><text x="${X(v)}" y="${Hh - m.b + 18}" text-anchor="middle" class="tk">${cfg.xFmt ? cfg.xFmt(v) : fmtN(v)}</text>`; });
    ticks(y0, y1, cfg.yLog).forEach(v => { s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${VZ.grid}"/><text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end" class="tk">${cfg.yFmt ? cfg.yFmt(v) : fmtN(v)}</text>`; });
    if (cfg.refY) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(cfg.refY.v)}" y2="${Y(cfg.refY.v)}" stroke="${VZ.ink}" stroke-dasharray="5 4"/><text x="${W - m.r}" y="${Y(cfg.refY.v) - 6}" text-anchor="end" class="rl">${esc(cfg.refY.label)}</text>`;
    if (cfg.refX) s += `<line x1="${X(cfg.refX.v)}" x2="${X(cfg.refX.v)}" y1="${m.t}" y2="${Hh - m.b}" stroke="${VZ.ink}" stroke-dasharray="5 4"/><text x="${X(cfg.refX.v) + 6}" y="${m.t + 12}" class="rl">${esc(cfg.refX.label)}</text>`;
    s += `<text x="${(W + m.l) / 2}" y="${Hh - 10}" text-anchor="middle" class="ax">${esc(cfg.xLabel)}</text><text transform="translate(16 ${(Hh - m.b + m.t) / 2}) rotate(-90)" text-anchor="middle" class="ax">${esc(cfg.yLabel)}</text>`;
    const order = pts.slice().sort((a, b) => (a.ok - b.ok) || ((a.v ?? -1) - (b.v ?? -1)));
    const rk = new Map(rows.filter(r => r.ok).map((r, i) => [r, i]));
    order.forEach(x => { const r = rk.get(x) ?? 999, c = colOf(x, r);
      s += `<circle cx="${X(cfg.x(x.it))}" cy="${Y(cfg.y(x.it))}" r="${r < (cfg.labelTop || 5) ? 7 : 5.5}" fill="${c}" stroke="#fff" stroke-width="2"><title>${esc(cfg.label(x.it))}${x.v != null ? ' · index ' + x.v.toFixed(1) : ''}${cfg.tip ? ' · ' + cfg.tip(x.it) : ''}</title></circle>`; });
    const lab = new Set(rows.filter(x => x.ok).slice(0, cfg.labelTop || 5).concat(rows.filter(x => (cfg.alwaysLabel || []).includes(cfg.label(x.it)))));
    const placed = [];
    [...lab].forEach(x => { if (cfg.x(x.it) == null) return; let lx = X(cfg.x(x.it)) + 10, ly = Y(cfg.y(x.it)) + 4; while (placed.some(p => Math.abs(p[0] - lx) < 90 && Math.abs(p[1] - ly) < 13)) ly += 13; placed.push([lx, ly]);
      const anchor = lx > W - 150 ? 'end' : 'start'; if (anchor === 'end') lx -= 20; s += `<text x="${lx}" y="${ly}" text-anchor="${anchor}" class="pl">${esc(cfg.short ? cfg.short(x.it) : cfg.label(x.it))}</text>`; });
    return s + '</svg>';
  }
  function heat(rows) {
    const crit = cfg.heatCols || cfg.criteria, n = crit.length, cw = 120, lw = 230, rh = 34, W = lw + (n + 1) * cw, Hh = 40 + rows.length * rh;
    const shade = v => { const t = Math.max(0, Math.min(1, v / 100)); return `color-mix(in oklab, ${cfg.hue || VZ.band[0]} ${Math.round(8 + t * 82)}%, #fcfcfb)`; };
    let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(cfg.title || 'Heatmap')}">`;
    crit.concat(['Index']).forEach((c, j) => s += `<text x="${lw + j * cw + cw / 2}" y="24" text-anchor="middle" class="ax">${esc(c)}</text>`);
    rows.forEach((x, i) => { const y = 36 + i * rh;
      s += `<text x="${lw - 10}" y="${y + rh / 2 + 4}" text-anchor="end" class="pl">${esc(cfg.label(x.it))}</text>`;
      x.it.s.forEach((v, j) => { const tv = v === '' || v == null ? null : +v; s += `<rect x="${lw + j * cw + 1}" y="${y + 1}" width="${cw - 2}" height="${rh - 2}" rx="3" fill="${tv == null ? '#f1f0ec' : shade(tv)}"><title>${esc(cfg.label(x.it))} · ${esc(crit[j])}: ${tv == null ? 'n/a' : tv.toFixed(0)}</title></rect><text x="${lw + j * cw + cw / 2}" y="${y + rh / 2 + 4}" text-anchor="middle" class="cv" fill="${tv != null && tv > 60 ? '#fff' : VZ.ink}">${tv == null ? '–' : tv.toFixed(0)}</text>`; });
      const c = colOf(x, i); s += `<rect x="${lw + n * cw + 1}" y="${y + 1}" width="${cw - 2}" height="${rh - 2}" rx="3" fill="#fcfcfb" stroke="${c}" stroke-width="2"/><text x="${lw + n * cw + cw / 2}" y="${y + rh / 2 + 4}" text-anchor="middle" class="cv" font-weight="700">${x.v != null ? x.v.toFixed(1) : '–'}</text>`; });
    return s + '</svg>';
  }
  function dumbbell(rows) {
    const W = 900, rh = 26, m = { l: cfg.labelW || 210, r: 70, t: 30, b: 30 }, Hh = m.t + m.b + rows.length * rh;
    const vals = rows.flatMap(x => [cfg.a(x.it), cfg.b(x.it)]), lo = Math.min(0, ...vals), hi = Math.max(...vals) * 1.05;
    const X = v => m.l + (v - lo) / (hi - lo) * (W - m.l - m.r);
    let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(cfg.title || 'Dumbbell chart')}">`;
    const step = 10 ** Math.floor(Math.log10(hi / 4)); const st = [1, 2, 5, 10].map(k => k * step).find(q => hi / q <= 6);
    for (let v = 0; v <= hi; v += st) s += `<line x1="${X(v)}" x2="${X(v)}" y1="${m.t - 6}" y2="${Hh - m.b}" stroke="${VZ.grid}"/><text x="${X(v)}" y="${Hh - m.b + 16}" text-anchor="middle" class="tk">${cfg.xFmt ? cfg.xFmt(v) : fmtN(v)}</text>`;
    s += `<g class="ax"><circle cx="${m.l}" cy="12" r="5" fill="#fcfcfb" stroke="${VZ.ink}" stroke-width="2"/><text x="${m.l + 10}" y="16">${esc(cfg.aLabel)}</text><circle cx="${m.l + 230}" cy="12" r="5" fill="${VZ.ink}"/><text x="${m.l + 240}" y="16">${esc(cfg.bLabel)}</text></g>`;
    rows.forEach((x, i) => { const y = m.t + i * rh + rh / 2, a = cfg.a(x.it), b = cfg.b(x.it), c = colOf(x, i);
      s += `<text x="${m.l - 10}" y="${y + 4}" text-anchor="end" class="pl">${esc(cfg.label(x.it))}</text><line x1="${X(a)}" x2="${X(b)}" y1="${y}" y2="${y}" stroke="${c}" stroke-width="4" stroke-linecap="round"/>
        <circle cx="${X(a)}" cy="${y}" r="5.5" fill="#fcfcfb" stroke="${c}" stroke-width="2.5"><title>${esc(cfg.label(x.it))} · ${esc(cfg.aLabel)}: ${fmtN(a)}</title></circle>
        <circle cx="${X(b)}" cy="${y}" r="5.5" fill="${c}"><title>${esc(cfg.label(x.it))} · ${esc(cfg.bLabel)}: ${fmtN(b)}</title></circle>
        <text x="${W - m.r + 8}" y="${y + 4}" class="tk">${cfg.right ? cfg.right(x) : ''}</text>`; });
    return s + '</svg>';
  }
  function diverge(rows) {
    const W = 900, rh = 26, m = { l: cfg.labelW || 220, r: 30, t: 14, b: 30 }, Hh = m.t + m.b + rows.length * rh;
    const vs = rows.map(x => cfg.v(x.it)), mx = Math.max(...vs.map(Math.abs)) * 1.25, X = v => m.l + (v + mx) / (2 * mx) * (W - m.l - m.r);
    let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(cfg.title || 'Diverging bar chart')}">`;
    s += `<line x1="${X(0)}" x2="${X(0)}" y1="${m.t}" y2="${Hh - m.b}" stroke="${VZ.ink}"/><text x="${X(-mx / 2)}" y="${Hh - 8}" text-anchor="middle" class="ax">${esc(cfg.negLabel)}</text><text x="${X(mx / 2)}" y="${Hh - 8}" text-anchor="middle" class="ax">${esc(cfg.posLabel)}</text>`;
    rows.forEach((x, i) => { const y = m.t + i * rh, v = cfg.v(x.it), c = colOf(x, i), x0 = Math.min(X(0), X(v));
      s += `<text x="${m.l - 10}" y="${y + rh / 2 + 4}" text-anchor="end" class="pl">${esc(cfg.label(x.it))}</text><rect x="${x0}" y="${y + 4}" width="${Math.max(1, Math.abs(X(v) - X(0)))}" height="${rh - 8}" rx="3" fill="${c}"><title>${esc(cfg.label(x.it))} · ${cfg.tip(x.it)}</title></rect>
        <text x="${v < 0 ? X(0) + 6 : X(v) + 6}" y="${y + rh / 2 + 4}" text-anchor="start" class="tk">${fmtN(v, 0)}</text>`; });
    return s + '</svg>';
  }
  function line() {
    const W = 900, Hh = 380, m = { l: 50, r: 150, t: 16, b: 36 }, S0 = cfg.series, S = S0.map((r, i) => { const o = { week: r.week }; cfg.keys.forEach(k => { const win = S0.slice(Math.max(0, i - 3), i + 1); o[k] = win.reduce((a, q) => a + q[k], 0) / win.length; }); return o; }), keys = cfg.keys, sel = new Set(cfg.emph);
    const all = keys.flatMap(k => S.map(r => r[k])).filter(v => v != null), y1 = Math.max(...all) * 1.05;
    const X = i => m.l + i / (S.length - 1) * (W - m.l - m.r), Y = v => Hh - m.b - v / y1 * (Hh - m.t - m.b);
    let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(cfg.title || 'Line chart')}">`;
    [0, 50, 100, 150, 200, 250, 300, 350, 400].filter(v => v <= y1).forEach(v => s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${v === 100 ? VZ.ink : VZ.grid}" ${v === 100 ? 'stroke-dasharray="5 4"' : ''}/><text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end" class="tk">${v}</text>`);
    S.forEach((r, i) => { if (i === 0 || r.week.slice(0, 4) !== S[i - 1].week.slice(0, 4)) s += `<text x="${X(i)}" y="${Hh - m.b + 18}" text-anchor="middle" class="tk">${r.week.slice(0, 4)}</text>`; });
    const pal = [VZ.band[0], VZ.band[2], '#1baf7a'];
    keys.forEach(k => { if (sel.has(k)) return; s += `<path d="${S.map((r, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(r[k]).toFixed(1)).join('')}" fill="none" stroke="${VZ.gray}" stroke-width="1.5"><title>${esc(k)}</title></path>`; });
    [...sel].forEach((k, j) => { s += `<path d="${S.map((r, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(r[k]).toFixed(1)).join('')}" fill="none" stroke="${pal[j]}" stroke-width="2.5"><title>${esc(k)}</title></path><text x="${W - m.r + 8}" y="${Y(S[S.length - 1][k]) + 4}" class="pl" fill="${VZ.ink}">${esc(k)}</text>`; });
    return s + '</svg>';
  }

  function draw() {
    if (cfg.type === 'line') { document.getElementById(cfg.el + '-c').innerHTML = line(); document.getElementById(cfg.el + '-a').innerHTML = cfg.answer ? cfg.answer() : ''; legend(); return; }
    const items = scored(); const rows = items.filter(x => x.ok).sort((a, b) => b.v - a.v).concat(items.filter(x => !x.ok));
    const R = { scatter, heat, dumbbell, diverge }[cfg.type];
    document.getElementById(cfg.el + '-c').innerHTML = R(cfg.type === 'heat' || cfg.type === 'dumbbell' || cfg.type === 'diverge' ? (cfg.sort ? rows.slice().sort(cfg.sort) : rows) : rows);
    document.getElementById(cfg.el + '-a').innerHTML = cfg.answer ? cfg.answer(rows.filter(x => x.ok), g) : '';
    legend(); table(rows);
  }
  if (w) {
    cfg.criteria.forEach((c, i) => { const inp = document.getElementById(`${cfg.el}-w${i}`);
      inp.addEventListener('input', () => { w[i] = +inp.value; document.getElementById(`${cfg.el}-v${i}`).textContent = w[i]; draw(); }); });
    document.getElementById(cfg.el + '-r').addEventListener('click', () => { cfg.weights.forEach((v, i) => { w[i] = v; document.getElementById(`${cfg.el}-w${i}`).value = v; document.getElementById(`${cfg.el}-v${i}`).textContent = v; }); draw(); });
  }
  if (cfg.groups) document.getElementById(cfg.el + '-g').addEventListener('change', e => { g = e.target.value; draw(); });
  draw();
}
