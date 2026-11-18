/* Generic weighted-scoring dashboard.
   cfg = { el, criteria:[names], weights:[defaults], groups:{label:[items]} or items:[...],
           top:N, label:item=>string, extra:item=>string, eligible:item=>bool,
           bands:{hi:60, lo:35, labels:['CHARGE','HOLD','ABSORB']}, answer:(ranked,group)=>html }
   item.s = array of 0-100 criterion scores (already min-max scored in the workbook). */
function makeDash(cfg) {
  const root = document.getElementById(cfg.el);
  const w = cfg.weights.slice();
  const groups = cfg.groups || { all: cfg.items };
  let g = Object.keys(groups)[0];
  let html = '';
  if (cfg.groups) {
    html += `<div class="sel"><label>${cfg.groupLabel || 'View'}: <select id="${cfg.el}-g">` +
      Object.keys(groups).map(k => `<option>${k}</option>`).join('') + `</select></label></div>`;
  }
  html += `<div class="ctrls">` + cfg.criteria.map((c, i) =>
    `<div class="ctrl"><label for="${cfg.el}-w${i}"><span>${c}</span><span id="${cfg.el}-v${i}">${w[i]}</span></label>
     <input type="range" id="${cfg.el}-w${i}" min="0" max="100" step="5" value="${w[i]}"></div>`).join('') + `</div>`;
  html += `<div class="answer" id="${cfg.el}-a"></div><div class="bars" id="${cfg.el}-b"></div>
           <p class="note">Weights are rescaled to 100%. Scores per criterion come from the Excel model (0–100, best = 100). <button type="button" id="${cfg.el}-r">Reset weights</button></p>`;
  root.innerHTML = html;
  function draw() {
    const tot = w.reduce((a, b) => a + b, 0) || 1;
    const items = groups[g].map(it => {
      const ok = cfg.eligible ? cfg.eligible(it) : true;
      return { it, ok, v: ok ? it.s.reduce((a, s, i) => a + s * w[i], 0) / tot : null };
    });
    const ranked = items.filter(x => x.ok).sort((a, b) => b.v - a.v);
    const rest = items.filter(x => !x.ok);
    const show = ranked.slice(0, cfg.top || ranked.length);
    const band = v => !cfg.bands ? '' : (v >= cfg.bands.hi ? cfg.bands.labels[0] : v <= cfg.bands.lo ? cfg.bands.labels[2] : cfg.bands.labels[1]);
    document.getElementById(cfg.el + '-b').innerHTML = show.map((x, i) =>
      `<div class="row${i < (cfg.highlight || 1) ? ' top' : ''}"><div>${i + 1}. ${cfg.label(x.it)}${cfg.extra ? `<span class="tag">${cfg.extra(x.it)}</span>` : ''}${cfg.bands ? ` <span class="tag"><b>${band(x.v)}</b></span>` : ''}</div>
       <div class="track"><div class="fill" style="width:${Math.max(1, x.v).toFixed(1)}%"></div></div><div class="val">${x.v.toFixed(1)}</div></div>`).join('') +
      (rest.length ? `<p class="note">Not ranked (below the import minimum): ${rest.map(x => cfg.label(x.it)).join(', ')}</p>` : '') +
      (cfg.top && ranked.length > cfg.top ? `<p class="note">Showing the top ${cfg.top} of ${ranked.length}.</p>` : '');
    document.getElementById(cfg.el + '-a').innerHTML = cfg.answer ? cfg.answer(ranked, g) : '';
  }
  cfg.criteria.forEach((c, i) => {
    const inp = document.getElementById(`${cfg.el}-w${i}`);
    inp.addEventListener('input', () => { w[i] = +inp.value; document.getElementById(`${cfg.el}-v${i}`).textContent = w[i]; draw(); });
  });
  document.getElementById(cfg.el + '-r').addEventListener('click', () => {
    cfg.weights.forEach((v, i) => { w[i] = v; document.getElementById(`${cfg.el}-w${i}`).value = v; document.getElementById(`${cfg.el}-v${i}`).textContent = v; }); draw();
  });
  if (cfg.groups) document.getElementById(cfg.el + '-g').addEventListener('change', e => { g = e.target.value; draw(); });
  draw();
}
