"""Configs and seeded generators for synthetic briefs 3, 4, 9, 13, 15, 18."""
import inspect, json
import numpy as np, pandas as pd

D = '/home/claude/p2/syn/'
LAB = json.load(open(D + 'labels.json'))
PROMPT_BASE = ("Generate a synthetic table for Brief {n} that a {who_short} would see on a normal day. Anchor every field to the "
               "public data in Anchor_Data (ranges, means, mixes, seasonality) or to a labelled assumption; use a fixed seed so the table "
               "can be regenerated exactly; keep the generator short enough to print in the workbook; check the generated values against "
               "the anchor and report PASS/CHECK. Do not use the synthetic table as evidence about the real company.")
W5 = lambda base: [("Base", base), ("Equal", [20] * 5)]


# ======================= B3 Berth window priority =======================
def gen_b3(seed=303):
    rng = np.random.default_rng(seed)
    n = 19                                            # PortWatch: 7,045 container calls a year / 365 = 19.3 a day
    svc = rng.choice(['Mainline', 'Feeder', 'Shortsea'], n, p=[0.40, 0.45, 0.15])
    mu = {'Mainline': 9.0, 'Feeder': 7.0, 'Shortsea': 6.3}    # log-TEU centres, rescaled below to the UNCTAD mean
    teu = np.array([rng.lognormal(mu[s], 0.35) for s in svc])
    teu = np.clip(teu * 3151 / teu.mean(), 300, 24116).round(-1)   # UNCTAD NL: mean 3,151 TEU, max 24,116
    exch = rng.uniform(0.25, 0.45, n)                              # share of capacity exchanged per call (assumption)
    moves = (teu * exch / 1.6).round()                             # boxes, 1.6 TEU per box (assumption)
    eta = rng.normal(0, 6, n).round(1)                             # hours early(-)/late(+) vs agreed window
    ts = np.where(svc == 'Feeder', rng.uniform(0.4, 0.8, n), rng.uniform(0.15, 0.5, n)).round(2)
    slack = rng.uniform(4, 48, n).round(1)                         # hours to the connecting vessel's cut-off
    tier = np.array([{'Mainline': 1.0, 'Feeder': 0.5, 'Shortsea': 0.0}[s] for s in svc])
    yard = (moves * (1 - ts) * rng.uniform(0.3, 0.9, n)).round()   # export boxes already stacked for this call
    return pd.DataFrame({'call': [f'V{i+1:02d}' for i in range(n)], 'service': svc, 'teu': teu, 'moves': moves,
                         'eta_dev': eta, 'ts_share': ts, 'slack': slack, 'tier': tier, 'yard': yard})


def cfg_b3():
    s = gen_b3()
    pw = pd.DataFrame({'Source': ['PortWatch ports database', 'PortWatch ports database', 'UNCTAD port calls (NL, container ships)', 'UNCTAD port calls (NL, container ships)', 'UNCTAD port calls (NL, container ships)', 'CPPI 2025 (World Bank/S&P)', 'CPPI 2025 (World Bank/S&P)'],
                       'Field': ['Container vessel calls, Rotterdam (port1114), per year', 'All vessel calls, Rotterdam, per year', 'Average container ship size, TEU', 'Largest ship, TEU', 'Median time in port, days', 'Rotterdam CPPI 2025 score', 'Share of port hours spent at berth'],
                       'Value': [7045, 32584, 3151, 24116, 0.8, -38.3, 0.65]})
    return dict(
        n=3, slug='Brief-03_Berth_Window_Priority', file='Brief03_ECT_Berth_Window_Model.xlsx', colour='0B5563',
        title='Brief 3 - Berth window priority (Hutchison Ports ECT Rotterdam, synthetic shift data)',
        decision='On a congested day, which arriving container vessels keep their agreed berth window (PROTECT), which can be moved a few hours (FLEX) and which go to the back of the queue (SHIFT)?',
        who='Berth planner at a deep-sea container terminal, deciding shift by shift. The plan is redone every 8 hours as ETAs change.',
        company='Hutchison Ports ECT Rotterdam (Euromax / Delta terminals) as the reference. All call-level data are synthetic.',
        anchor_note='PortWatch (IMF/Oxford) port database: Rotterdam container calls per year. UNCTAD port-call statistics for the Netherlands: ship size and time in port. CPPI 2025: Rotterdam score and berth share.',
        anchor_src='PortWatch ArcGIS PortWatch_ports_database (pulled 17 Nov 2026); UNCTADstat port calls (user upload); CPPI 2025 Annex 2.',
        syn_note='19 vessel calls for one day (7,045 calls / 365). Ship size scaled so the mean matches UNCTAD 3,151 TEU; service mix, ETA deviation, transshipment share, connection slack and yard stacks are generated from stated distributions.',
        method='Five criteria per call -> min-max 0-100 -> weighted Berth Priority Index -> bands.',
        rule_note='PROTECT if index >= high band; SHIFT if <= low band; otherwise FLEX.',
        private='A terminal operating system (Navis N4, TOPS, CATOS) holds every call, stowage plan (BAPLIE), yard stack and connection; carriers send ETAs (EDI) and AIS gives live positions. None of it is public.',
        inputs=[('W1', 'Weight - Window adherence (|ETA deviation|, lower better)', 20, 'pts', 'Punctual ships keep their slot; standard berth-window agreements.', True),
                ('W2', 'Weight - Call size (boxes to move)', 20, 'pts', 'Crane hours and quay productivity.', True),
                ('W3', 'Weight - Connections at risk (transshipment boxes with tight slack)', 25, 'pts', 'Missed connections cost the carrier a week.', True),
                ('W4', 'Weight - Service tier (mainline 1, feeder 0.5, shortsea 0)', 15, 'pts', 'Contract priority.', True),
                ('W5', 'Weight - Yard pressure (export boxes already stacked)', 20, 'pts', 'Clearing the yard frees space.', True),
                ('T1', 'Tight connection threshold', 24, 'hours', 'Below this slack, a transshipment box is at risk.', True),
                ('T2', 'Weight on boxes with loose connections', 0.25, 'x', 'Share of at-risk weight kept above the threshold (assumption).', False),
                ('B1', 'PROTECT band (index >=)', 60, 'pts', '', True), ('B2', 'SHIFT band (index <=)', 35, 'pts', '', True)],
        anchor=pw, synthetic=s,
        syn_labels={'call': 'Call', 'service': 'Service', 'teu': 'Ship size (TEU)', 'moves': 'Boxes to move', 'eta_dev': 'ETA vs window (h)', 'ts_share': 'Transshipment share', 'slack': 'Connection slack (h)', 'tier': 'Service tier', 'yard': 'Export boxes in yard'},
        syn_fmt={'ts_share': '0%', 'tier': '0.0', 'eta_dev': '0.0', 'slack': '0.0'},
        item_label='Call', scores_note='S1 uses |ETA deviation|; S3 = boxes x transshipment share x (1 if slack < T1 else T2).',
        derived=[],
        criteria=[dict(label='|ETA dev| (h)', f='ABS({eta_dev})', dir=-1, w='W1', fmt='0.0'),
                  dict(label='Boxes to move', f='{moves}', dir=1, w='W2', fmt='#,##0'),
                  dict(label='Boxes at risk', f='{moves}*{ts_share}*IF({slack}<{IN:T1},1,{IN:T2})', dir=1, w='W3', fmt='#,##0'),
                  dict(label='Service tier', f='{tier}', dir=1, w='W4', fmt='0.0'),
                  dict(label='Yard boxes', f='{yard}', dir=1, w='W5', fmt='#,##0')],
        rule='IF([IDX]>={IN:B1},"PROTECT",IF([IDX]<={IN:B2},"SHIFT","FLEX"))',
        dec_colours=[('PROTECT', 'C6EFCE'), ('FLEX', 'FFEB9C'), ('SHIFT', 'FFC7CE')],
        summary=[('Calls to PROTECT', 'COUNTIF([DEC],"PROTECT")'), ('Calls to FLEX', 'COUNTIF([DEC],"FLEX")'), ('Calls to SHIFT', 'COUNTIF([DEC],"SHIFT")')],
        sens=[('Base', [20, 20, 25, 15, 20]), ('Equal', [20] * 5), ('Punctuality-led', [40, 15, 20, 10, 15]), ('Connection-led', [10, 15, 50, 10, 15]), ('Contract-led', [15, 15, 20, 40, 10])],
        sens_count='COUNTIF([IDX],">="&Inputs!$C$12)', sens_count_label='Calls >= PROTECT band',
        seed=303, script='gen_b3() in briefs.py', prompt=PROMPT_BASE.format(n=3, who_short='berth planner at a Rotterdam container terminal'),
        gen_params=[('Calls per day', 'Fixed', '19', 'PortWatch: 7,045 container calls / 365 = 19.3'),
                    ('Service', 'Categorical', 'Mainline 40%, Feeder 45%, Shortsea 15%', 'Assumption: deep-sea hub with large feeder network'),
                    ('Ship size TEU', 'Lognormal by service, rescaled to mean, clipped', 'log-centres 9.0/7.0/6.3, sd 0.35; mean 3,151; max 24,116', 'UNCTAD NL average and largest ship'),
                    ('Boxes to move', 'TEU x exchange ratio / 1.6', 'exchange U(0.25, 0.45)', 'Assumption'),
                    ('ETA deviation', 'Normal', 'mean 0 h, sd 6 h', 'Assumption'),
                    ('Transshipment share', 'Uniform by service', 'Feeder U(0.4,0.8); other U(0.15,0.5)', 'Assumption'),
                    ('Connection slack', 'Uniform', 'U(4, 48) h', 'Assumption'),
                    ('Yard boxes', 'boxes x (1 - TS share) x U(0.3, 0.9)', '', 'Assumption')],
        checks=[('Calls in the day vs PortWatch daily average', 'COUNTA([S]A[R0]:A[RN])', 'Anchor_Data!C5/365', 0.05),
                ('Mean ship size (TEU) vs UNCTAD', 'AVERAGE([S]C[R0]:C[RN])', 'Anchor_Data!C7', 0.05),
                ('Largest generated ship does not exceed UNCTAD maximum (1 = yes)', 'IF(MAX([S]C[R0]:C[RN])<=Anchor_Data!C8,1,0)', 1, 0)],
        code=inspect.getsource(gen_b3),
        source_key=[('Calls per day', 'REAL (anchor)', 'PortWatch annual container calls / 365'), ('Ship size distribution', 'SYNTHETIC', 'Rescaled to UNCTAD mean 3,151 TEU'),
                    ('Service, ETA, TS share, slack, yard', 'SYNTHETIC', 'Generated, see Generation_Log'), ('Weights, bands, thresholds', 'ASSUMPTION', 'Inputs sheet'),
                    ('CPPI score, berth share', 'REAL (anchor)', 'Context only; not used in scoring')],
        limits=['Every call-level value is synthetic: the ranking shows how the rule behaves, not which real ships should berth.',
                'Real berth planning is a scheduling problem (berth length, crane splits, tides); this index only orders priority.',
                'The plan changes every few hours; a static index is a snapshot.',
                'Service tier stands in for contract terms that are confidential.'],
    )


# ======================= B4 Empty repositioning =======================
PORTS4 = ['NL_0NLRTM', 'BE_0BE003', 'DE_1DEHAM', 'DE_1DEBRV', 'FR_1FR001', 'PL_0PLGDN', 'SE_2SEGOT', 'ES_2ESVLC', 'ES_2ESBCN', 'ES_2ESALG', 'EL_0GRPIR', 'IT_0ITGOA', 'SI_0SIKOP', 'FR_2FRMRS']


def anchor_b4():
    b = pd.read_csv(D + 'anchor_B4.csv'); b = b[b.unit == 'THS_TEU']
    t = b[(b.loadstat == 'TOTAL') & (b.time == 2024)].set_index('rep_mar').value
    e = b[(b.loadstat == 'EMPTY') & (b.time == 2024)].set_index('rep_mar').value
    return pd.DataFrame({'code': PORTS4, 'port': [LAB['b4'][p] for p in PORTS4], 'teu_2024_k': [t[p] for p in PORTS4],
                         'empty_2024_k': [e[p] for p in PORTS4], 'empty_share': [round(e[p] / t[p], 4) for p in PORTS4]})


def gen_b4(anchor, seed=404):
    rng = np.random.default_rng(seed)
    a = anchor.copy(); n = len(a)
    share = 0.12                                                   # carrier's share of each port's boxes (assumption)
    wk = a.teu_2024_k * 1000 * share / 52                          # carrier TEU through the port per week
    tilt = (a.empty_share - 0.173) * 4                             # vs top-20 average 17.3%: high empty share -> surplus tilt
    demand = (wk * 0.5 * 4 * rng.uniform(0.85, 1.15, n)).round(-1)            # 4-week export demand for empties
    returns = (demand * (1 + tilt + rng.normal(0, 0.12, n))).clip(0).round(-1)  # 4-week import returns
    stock = (wk * rng.uniform(0.15, 0.45, n)).round(-1)            # empties on hand now
    safety = (demand / 28 * 5).round(-1)                           # 5 days of demand as minimum stock
    cost = rng.uniform(90, 320, n).round()                         # EUR/TEU to bring an empty from the nearest surplus depot
    rev = rng.uniform(500, 1200, n).round(-1)                      # EUR contribution per export TEU lost if no box
    mape = rng.uniform(0.06, 0.30, n).round(2)                     # forecast error of the 4-week demand
    return pd.DataFrame({'depot': a.port, 'stock': stock, 'demand4w': demand, 'returns4w': returns, 'safety': safety,
                         'cost_teu': cost, 'rev_teu': rev, 'mape': mape})


def cfg_b4():
    a = anchor_b4(); s = gen_b4(a)
    return dict(
        n=4, slug='Brief-04_Empty_Repositioning', file='Brief04_CMA_CGM_Empty_Repositioning_Model.xlsx', colour='1F3A68',
        title='Brief 4 - Empty container repositioning (CMA CGM Europe, synthetic depot data)',
        decision='Over the next four weeks, which European depots should receive repositioned empty containers first, and which depots can supply them?',
        who='Equipment-control manager at a container line, weekly cycle, balancing empty stock across European depots.',
        company='CMA CGM as the reference carrier. Port volumes are real (Eurostat); all depot stock, forecasts and costs are synthetic.',
        anchor_note='Eurostat mar_mg_am_pvh: TEU handled in the top 20 EU ports, total and empty, 2019-2024 (pulled 17 Nov 2026).',
        anchor_src='Eurostat mar_mg_am_pvh, 2024, thousand TEU (pulled 17 Nov 2026 via the dissemination API).',
        syn_note='14 depots at EU top-20 ports. Weekly flow = port TEU x 12% carrier share / 52. Returns are tilted by each port\'s real empty share versus the top-20 average (17.3%): ports that handle many empties lean to surplus. Stock, costs, revenue and forecast error are generated.',
        method='Projected balance = stock + returns - demand. Deficit depots scored on five criteria -> weighted Repositioning Need Index -> bands. Depots in surplus are flagged as sources.',
        rule_note='SOURCE if projected balance >= safety stock; else REPOSITION if index >= high band, NO ACTION if <= low band, otherwise WATCH.',
        private='Carrier equipment-control systems (e.g. CMA CGM\'s own, Hapag-Lloyd\'s, or Avantida/xChange marketplaces) hold daily stock by depot, bookings, off-hire returns and leasing costs. Public data stop at port-level TEU per year.',
        inputs=[('W1', 'Weight - Shortage (TEU below safety)', 30, 'pts', '', True), ('W2', 'Weight - Revenue at risk (EUR)', 25, 'pts', '', True),
                ('W3', 'Weight - Repositioning cost per TEU (lower better)', 20, 'pts', '', True), ('W4', 'Weight - Days of cover (lower = more urgent)', 15, 'pts', '', True),
                ('W5', 'Weight - Forecast reliability (MAPE, lower better)', 10, 'pts', '', True),
                ('B1', 'REPOSITION band (index >=)', 60, 'pts', '', True), ('B2', 'NO ACTION band (index <=)', 35, 'pts', '', True)],
        anchor=a, synthetic=s,
        syn_labels={'depot': 'Depot', 'stock': 'Empties on hand (TEU)', 'demand4w': 'Export demand, 4 wks (TEU)', 'returns4w': 'Import returns, 4 wks (TEU)', 'safety': 'Safety stock (TEU)', 'cost_teu': 'Repositioning cost (EUR/TEU)', 'rev_teu': 'Contribution per export TEU (EUR)', 'mape': 'Forecast error (MAPE)'},
        syn_fmt={'mape': '0%', 'stock': '#,##0', 'demand4w': '#,##0', 'returns4w': '#,##0', 'safety': '#,##0', 'cost_teu': '#,##0', 'rev_teu': '#,##0'},
        item_label='Depot', scores_note='Balance = stock + returns - demand. Shortage = MAX(0, safety - balance). Days of cover = MAX(0, stock + returns - safety) / daily demand.',
        derived=[('Projected balance (TEU)', '{stock}+{returns4w}-{demand4w}', '#,##0')],
        criteria=[dict(label='Shortage (TEU)', f='MAX(0,{safety}-B{ROW})', dir=1, w='W1', fmt='#,##0'),
                  dict(label='Revenue at risk (EUR)', f='MAX(0,{safety}-B{ROW})*{rev_teu}', dir=1, w='W2', fmt='#,##0'),
                  dict(label='Cost per TEU (EUR)', f='{cost_teu}', dir=-1, w='W3', fmt='#,##0'),
                  dict(label='Days of cover', f='MAX(0,{stock}+{returns4w}-{safety})/({demand4w}/28)', dir=-1, w='W4', fmt='0.0'),
                  dict(label='Forecast MAPE', f='{mape}', dir=-1, w='W5', fmt='0%')],
        eligible='IF(B{ROW}>={safety},0,1)',
        rule='IF(B{ROW}>={safety},"SOURCE",IF([IDX]>={IN:B1},"REPOSITION",IF([IDX]<={IN:B2},"NO ACTION","WATCH")))',
        dec_colours=[('REPOSITION', 'FFC7CE'), ('WATCH', 'FFEB9C'), ('NO ACTION', 'EDEDED'), ('SOURCE', 'C6EFCE')],
        summary=[('Depots to receive (REPOSITION)', 'COUNTIF([DEC],"REPOSITION")'), ('Source depots (surplus)', 'COUNTIF([DEC],"SOURCE")'),
                 ('Total shortage (TEU)', 'SUM(Scores!C5:C18)'), ('Total surplus above safety (TEU)', 'SUMPRODUCT((Scores!B5:B18>Synthetic_Data!E5:E18)*(Scores!B5:B18-Synthetic_Data!E5:E18))')],
        sens=[('Base', [30, 25, 20, 15, 10]), ('Equal', [20] * 5), ('Cost-led', [20, 15, 45, 10, 10]), ('Revenue-led', [20, 45, 15, 10, 10]), ('Urgency-led', [25, 15, 10, 40, 10])],
        sens_count=None,
        seed=404, script='anchor_b4() and gen_b4() in briefs.py', prompt=PROMPT_BASE.format(n=4, who_short='container line equipment controller'),
        gen_params=[('Weekly carrier TEU', 'port TEU 2024 x share / 52', 'share 12%', 'Eurostat port TEU (real)'),
                    ('Surplus tilt', '(empty share - 0.173) x 4', '', 'Eurostat empty share vs top-20 average'),
                    ('Export demand 4 wks', 'weekly x 0.5 x 4 x U(0.85,1.15)', '', 'Assumption: half of boxes are exports'),
                    ('Import returns 4 wks', 'demand x (1 + tilt + N(0,0.12)), >= 0', '', 'Anchored tilt + noise'),
                    ('Stock now', 'weekly x U(0.15,0.45)', '', 'Assumption'), ('Safety stock', '5 days of demand', '', 'Assumption'),
                    ('Repositioning cost', 'U(90, 320) EUR/TEU', '', 'Assumption; truck/barge/feeder range'),
                    ('Contribution per TEU', 'U(500, 1200) EUR', '', 'Assumption; Europe-Asia backhaul is cheaper than the WCI headhaul rate'),
                    ('Forecast MAPE', 'U(0.06, 0.30)', '', 'Assumption')],
        checks=[('Total weekly carrier TEU = 12% of 2024 port TEU / 52', 'SUM([S]C[R0]:C[RN])/2', 'SUM(Anchor_Data!C5:C18)*1000*0.12/52', 0.1),
                ('Import returns rise with the real empty share (1 = positive correlation)', 'IF(SUMPRODUCT((Anchor_Data!E5:E18-AVERAGE(Anchor_Data!E5:E18))*([S]D[R0]:D[RN]-AVERAGE([S]D[R0]:D[RN])))>0,1,0)', 1, 0)],
        code=inspect.getsource(anchor_b4) + '\n' + inspect.getsource(gen_b4),
        source_key=[('Port TEU, empty TEU, empty share', 'REAL (anchor)', 'Eurostat mar_mg_am_pvh 2024'), ('Carrier share 12%', 'ASSUMPTION', 'Inputs to generator'),
                    ('Stock, demand, returns, safety', 'SYNTHETIC', 'Generated, see Generation_Log'), ('Costs, contribution, MAPE', 'SYNTHETIC', 'Generated'),
                    ('Weights and bands', 'ASSUMPTION', 'Inputs sheet')],
        limits=['Depot stock, bookings and costs are synthetic; the output shows how the rule allocates, not where CMA CGM is short.',
                'Eurostat counts empties handled (in and out); reading a high empty share as surplus is an assumption.',
                'A real plan is a flow optimisation (which source to which deficit, by mode); this index only ranks the receiving depots.',
                'Leasing and street-turns are not modelled.'],
    )


# ======================= B9 Air vs sea =======================
CH9 = {'33': ('Cosmetics', 15.73), '42': ('Bags', 13.04), '61': ('Knitwear', 16.97), '62': ('Apparel woven', 23.23), '64': ('Footwear', 18.18),
       '85': ('Small electronics', 21.53), '90': ('Optical/health devices', 90.72), '91': ('Watches', 238.96), '95': ('Toys', 9.66)}


def gen_b9(seed=909):
    rng = np.random.default_rng(seed)
    lines = [('33', 2), ('42', 2), ('61', 3), ('62', 3), ('64', 2), ('85', 3), ('90', 2), ('91', 1), ('95', 2)]
    rows = []
    for ch, k in lines:
        for j in range(k):
            name, eurkg = CH9[ch]
            v = eurkg * rng.lognormal(0, 0.35)                   # value density around the chapter's real EUR/kg
            season = {'61': 10, '62': 10, '64': 12, '95': 8}.get(ch, 26) * rng.uniform(0.7, 1.3)   # selling window, weeks
            rows.append(dict(line=f'{name} {j+1}', hs=ch, eur_kg=round(v, 2), kg_month=round(rng.lognormal(8.3, 0.6), -1),
                             margin=round(rng.uniform(0.35, 0.65), 2), season_wk=round(season, 1),
                             stockout=round(rng.uniform(1, 5), 1)))
    return pd.DataFrame(rows)


def cfg_b9():
    s = gen_b9()
    b9 = pd.read_csv(D + 'anchor_B9.csv'); v = b9.pivot_table(index='product', columns='indicators', values='value')
    an = pd.DataFrame({'HS chapter': [str(i) for i in v.index], 'Product group': [CH9.get(str(i), ('Pharma' if i == 30 else 'Machinery' if i == 84 else str(i), 0))[0] for i in v.index],
                       'EU27 extra-EU imports 2025, EUR bn': (v.VALUE_IN_EUROS / 1e9).round(2).values, 'Tonnes': (v.QUANTITY_IN_100KG / 10).round(0).values,
                       'EUR per kg': (v.VALUE_IN_EUROS / (v.QUANTITY_IN_100KG * 100)).round(2).values})
    return dict(
        n=9, slug='Brief-09_Air_vs_Sea', file='Brief09_HEMA_Air_vs_Sea_Model.xlsx', colour='7A1F5C',
        title='Brief 9 - Air or sea by product line (HEMA, synthetic product lines)',
        decision='For each product line imported from Asia this season, ship by sea, by air, or split (sea base plus air top-up)?',
        who='Logistics/supply manager at a European retailer importing from Asia, reviewed every season or when rates jump.',
        company='HEMA (Dutch variety retailer: apparel, cosmetics, toys, small electronics) as the reference. Product lines are synthetic.',
        anchor_note='Eurostat Comext DS-045409: EU27 extra-EU imports 2025 by HS chapter, value and weight -> real EUR/kg by product group. Rates: TAC Index Hong Kong-Europe air (USD 4.26/kg, Oct 2026) and Drewry WCI Shanghai-Rotterdam (USD 3,504/FEU, 12 Nov 2026). LPI 2.0: import transport time and dwell, Netherlands.',
        anchor_src='Eurostat Comext DS-045409 (2025, pulled 17 Nov 2026); TAC Index via indiaseatradenews (Oct 2026); Drewry WCI via ShipUniverse (12 Nov 2026); World Bank LPI 2.0 (2024).',
        syn_note='20 product lines across nine HS chapters. Each line\'s EUR/kg is drawn around its chapter\'s real Comext EUR/kg; volume, margin, selling window and stock-out cost are generated.',
        method='Freight cost per kg by mode, transit-time carrying cost and CO2 per kg -> five criteria -> weighted Air Case Index -> bands.',
        rule_note='AIR if index >= high band; SEA if <= low band; otherwise SPLIT (sea base, air top-up).',
        private='Forwarder bookings and contract rate cards (Kuehne+Nagel, DSV), the retailer\'s ERP sell-through and markdown history, and actual chargeable weights. Public data give only chapter averages and spot indices.',
        inputs=[('W1', 'Weight - Value density (EUR/kg)', 25, 'pts', 'High value absorbs air freight.', True), ('W2', 'Weight - Air premium as % of value (lower better)', 25, 'pts', '', True),
                ('W3', 'Weight - Time sensitivity (markdown risk per week)', 20, 'pts', 'margin / selling window', True), ('W4', 'Weight - Stock-out cost index', 15, 'pts', '', True),
                ('W5', 'Weight - Extra CO2 per EUR 1,000 if air (lower better)', 15, 'pts', '', True),
                ('R1', 'Air rate HK-Europe', 4.26, 'USD/kg', 'TAC Index, Oct 2026 (indiaseatradenews). Spot, moves weekly.', True),
                ('R2', 'Sea rate Shanghai-Rotterdam', 3504, 'USD/FEU', 'Drewry WCI, 12 Nov 2026 (ShipUniverse).', True),
                ('R3', 'Chargeable kg per FEU (consumer goods, volume-limited)', 8000, 'kg', 'ASSUMPTION', True),
                ('R4', 'USD per EUR', 1.15, 'x', 'ASSUMPTION', False),
                ('T1', 'Sea door-to-door days', 41.4, 'days', 'LPI 2.0 NLD import transport time 37.5 + import dwell 3.9 (2024)', False),
                ('T2', 'Air door-to-door days', 6, 'days', 'ASSUMPTION', False), ('T3', 'Inventory carrying rate', 0.25, '%', 'ASSUMPTION, per year', False),
                ('E1', 'Air emission factor', 0.8, 'kgCO2e/tkm', 'ASSUMPTION - check GLEC Framework v3.2 default tables before use', True),
                ('E2', 'Sea emission factor', 0.015, 'kgCO2e/tkm', 'ASSUMPTION - check GLEC Framework v3.2', True),
                ('D1', 'Air distance HKG-AMS', 9300, 'km', 'Great-circle, rounded', False), ('D2', 'Sea distance Shanghai-Rotterdam', 19500, 'km', 'Via Suez, rounded', False),
                ('B1', 'AIR band (index >=)', 60, 'pts', '', True), ('B2', 'SEA band (index <=)', 40, 'pts', '', True)],
        anchor=an, synthetic=s,
        syn_labels={'line': 'Product line', 'hs': 'HS chapter', 'eur_kg': 'Value (EUR/kg)', 'kg_month': 'Volume (kg/month)', 'margin': 'Gross margin', 'season_wk': 'Selling window (weeks)', 'stockout': 'Stock-out cost index (1-5)'},
        syn_fmt={'margin': '0%', 'season_wk': '0.0', 'stockout': '0.0', 'kg_month': '#,##0'},
        item_label='Product line', scores_note='Air premium EUR/kg = (R1 - R2/R3)/R4 less carrying-cost saving (value x (T1-T2)/365 x T3). CO2 per kg by mode = factor x distance / 1000.',
        derived=[('Net air premium (EUR/kg)', '({IN:R1}-{IN:R2}/{IN:R3})/{IN:R4}-{eur_kg}*({IN:T1}-{IN:T2})/365*{IN:T3}', '0.00')],
        criteria=[dict(label='Value (EUR/kg)', f='{eur_kg}', dir=1, w='W1', fmt='#,##0.00'),
                  dict(label='Air premium % of value', f='MAX(0,B{ROW})/{eur_kg}', dir=-1, w='W2', fmt='0.0%'),
                  dict(label='Markdown risk / week', f='{margin}/{season_wk}', dir=1, w='W3', fmt='0.0%'),
                  dict(label='Stock-out index', f='{stockout}', dir=1, w='W4', fmt='0.0'),
                  dict(label='Extra kgCO2 per EUR 1k', f='({IN:E1}*{IN:D1}-{IN:E2}*{IN:D2})/1000/{eur_kg}*1000', dir=-1, w='W5', fmt='#,##0')],
        rule='IF([IDX]>={IN:B1},"AIR",IF([IDX]<={IN:B2},"SEA","SPLIT"))',
        dec_colours=[('AIR', 'D9C2E9'), ('SPLIT', 'FFEB9C'), ('SEA', 'BDD7EE')],
        summary=[('Lines by AIR', 'COUNTIF([DEC],"AIR")'), ('Lines SPLIT', 'COUNTIF([DEC],"SPLIT")'), ('Lines by SEA', 'COUNTIF([DEC],"SEA")')],
        sens=[('Base', [25, 25, 20, 15, 15]), ('Equal', [20] * 5), ('Cost-led', [20, 45, 15, 10, 10]), ('Service-led', [15, 15, 35, 25, 10]), ('Carbon-led', [20, 20, 15, 10, 35])],
        sens_count='COUNTIF([IDX],">="&Inputs!$C$21)', sens_count_label='Lines >= AIR band',
        seed=909, script='gen_b9() in briefs.py', prompt=PROMPT_BASE.format(n=9, who_short='retail supply manager choosing air or sea'),
        gen_params=[('Lines per chapter', 'Fixed', '33:2, 42:2, 61:3, 62:3, 64:2, 85:3, 90:2, 91:1, 95:2', 'Assumption: a variety retailer\'s mix'),
                    ('Value EUR/kg', 'chapter EUR/kg x lognormal(0, 0.35)', '', 'Comext 2025 EUR/kg by chapter (real)'),
                    ('Volume kg/month', 'lognormal(8.3, 0.6)', 'median ~4,000 kg', 'Assumption'),
                    ('Gross margin', 'U(0.35, 0.65)', '', 'Assumption'),
                    ('Selling window weeks', 'base x U(0.7,1.3)', 'apparel 10, footwear 12, toys 8, other 26', 'Assumption'),
                    ('Stock-out index', 'U(1, 5)', '', 'Assumption')],
        checks=[('Median EUR/kg of generated knitwear lines vs Comext ch.61', 'MEDIAN([S]C9:C11)', 'Anchor_Data!E8', 0.4),
                ('Median EUR/kg of generated electronics lines vs Comext ch.85', 'MEDIAN([S]C17:C19)', 'Anchor_Data!E13', 0.4),
                ('Mean EUR/kg of toys vs Comext ch.95', 'AVERAGE([S]C23:C24)', 'Anchor_Data!E16', 0.4)],
        code=inspect.getsource(gen_b9),
        source_key=[('Chapter EUR/kg', 'REAL (anchor)', 'Comext DS-045409 2025'), ('Air and sea rates', 'REAL (spot)', 'TAC Index (Oct 2026), Drewry WCI (12 Nov 2026)'),
                    ('Sea transit days', 'REAL (anchor)', 'LPI 2.0 NLD LT_M + CT_DT_M (2024)'), ('Emission factors, distances, FX, kg per FEU', 'ASSUMPTION', 'Inputs; check GLEC v3.2'),
                    ('Line value, volume, margin, window, stock-out', 'SYNTHETIC', 'Generated, see Generation_Log')],
        limits=['Product lines are synthetic; the split by mode illustrates the rule, not HEMA\'s actual choices.',
                'Spot rates move weekly; contract rates differ.', 'Emission factors are placeholders until checked against GLEC v3.2.',
                'Air premium uses one origin (Hong Kong/Shanghai); Bangladesh or Viet Nam lanes differ.'],
    )


# ======================= B13 Supplier transport emissions =======================
ORIG13 = {'CN': ('China', 'sea', 19500, 0), 'PL': ('Poland', 'road', 900, 241), 'DE': ('Germany', 'road', 300, 101), 'IT': ('Italy', 'road', 1100, 137),
          'LT': ('Lithuania', 'road', 1400, 480), 'CZ': ('Czechia', 'road', 700, 159), 'TR': ('Türkiye', 'sea', 6200, 0), 'ES': ('Spain', 'road', 1600, 165),
          'RO': ('Romania', 'road', 1800, 209), 'VN': ('Viet Nam', 'sea', 18500, 0), 'IN': ('India', 'sea', 11800, 0)}


def gen_b13(anchor, seed=1313):
    rng = np.random.default_rng(seed)
    w = anchor.set_index('code').tonnes; p = w / w.sum()
    origins = rng.choice(list(p.index), 30, p=p.values)            # supplier origins in proportion to real HS 94 import tonnes
    rows = []
    for i, o in enumerate(origins):
        name, mode, km, haul = ORIG13[o]
        t = rng.lognormal(7.2, 0.8)                                  # tonnes a year (median ~1,300 t)
        first = haul * rng.uniform(0.6, 1.4) if haul else rng.uniform(150, 900)   # first-mile road km: national average haul (Eurostat)
        rows.append(dict(supplier=f'S{i+1:02d} {name}', origin=o, mode=mode, tonnes=round(t), road_km=round(first + (km if mode == 'road' else 250)),
                         sea_km=km if mode == 'sea' else 0, eur_kg=round(float(anchor.set_index('code').eur_kg[o]) * rng.uniform(0.8, 1.25), 2),
                         primary=int(rng.random() < 0.35)))
    return pd.DataFrame(rows)


def cfg_b13():
    c = pd.read_csv(D + 'anchor_B13C.csv'); v = c.pivot_table(index='partner', columns='indicators', values='value')
    r = pd.read_csv(D + 'anchor_B13R.csv'); hp = r.pivot_table(index='geo', columns='unit', values='value'); haul = (hp.MIO_TKM * 1e3 / hp.THS_T)
    codes = list(ORIG13)
    an = pd.DataFrame({'code': codes, 'origin': [ORIG13[k][0] for k in codes], 'tonnes': [round(v.QUANTITY_IN_100KG[k] / 10) for k in codes],
                       'eur_kg': [round(v.VALUE_IN_EUROS[k] / (v.QUANTITY_IN_100KG[k] * 100), 2) for k in codes],
                       'avg_road_haul_km': [round(haul[k]) if k in haul.index else None for k in codes]})
    s = gen_b13(an)
    return dict(
        n=13, slug='Brief-13_Supplier_Transport_Emissions', file='Brief13_IKEA_Supplier_Emissions_Model.xlsx', colour='2E6B30',
        title='Brief 13 - Which suppliers to engage first on transport emissions (IKEA, synthetic supplier lanes)',
        decision='Which six suppliers should the sustainability team engage first to cut inbound transport emissions this year?',
        who='Sustainability/logistics lead at a European furniture retailer, annual programme with quarterly review.',
        company='IKEA (Inter IKEA supply) as the reference retailer, inbound to a central-European DC. All supplier lanes are synthetic.',
        anchor_note='Eurostat Comext DS-045409: EU27 furniture imports (HS 94) 2025 by origin, tonnes and EUR/kg. Eurostat road_go_ta_tott 2024: average road haul per country (tkm / t). Truck intensity ~80 g CO2/tkm (Sixfold methodology).',
        anchor_src='Comext DS-045409 HS 94, 2025; Eurostat road_go_ta_tott 2024 (both pulled 17 Nov 2026); Sixfold carbon methodology (truck ~80 g/tkm).',
        syn_note='30 suppliers whose origins are drawn in proportion to real HS 94 import tonnes; value per kg drawn around each origin\'s real EUR/kg; first-mile road distance around the origin\'s real average haul. Tonnes and primary-data flag are generated.',
        method='tkm by mode x emission factor = tCO2e per supplier -> five criteria -> weighted Engagement Priority Index -> top N.',
        rule_note='ENGAGE for the top N by index (Inputs N1); others LATER.',
        private='Supplier shipment records and the retailer\'s TMS (weights, lanes, carriers, modes), carrier-reported primary emissions (GLEC/ISO 14083 reports), purchase spend by supplier. Public data give origin totals only.',
        inputs=[('W1', 'Weight - Total tCO2e', 35, 'pts', '', True), ('W2', 'Weight - Intensity (kgCO2e per EUR 1,000 spend)', 20, 'pts', '', True),
                ('W3', 'Weight - Mode-shift potential (road tkm on long lanes)', 20, 'pts', '', True), ('W4', 'Weight - Spend leverage (EUR m)', 15, 'pts', '', True),
                ('W5', 'Weight - Data gap (no primary data = 1)', 10, 'pts', '', True),
                ('E1', 'Road emission factor', 0.08, 'kgCO2e/tkm', 'Sixfold: typical truck about 80 g per t-km', True),
                ('E2', 'Sea emission factor', 0.015, 'kgCO2e/tkm', 'ASSUMPTION - check GLEC Framework v3.2 container defaults', True),
                ('K1', 'Long-lane threshold for mode shift', 500, 'km', 'Road legs above this are rail/barge candidates (assumption)', False),
                ('N1', 'Suppliers to engage this year', 6, 'count', '', True)],
        anchor=an, synthetic=s,
        syn_labels={'supplier': 'Supplier', 'origin': 'Origin', 'mode': 'Main mode', 'tonnes': 'Tonnes / year', 'road_km': 'Road km per tonne', 'sea_km': 'Sea km per tonne', 'eur_kg': 'Value (EUR/kg)', 'primary': 'Reports primary data (1/0)'},
        syn_fmt={'tonnes': '#,##0', 'road_km': '#,##0', 'sea_km': '#,##0'},
        item_label='Supplier', scores_note='tCO2e = tonnes x (road km x E1 + sea km x E2) / 1000. Spend = tonnes x 1,000 x EUR/kg.',
        derived=[('tCO2e', '{tonnes}*({road_km}*{IN:E1}+{sea_km}*{IN:E2})/1000', '#,##0'), ('Spend EUR m', '{tonnes}*{eur_kg}/1000', '#,##0.0')],
        criteria=[dict(label='tCO2e / year', f='B{ROW}', dir=1, w='W1', fmt='#,##0'),
                  dict(label='kgCO2e per EUR 1k', f='B{ROW}/C{ROW}', dir=1, w='W2', fmt='#,##0.0'),
                  dict(label='Long road tkm (k)', f='IF({road_km}>{IN:K1},{tonnes}*{road_km}/1000,0)', dir=1, w='W3', fmt='#,##0'),
                  dict(label='Spend EUR m', f='C{ROW}', dir=1, w='W4', fmt='#,##0.0'),
                  dict(label='Data gap', f='1-{primary}', dir=1, w='W5', fmt='0')],
        rule='IF([RANK]<={IN:N1},"ENGAGE","LATER")',
        dec_colours=[('ENGAGE', 'C6EFCE'), ('LATER', 'EDEDED')],
        summary=[('Suppliers to ENGAGE', 'COUNTIF([DEC],"ENGAGE")'), ('Share of total tCO2e covered', 'SUMIF([DEC],"ENGAGE",Scores!B5:B34)/SUM(Scores!B5:B34)')],
        sens=[('Base', [35, 20, 20, 15, 10]), ('Equal', [20] * 5), ('Volume-led', [55, 10, 15, 10, 10]), ('Quick-win', [20, 15, 40, 10, 15]), ('Leverage-led', [25, 15, 15, 35, 10])],
        sens_count='SUMPRODUCT(([RANK]<=Inputs!$C$13)*Scores!$B$5:$B$34)/SUM(Scores!$B$5:$B$34)', sens_count_label='tCO2e share covered',
        seed=1313, script='gen_b13() in briefs.py', prompt=PROMPT_BASE.format(n=13, who_short='retail sustainability lead'),
        gen_params=[('Supplier origin', 'Categorical, p = origin share of HS 94 tonnes', '30 suppliers', 'Comext 2025 tonnes by origin (real)'),
                    ('Tonnes / year', 'lognormal(7.2, 0.8)', 'median ~1,300 t', 'Assumption'),
                    ('First-mile road km', 'national avg haul x U(0.6,1.4); non-EU U(150,900)', '', 'Eurostat road_go_ta_tott average haul (real)'),
                    ('Linehaul km', 'Fixed by origin', 'road EU lanes; sea for CN, VN, IN, TR + 250 km road', 'Assumption (rounded distances to a central-European DC)'),
                    ('Value EUR/kg', 'origin EUR/kg x U(0.8,1.25)', '', 'Comext 2025 EUR/kg by origin (real)'),
                    ('Primary data flag', 'Bernoulli', 'p = 0.35', 'Assumption')],
        checks=[('Share of suppliers from China vs China share of HS 94 tonnes', 'COUNTIF([S]B[R0]:B[RN],"CN")/30', 'Anchor_Data!C5/SUM(Anchor_Data!C5:C15)', 0.35),
                ('Mean EUR/kg of suppliers vs tonnage-weighted anchor', 'AVERAGE([S]G[R0]:G[RN])', 'SUMPRODUCT(Anchor_Data!C5:C15,Anchor_Data!D5:D15)/SUM(Anchor_Data!C5:C15)', 0.2)],
        code=inspect.getsource(gen_b13),
        source_key=[('Origin mix, EUR/kg', 'REAL (anchor)', 'Comext HS 94 2025'), ('Average road haul', 'REAL (anchor)', 'Eurostat road_go_ta_tott 2024'),
                    ('Road factor 80 g/tkm', 'REAL (cited typical)', 'Sixfold methodology'), ('Sea factor, linehaul distances', 'ASSUMPTION', 'Inputs / generator'),
                    ('Supplier tonnes, primary-data flag', 'SYNTHETIC', 'Generated, see Generation_Log')],
        limits=['Suppliers are synthetic; the list shows how the rule picks, not IKEA\'s real suppliers.',
                'Emission factors are single defaults per mode; real factors vary by vehicle, load and fuel.',
                'Distances are rounded country-level lanes.', 'Engagement feasibility (relationship, contract renewal) is not modelled.'],
    )


# ======================= B15 DC reorganisation =======================
CAT15 = {'95': ('Toys', 0.012), '94': ('Home & furniture', 0.030), '61': ('Knitwear', 0.004), '62': ('Apparel woven', 0.004),
         '64': ('Footwear', 0.008), '42': ('Bags', 0.006), '33': ('Cosmetics', 0.0015), '85': ('Small electronics', 0.005)}


def gen_b15(season, seed=1515):
    rng = np.random.default_rng(seed)
    mix = {'95': 7, '94': 6, '61': 5, '62': 4, '64': 4, '42': 3, '33': 6, '85': 5}
    rows = []
    for ch, k in mix.items():
        idx = season[ch]                                            # real monthly seasonal index from Comext imports
        for j in range(k):
            base = rng.lognormal(6.3, 0.7)                          # picks per week in an average month
            cube = CAT15[ch][1] * rng.lognormal(0, 0.4)             # m3 per pick
            rows.append(dict(family=f'{CAT15[ch][0]} {j+1}', hs=ch, picks_wk=round(base), peak_idx=round(max(idx), 2), low_idx=round(min(idx), 2),
                             cube=round(cube, 4), affinity=round(rng.beta(2, 4), 2), slots=int(rng.integers(2, 9))))
    return pd.DataFrame(rows)


def cfg_b15():
    b = pd.read_csv(D + 'anchor_B15.csv'); b['m'] = b.time.str[-2:].astype(int)
    mean = b.groupby(['product', 'm']).value.mean().unstack()
    si = mean.div(mean.mean(axis=1), axis=0).round(3)
    season = {str(k): list(si.loc[k]) for k in si.index}
    an = si.reset_index().rename(columns={'product': 'HS chapter'}); an.columns = ['HS chapter'] + ['M' + str(m) for m in range(1, 13)]
    an.insert(1, 'Group', [CAT15[str(c)][0] for c in an['HS chapter']]); an['HS chapter'] = an['HS chapter'].astype(str)
    an['Peak'] = si.max(axis=1).values; an['Low'] = si.min(axis=1).values
    s = gen_b15(season)
    return dict(
        n=15, slug='Brief-15_DC_Golden_Zone', file='Brief15_Action_DC_Slotting_Model.xlsx', colour='B4462B',
        title='Brief 15 - Which product families go in the fast-pick zone (Action DC, synthetic pick data)',
        decision='Ahead of the autumn peak, which product families move into the limited fast-pick ("golden") zone next to dispatch, and which stay in reserve racking?',
        who='DC operations manager at a non-food discount retailer, re-slotting before each season.',
        company='Action (Dutch non-food discounter; DC network in NL, FR, DE, PL) as the reference. Pick data are synthetic.',
        anchor_note='Eurostat Comext DS-045409: EU27 extra-EU monthly imports 2022-2025 by HS chapter -> real seasonal index per product group (toys peak at 1.36 in September).',
        anchor_src='Comext DS-045409, freq M, 2022-01 to 2025-12, EU27 imports from extra-EU, value (pulled 17 Nov 2026).',
        syn_note='40 SKU families in eight groups. Picks per week, cube per pick, order affinity and slot need are generated; each family carries its group\'s real seasonal peak and low index.',
        method='Peak-season picks, cube, stability, affinity and replenishment -> weighted Slotting Index -> fill the golden zone in rank order until its slot capacity is used.',
        rule_note='GOLDEN ZONE if the cumulative slots of all families ranked at or above it fit within capacity (Inputs C1); otherwise RESERVE.',
        private='The WMS pick log (Manhattan, Blue Yonder, SAP EWM): every order line, location, pick time and replenishment task; item master with dimensions. None of it is public; import seasonality is only a proxy for outbound picks.',
        inputs=[('W1', 'Weight - Peak picks per week', 35, 'pts', '', True), ('W2', 'Weight - Cube per pick (lower better)', 20, 'pts', '', True),
                ('W3', 'Weight - Pick stability (low/peak index, higher better)', 15, 'pts', '', True), ('W4', 'Weight - Order affinity', 15, 'pts', 'Share of orders also holding a top family', True),
                ('W5', 'Weight - Replenishment trips per week (lower better)', 15, 'pts', '', True),
                ('C1', 'Golden-zone capacity', 90, 'slots', 'ASSUMPTION', True), ('C2', 'Slot volume', 1.2, 'm3', 'ASSUMPTION (pallet-flow lane)', False)],
        anchor=an, synthetic=s,
        syn_labels={'family': 'SKU family', 'hs': 'HS chapter', 'picks_wk': 'Picks / week (avg month)', 'peak_idx': 'Peak seasonal index', 'low_idx': 'Low seasonal index', 'cube': 'm3 per pick', 'affinity': 'Order affinity', 'slots': 'Slots needed'},
        syn_fmt={'cube': '0.0000', 'affinity': '0%', 'picks_wk': '#,##0'},
        item_label='SKU family', scores_note='Peak picks = picks x peak index. Replenishment trips = peak picks x cube / (slots x slot volume).',
        derived=[('Peak picks / week', '{picks_wk}*{peak_idx}', '#,##0')],
        criteria=[dict(label='Peak picks / week', f='B{ROW}', dir=1, w='W1', fmt='#,##0'),
                  dict(label='m3 per pick', f='{cube}', dir=-1, w='W2', fmt='0.0000'),
                  dict(label='Stability', f='{low_idx}/{peak_idx}', dir=1, w='W3', fmt='0.00'),
                  dict(label='Affinity', f='{affinity}', dir=1, w='W4', fmt='0%'),
                  dict(label='Replen trips / week', f='B{ROW}*{cube}/({slots}*{IN:C2})', dir=-1, w='W5', fmt='0.0')],
        rule='IF(SUMIF([RANKS],"<="&[RANK],Synthetic_Data!$H$5:$H$44)<={IN:C1},"GOLDEN ZONE","RESERVE")',
        dec_colours=[('GOLDEN ZONE', 'FFD966'), ('RESERVE', 'EDEDED')],
        summary=[('Families in golden zone', 'COUNTIF([DEC],"GOLDEN ZONE")'), ('Slots used', 'SUMIF([DEC],"GOLDEN ZONE",Synthetic_Data!H5:H44)'),
                 ('Share of peak picks served from golden zone', 'SUMIF([DEC],"GOLDEN ZONE",Scores!B5:B44)/SUM(Scores!B5:B44)')],
        sens=[('Base', [35, 20, 15, 15, 15]), ('Equal', [20] * 5), ('Volume-led', [55, 15, 10, 10, 10]), ('Space-led', [25, 40, 10, 10, 15]), ('Stability-led', [25, 15, 35, 10, 15])],
        sens_count=None,
        seed=1515, script='gen_b15() in briefs.py', prompt=PROMPT_BASE.format(n=15, who_short='DC operations manager'),
        gen_params=[('Families per group', 'Fixed', 'toys 7, home 6, knitwear 5, woven 4, footwear 4, bags 3, cosmetics 6, electronics 5', 'Assumption: discounter mix'),
                    ('Seasonal peak / low index', 'max / min of monthly index', '', 'Comext monthly imports 2022-2025 (real)'),
                    ('Picks per week', 'lognormal(6.3, 0.7)', 'median ~545', 'Assumption'),
                    ('m3 per pick', 'group base x lognormal(0, 0.4)', 'toys 0.012, home 0.030, apparel 0.004 ...', 'Assumption'),
                    ('Order affinity', 'Beta(2, 4)', 'mean 0.33', 'Assumption'), ('Slots needed', 'integer U[2, 8]', '', 'Assumption')],
        checks=[('Highest family peak index = highest group peak in Comext (toys)', 'MAX([S]D[R0]:D[RN])', 'MAX(Anchor_Data!O5:O12)', 0.01),
                ('Mean peak index across families vs anchor mean of group peaks', 'AVERAGE([S]D[R0]:D[RN])', 'AVERAGE(Anchor_Data!O5:O12)', 0.15)],
        code=inspect.getsource(gen_b15),
        source_key=[('Monthly seasonal index by group', 'REAL (anchor)', 'Comext monthly imports, extra-EU, 2022-2025'),
                    ('Picks, cube, affinity, slots', 'SYNTHETIC', 'Generated, see Generation_Log'), ('Capacity, slot volume, weights', 'ASSUMPTION', 'Inputs')],
        limits=['Pick data are synthetic; import seasonality stands in for outbound demand, which leads it by weeks.',
                'Real slotting also weighs ergonomics, weight, hazmat and pick-path; not modelled.',
                'The greedy fill by rank can leave a few slots unused.', 'Re-slotting cost (labour moves) is not included.'],
    )


# ======================= B18 Safety stock =======================
ORIG18 = {'CHN': 35, 'VNM': 33, 'IND': 28, 'IDN': 32, 'BGD': 38, 'TUR': 12, 'MAR': 6, 'BRA': 22, 'USA': 14}


def gen_b18(seed=1818):
    rng = np.random.default_rng(seed)
    org = rng.choice(list(ORIG18), 15, p=[0.30, 0.15, 0.10, 0.08, 0.07, 0.10, 0.06, 0.07, 0.07])
    rows = []
    for i, o in enumerate(org):
        d = rng.lognormal(4.0, 0.7)                                  # units per day
        rows.append(dict(line=f'L{i+1:02d}', origin=o, transit=ORIG18[o], transit_sd=round(ORIG18[o] * rng.uniform(0.08, 0.2), 1),
                         d_day=round(d, 1), d_cv=round(rng.uniform(0.2, 0.9), 2), unit_eur=round(rng.lognormal(3.0, 0.8), 2),
                         margin=round(rng.uniform(0.2, 0.6), 2), ss_now=round(d * rng.uniform(3, 14))))
    return pd.DataFrame(rows)


def cfg_b18():
    lpi = pd.read_csv('/mnt/user-data/uploads/0b709e74-WB_LPI_20.csv')
    x = lpi[(lpi.TIME_PERIOD == 2024) & lpi.INDICATOR.isin(['CT_DT_X', 'CT_DT_M'])]
    p = x.pivot_table(index='REF_AREA', columns=['INDICATOR', 'METRIC'], values='OBS_VALUE')
    codes = list(ORIG18)
    an = pd.DataFrame({'code': codes, 'export_dwell_median': [p.loc[c, ('CT_DT_X', 'MD')] for c in codes], 'export_dwell_IQR': [p.loc[c, ('CT_DT_X', 'IQR_75_25')] for c in codes]})
    an = pd.concat([an, pd.DataFrame({'code': ['NLD (import)'], 'export_dwell_median': [p.loc['NLD', ('CT_DT_M', 'MD')]], 'export_dwell_IQR': [p.loc['NLD', ('CT_DT_M', 'IQR_75_25')]]})], ignore_index=True)
    an = an.rename(columns={'export_dwell_median': 'dwell_median_days', 'export_dwell_IQR': 'dwell_IQR_days'})
    s = gen_b18()
    return dict(
        n=18, slug='Brief-18_Safety_Stock', file='Brief18_Philips_Safety_Stock_Model.xlsx', colour='3B4CA8',
        title='Brief 18 - Where to raise or cut safety stock (Philips EU DC, synthetic product lines)',
        decision='For each imported product line, should safety stock at the European DC be raised, held or cut, given how variable the inbound lead time really is?',
        who='Inventory/supply planner at a manufacturer importing finished goods into a Dutch DC, monthly review.',
        company='Philips (consumer health products into its EU distribution centre in the Netherlands) as the reference. Product lines are synthetic.',
        anchor_note='World Bank LPI 2.0 (2024): container export dwell by origin and import dwell in the Netherlands, median and inter-quartile range. These drive the lead-time variability in the formula.',
        anchor_src='World Bank LPI 2.0 indicators CT_DT_X and CT_DT_M, 2024 (user upload).',
        syn_note='15 product lines sourced from nine origins. Daily demand, its variability, unit cost, margin, current safety stock and transit-time spread are generated; dwell variability comes from the real LPI quartiles.',
        method='Lead time = origin export dwell + transit + NL import dwell; sigma from IQR/1.349. Required safety stock = z x sqrt(LT x sd_d^2 + d^2 x sd_LT^2). Gap vs current -> five criteria -> priority index -> RAISE / HOLD / CUT.',
        rule_note='CUT if current stock exceeds requirement by more than Inputs X1; RAISE if there is a gap and index >= Inputs B1; otherwise HOLD.',
        private='ERP lead-time history per purchase order (SAP), carrier and forwarder milestones (project44, FourKites), and demand history by SKU. LPI gives country medians only.',
        inputs=[('W1', 'Weight - Gap value (EUR)', 30, 'pts', '', True), ('W2', 'Weight - Lead-time sigma (days)', 20, 'pts', '', True),
                ('W3', 'Weight - Demand volatility (CV)', 15, 'pts', '', True), ('W4', 'Weight - Margin (criticality proxy)', 20, 'pts', '', True),
                ('W5', 'Weight - Coverage shortfall (% of requirement)', 15, 'pts', '', True),
                ('Z1', 'Service level z (97.5%)', 1.96, 'z', 'Target cycle service level', True), ('X1', 'Excess tolerance before CUT', 0.25, '%', 'Assumption', False),
                ('B1', 'RAISE band (index >=)', 45, 'pts', '', True)],
        anchor=an, synthetic=s,
        syn_labels={'line': 'Line', 'origin': 'Origin', 'transit': 'Sea/road transit (days)', 'transit_sd': 'Transit sd (days)', 'd_day': 'Demand (units/day)', 'd_cv': 'Demand CV', 'unit_eur': 'Unit cost (EUR)', 'margin': 'Margin', 'ss_now': 'Current safety stock (units)'},
        syn_fmt={'d_cv': '0.00', 'margin': '0%', 'ss_now': '#,##0'},
        item_label='Line', scores_note='LT mean = export dwell median + transit + NL import dwell median. sd_LT = sqrt((IQR_exp/1.349)^2 + transit_sd^2 + (IQR_imp/1.349)^2).',
        derived=[('LT mean (days)', 'VLOOKUP({origin},{AN:$A$5:$C$14},2,FALSE)+{transit}+{AN:$B$14}', '0.0'),
                 ('LT sd (days)', 'SQRT((VLOOKUP({origin},{AN:$A$5:$C$14},3,FALSE)/1.349)^2+{transit_sd}^2+({AN:$C$14}/1.349)^2)', '0.0'),
                 ('Required SS (units)', '{IN:Z1}*SQRT(B{ROW}*({d_day}*{d_cv})^2+{d_day}^2*C{ROW}^2)', '#,##0')],
        criteria=[dict(label='Gap value (EUR)', f='MAX(0,D{ROW}-{ss_now})*{unit_eur}', dir=1, w='W1', fmt='#,##0'),
                  dict(label='LT sigma (days)', f='C{ROW}', dir=1, w='W2', fmt='0.0'),
                  dict(label='Demand CV', f='{d_cv}', dir=1, w='W3', fmt='0.00'),
                  dict(label='Margin', f='{margin}', dir=1, w='W4', fmt='0%'),
                  dict(label='Shortfall %', f='MAX(0,D{ROW}-{ss_now})/D{ROW}', dir=1, w='W5', fmt='0%')],
        rule='IF({ss_now}>D{ROW}*(1+{IN:X1}),"CUT",IF(AND({ss_now}<D{ROW},[IDX]>={IN:B1}),"RAISE","HOLD"))',
        dec_colours=[('RAISE', 'FFC7CE'), ('HOLD', 'FFEB9C'), ('CUT', 'BDD7EE')],
        summary=[('Lines to RAISE', 'COUNTIF([DEC],"RAISE")'), ('Lines to CUT', 'COUNTIF([DEC],"CUT")'),
                 ('EUR to add (RAISE lines)', 'SUMIF([DEC],"RAISE",Scores!E5:E19)'),
                 ('EUR freed (CUT lines)', 'SUMPRODUCT(([DEC]="CUT")*(Synthetic_Data!I5:I19-Scores!D5:D19)*Synthetic_Data!G5:G19)')],
        sens=[('Base', [30, 20, 15, 20, 15]), ('Equal', [20] * 5), ('Cash-led', [50, 15, 10, 10, 15]), ('Risk-led', [15, 40, 25, 10, 10]), ('Margin-led', [20, 15, 10, 45, 10])],
        sens_count=None,
        seed=1818, script='gen_b18() in briefs.py', prompt=PROMPT_BASE.format(n=18, who_short='inventory planner'),
        gen_params=[('Origin', 'Categorical', 'CHN 30%, VNM 15%, IND 10%, TUR 10%, IDN 8%, BGD 7%, BRA 7%, USA 7%, MAR 6%', 'Assumption'),
                    ('Transit days', 'Fixed by origin', 'CHN 35, VNM 33, IND 28, IDN 32, BGD 38, TUR 12, MAR 6, BRA 22, USA 14', 'Assumption (port-to-port, rounded)'),
                    ('Transit sd', 'transit x U(0.08, 0.20)', '', 'Assumption'), ('Demand units/day', 'lognormal(4.0, 0.7)', 'median ~55', 'Assumption'),
                    ('Demand CV', 'U(0.2, 0.9)', '', 'Assumption'), ('Unit cost', 'lognormal(3.0, 0.8)', 'median ~EUR 20', 'Assumption'),
                    ('Margin', 'U(0.2, 0.6)', '', 'Assumption'), ('Current SS', 'demand x U(3, 14) days', '', 'Assumption'),
                    ('Dwell median and IQR', 'Looked up, not generated', '', 'LPI 2.0 2024 (real)')],
        checks=[('Mean dwell sigma used vs LPI median IQR/1.349 (origins in data)', 'AVERAGE(Scores!C5:C19)', 'SQRT((MEDIAN(Anchor_Data!C5:C13)/1.349)^2+(Anchor_Data!C14/1.349)^2+(0.14*28)^2)', 0.35)],
        code=inspect.getsource(gen_b18),
        source_key=[('Export and import dwell median, IQR', 'REAL (anchor)', 'LPI 2.0 2024'), ('Transit days', 'ASSUMPTION', 'Rounded port-to-port times'),
                    ('Demand, CV, cost, margin, current SS, transit sd', 'SYNTHETIC', 'Generated, see Generation_Log'), ('z, tolerance, band, weights', 'ASSUMPTION', 'Inputs')],
        limits=['Product lines and current stock are synthetic.', 'LPI dwell is a country-level distribution, not a lane or carrier.',
                'Normal approximation for lead time and demand; real lead times are skewed (long right tail).', 'Review period and order cycle stock are not modelled.'],
    )


ALL = {3: cfg_b3, 4: cfg_b4, 9: cfg_b9, 13: cfg_b13, 15: cfg_b15, 18: cfg_b18}
