"""Generic workbook builder for the Phase 2 synthetic briefs.

Each brief supplies a config dict: anchor table, a seeded synthetic table, criteria as Excel
formula templates, a decision rule, sensitivity weightings and documentation. The workbook is
formula-driven: Scores and Sensitivity recalculate when Inputs or Synthetic_Data change.
Template tokens: {field} -> Synthetic_Data cell of this row; {IN:code} -> Inputs value cell;
{AN:range} -> 'Anchor_Data'!range (absolute); {ROW} -> current row number.
"""
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.formatting.rule import DataBarRule, CellIsRule
from openpyxl.comments import Comment

F = "Arial"
B = Font(name=F, size=10); BB = Font(name=F, size=10, bold=True)
INP = Font(name=F, color="0000FF", size=10); GRN = Font(name=F, size=10, color="008000")
KEY = PatternFill("solid", fgColor="FFFF00"); SYN = PatternFill("solid", fgColor="FCE4D6")
SYNH = PatternFill("solid", fgColor="C55A11"); NOTE = Font(name=F, size=9, italic=True, color="555555")
thin = Side(style="thin", color="CCCCCC"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WR = Alignment(wrap_text=True, vertical="top")
BANNER = "SYNTHETIC DATA - generated with a seeded Python script and anchored to public data. Not observed values. Never the source of a finding on its own."


def build(cfg, out):
    P = cfg["colour"]
    H = Font(name=F, bold=True, color="FFFFFF", size=10); HF = PatternFill("solid", fgColor=P)
    T = Font(name=F, size=14, bold=True, color=P)
    wb = Workbook()

    def sheet(name, title, sub=None, first=False):
        ws = wb.active if first else wb.create_sheet(name)
        ws.title = name; ws["A1"] = title; ws["A1"].font = T
        if sub: ws["A2"] = sub; ws["A2"].font = NOTE
        ws.sheet_view.showGridLines = False
        return ws

    def hdr(ws, r, labels, widths=None, fill=None):
        for i, t in enumerate(labels, 1):
            c = ws.cell(r, i, t); c.font = H; c.fill = fill or HF; c.border = BOX
            c.alignment = Alignment(wrap_text=True, vertical="center")
        if widths:
            for i, w in enumerate(widths, 1): ws.column_dimensions[L(i)].width = w
        ws.row_dimensions[r].height = 42

    def banner(ws, r=2):
        ws.cell(r, 1, BANNER).font = Font(name=F, size=10, bold=True, color="FFFFFF")
        for c in range(1, 12): ws.cell(r, c).fill = SYNH

    # ---------- README ----------
    ws = sheet("README", cfg["title"], first=True); banner(ws)
    rows = [("Decision", cfg["decision"]), ("Decision-maker", cfg["who"]), ("Company", cfg["company"]),
            ("Real anchor data", cfg["anchor_note"]), ("Synthetic data", cfg["syn_note"]), ("Method", cfg["method"]),
            ("Decision rule", cfg["rule_note"]), ("Private equivalent", cfg["private"]),
            ("Labelling", "Every synthetic field sits on Synthetic_Data (orange header, banner) and is marked SYNTHETIC on Source_Key. Findings are stated as what the model does with anchored data, never as facts about the company."),
            ("Colour code", "Blue = input; black = formula; green = cross-sheet link; yellow fill = key assumption; orange = synthetic.")]
    for i, (k, v) in enumerate(rows, 4):
        ws.cell(i, 1, k).font = BB; c = ws.cell(i, 2, v); c.font = B; c.alignment = WR
        ws.row_dimensions[i].height = max(30, 15 * (len(v) // 120 + 1))
    ws.column_dimensions["A"].width = 18; ws.column_dimensions["B"].width = 125

    # ---------- Inputs ----------
    wi = sheet("Inputs", "Inputs - change the blue cells")
    hdr(wi, 4, ["Code", "Parameter", "Value", "Unit", "Note / source"], [8, 50, 14, 10, 95])
    IN = {}; r = 5
    for code, name, val, unit, note, key in cfg["inputs"]:
        wi.cell(r, 1, code).font = BB; wi.cell(r, 2, name).font = B
        c = wi.cell(r, 3, val); c.font = INP
        if key: c.fill = KEY
        if isinstance(val, float) and val < 1: c.number_format = "0.0%" if unit == "%" else "0.000"
        elif isinstance(val, (int, float)): c.number_format = "#,##0.##"
        wi.cell(r, 4, unit).font = B; n = wi.cell(r, 5, note); n.font = B; n.alignment = WR
        IN[code] = f"Inputs!$C${r}"; r += 1
    wi.cell(r, 2, "Sum of weights (normalised automatically)").font = BB
    wcodes = [c["w"] for c in cfg["criteria"]]
    wi.cell(r, 3, "=" + "+".join(IN[w] for w in wcodes)).font = BB
    IN["WSUM"] = f"Inputs!$C${r}"

    # ---------- Anchor_Data ----------
    wa = sheet("Anchor_Data", "Anchor data - real, public", cfg["anchor_src"])
    a = cfg["anchor"]
    hdr(wa, 4, list(a.columns), [max(12, min(40, len(str(c)) + 6)) for c in a.columns])
    for i, row in enumerate(a.itertuples(index=False), 5):
        for j, v in enumerate(row, 1):
            c = wa.cell(i, j, None if (isinstance(v, float) and v != v) else v); c.font = B
            if isinstance(v, float): c.number_format = "#,##0.00"
    AN_END = 4 + len(a)

    # ---------- Synthetic_Data ----------
    wsy = sheet("Synthetic_Data", "Synthetic data - generated, not observed"); banner(wsy)
    s = cfg["synthetic"]; cols = list(s.columns)
    hdr(wsy, 4, [cfg["syn_labels"].get(c, c) for c in cols], [max(11, min(30, len(cfg["syn_labels"].get(c, c)) * 0.6 + 4)) for c in cols], fill=SYNH)
    R0 = 5; N = len(s); RN = R0 + N - 1
    COL = {c: L(j) for j, c in enumerate(cols, 1)}
    for i, row in enumerate(s.itertuples(index=False), R0):
        for j, v in enumerate(row, 1):
            c = wsy.cell(i, j, v.item() if hasattr(v, "item") else v); c.font = INP if j > 1 else BB; c.fill = SYN if j > 1 else PatternFill()
            if isinstance(v, float): c.number_format = cfg.get("syn_fmt", {}).get(cols[j - 1], "#,##0.00")
    wsy.freeze_panes = "B5"

    def sub(tpl, r):
        def rep(m):
            k = m.group(1)
            if k.startswith("IN:"): return IN[k[3:]]
            if k.startswith("AN:"): return "Anchor_Data!" + k[3:]
            if k == "ROW": return str(r)
            return f"Synthetic_Data!{COL[k]}{r}"
        return re.sub(r"\{([^}]+)\}", rep, tpl)

    # ---------- Scores ----------
    wsc = sheet("Scores", "Scores - criteria, 0-100 scaling, weighted index and decision", cfg["scores_note"])
    crit = cfg["criteria"]; nC = len(crit)
    extra = cfg.get("derived", [])   # helper columns before criteria: (label, template, fmt)
    labels = [cfg["item_label"]] + [d[0] for d in extra] + [c["label"] for c in crit] + [f"S{i+1} score" for i in range(nC)] + ["Index", "Rank", "Decision"]
    widths = [16] + [14] * len(extra) + [16] * nC + [10] * nC + [10, 8, 22]
    hdr(wsc, 4, labels, widths)
    cD = 2; cC = cD + len(extra); cS = cC + nC; cI = cS + nC; cR = cI + 1; cDec = cR + 1
    for r in range(R0, RN + 1):
        c = wsc.cell(r, 1, f"=Synthetic_Data!A{r}"); c.font = GRN
        for k, (lab, tpl, fmt) in enumerate(extra):
            c = wsc.cell(r, cD + k, "=" + sub(tpl, r)); c.font = B; c.number_format = fmt
        for k, cr in enumerate(crit):
            c = wsc.cell(r, cC + k, "=" + sub(cr["f"], r)); c.font = B; c.number_format = cr.get("fmt", "#,##0.00")
        for k, cr in enumerate(crit):
            col = L(cC + k); rng = f"${col}${R0}:${col}${RN}"; x = f"{col}{r}"
            num = f"({x}-MIN({rng}))" if cr["dir"] > 0 else f"(MAX({rng})-{x})"
            c = wsc.cell(r, cS + k, f"=IF(MAX({rng})=MIN({rng}),50,{num}/(MAX({rng})-MIN({rng}))*100)"); c.font = B; c.number_format = "0.0"
        sc = f"{L(cS)}{r}:{L(cS+nC-1)}{r}"
        wts = ",".join(IN[w] for w in wcodes)
        el = f"*{L(cDec+1)}{r}" if cfg.get("eligible") else ""
        if el:
            wsc.cell(4, cDec + 1, "Scored (1) or surplus (0)").font = H; wsc.cell(4, cDec + 1).fill = HF
            wsc.cell(r, cDec + 1, "=" + sub(cfg["eligible"], r)).font = B
        c = wsc.cell(r, cI, "=(" + "+".join(f"{L(cS+k)}{r}*{IN[cr['w']]}" for k, cr in enumerate(crit)) + f")/{IN['WSUM']}" + el); c.font = BB; c.number_format = "0.0"
        ir = f"${L(cI)}${R0}:${L(cI)}${RN}"
        c = wsc.cell(r, cR, f"=RANK({L(cI)}{r},{ir},0)+COUNTIF(${L(cI)}${R0}:{L(cI)}{r},{L(cI)}{r})-1"); c.font = B
        c = wsc.cell(r, cDec, "=" + sub(cfg["rule"], r).replace("[IDX]", f"{L(cI)}{r}").replace("[RANK]", f"{L(cR)}{r}")
                     .replace("[RANKS]", f"${L(cR)}${R0}:${L(cR)}${RN}")); c.font = BB
    wsc.conditional_formatting.add(f"{L(cI)}{R0}:{L(cI)}{RN}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=100, color=P))
    for txt, col in cfg["dec_colours"]:
        wsc.conditional_formatting.add(f"{L(cDec)}{R0}:{L(cDec)}{RN}", CellIsRule(operator="equal", formula=[f'"{txt}"'], fill=PatternFill("solid", fgColor=col)))
    wsc.freeze_panes = "B5"
    # summary block under the table
    r = RN + 3
    wsc.cell(r, 1, "Summary").font = BB
    for k, (lab, f) in enumerate(cfg.get("summary", [])):
        wsc.cell(r + 1 + k, 1, lab).font = B
        c = wsc.cell(r + 1 + k, 3, "=" + f.replace("[DEC]", f"${L(cDec)}${R0}:${L(cDec)}${RN}").replace("[IDXR]", f"${L(cI)}${R0}:${L(cI)}${RN}")
                     .replace("[ITEMS]", f"$A${R0}:$A${RN}").replace("[RANKS]", f"${L(cR)}${R0}:${L(cR)}${RN}")); c.font = BB

    # ---------- Ranked view ----------
    wr = sheet("Ranked", "Ranked view (sorted by formula)")
    hdr(wr, 4, ["Rank", cfg["item_label"], "Index", "Decision"] + [c["label"] for c in crit], [7, 18, 9, 22] + [15] * nC)
    for k in range(N):
        r = R0 + k
        wr.cell(r, 1, k + 1).font = B
        m = f"MATCH($A{r},Scores!${L(cR)}${R0}:${L(cR)}${RN},0)"
        for j, col in enumerate([1, cI, cDec] + [cC + q for q in range(nC)]):
            c = wr.cell(r, 2 + j, f"=INDEX(Scores!${L(col)}${R0}:${L(col)}${RN},{m})"); c.font = GRN
            if j == 1: c.number_format = "0.0"
            elif j >= 3: c.number_format = crit[j - 3].get("fmt", "#,##0.00")

    # ---------- Sensitivity ----------
    wse = sheet("Sensitivity", "Sensitivity - does the answer survive other weightings?", "Weights per row; index and rank recalculate from the S-scores on Scores.")
    sets = cfg["sens"]; lay_dec = cDec
    hdr(wse, 4, ["Weighting"] + [c["label"] for c in crit] + ["No. 1", "No. 2", "No. 3", cfg.get("sens_count_label", "Count flagged")], [26] + [11] * nC + [16, 16, 16, 14])
    # hidden helper grid: index per item per set, starting col 20
    HC = 20
    for si, (nm, ws_) in enumerate(sets):
        r = 5 + si
        wse.cell(r, 1, nm).font = BB
        for k, w in enumerate(ws_):
            c = wse.cell(r, 2 + k, w); c.font = INP
    for si in range(len(sets)):
        r = 5 + si; wr_ = f"$B${r}:${L(1+nC)}${r}"
        icol = L(HC + 2 * si); rcol = L(HC + 2 * si + 1)
        wse.cell(4, HC + 2 * si, f"Idx {si+1}").font = BB; wse.cell(4, HC + 2 * si + 1, f"Rank {si+1}").font = BB
        for k in range(N):
            rr = R0 + 10 + k
            if si == 0: wse.cell(rr, HC - 1, f"=Scores!A{R0+k}").font = GRN
            c = wse.cell(rr, HC + 2 * si, f"=SUMPRODUCT({wr_},Scores!{L(cS)}{R0+k}:{L(cS+nC-1)}{R0+k})/SUM({wr_})" + (f"*Scores!{L(lay_dec+1)}{R0+k}" if cfg.get("eligible") else "")); c.number_format = "0.0"
            rng = f"${icol}${R0+10}:${icol}${R0+9+N}"
            wse.cell(rr, HC + 2 * si + 1, f"=RANK({icol}{rr},{rng},0)+COUNTIF(${icol}${R0+10}:{icol}{rr},{icol}{rr})-1")
        for p in range(3):
            c = wse.cell(r, 2 + nC + p, f"=INDEX(${L(HC-1)}${R0+10}:${L(HC-1)}${R0+9+N},MATCH({p+1},${rcol}${R0+10}:${rcol}${R0+9+N},0))"); c.font = BB if p == 0 else B
        cnt = cfg.get("sens_count")
        if cnt:
            c = wse.cell(r, 5 + nC, "=" + cnt.replace("[IDX]", f"${icol}${R0+10}:${icol}${R0+9+N}").replace("[RANK]", f"${rcol}${R0+10}:${rcol}${R0+9+N}")); c.font = B
    wse.cell(4 + len(sets) + 2, 1, "Helper grid (columns S onward): index and rank of every item under each weighting.").font = NOTE

    # ---------- Generation_Log ----------
    wg = sheet("Generation_Log", "Generation log - how the synthetic data was made (reproducible)"); banner(wg)
    rr = 4
    for k, v in [("Tool", "Python 3.13, numpy.random.default_rng (PCG64), pandas. Script: " + cfg["script"]),
                 ("Seed", str(cfg["seed"])), ("Generated", "17 Nov 2026, by Claude (Anthropic), at the user's request"),
                 ("Prompt (verbatim)", cfg["prompt"])]:
        wg.cell(rr, 1, k).font = BB; c = wg.cell(rr, 2, v); c.font = B; c.alignment = WR
        wg.row_dimensions[rr].height = max(18, 14 * (len(v) // 110 + 1)); rr += 1
    rr += 1; wg.cell(rr, 1, "Parameters").font = T; rr += 1
    hdr(wg, rr, ["Field", "Distribution / rule", "Parameters", "Anchor"], [22, 60, 40, 60]); rr += 1
    for row in cfg["gen_params"]:
        for j, v in enumerate(row, 1):
            c = wg.cell(rr, j, v); c.font = B; c.alignment = WR
        wg.row_dimensions[rr].height = 30; rr += 1
    rr += 1; wg.cell(rr, 1, "Validation against the anchor").font = T; rr += 1
    hdr(wg, rr, ["Check", "Synthetic value", "Anchor value", "Tolerance", "Result"]); rr += 1
    for lab, fs, fa, tol in cfg["checks"]:
        wg.cell(rr, 1, lab).font = B; wg.cell(rr, 1).alignment = WR
        c = wg.cell(rr, 2, "=" + fs.replace("[S]", "Synthetic_Data!").replace("[R0]", str(R0)).replace("[RN]", str(RN))); c.font = GRN; c.number_format = "#,##0.00"
        c = wg.cell(rr, 3, fa if not isinstance(fa, str) else "=" + fa); c.font = GRN if isinstance(fa, str) else INP; c.number_format = "#,##0.00"
        c = wg.cell(rr, 4, tol); c.font = INP; c.number_format = "0%"
        c = wg.cell(rr, 5, f'=IF(ABS(B{rr}-C{rr})<=D{rr}*ABS(C{rr}),"PASS","CHECK")'); c.font = BB
        wg.row_dimensions[rr].height = 28; rr += 1
    wg.conditional_formatting.add(f"E1:E{rr}", CellIsRule(operator="equal", formula=['"PASS"'], fill=PatternFill("solid", fgColor="C6EFCE")))
    wg.conditional_formatting.add(f"E1:E{rr}", CellIsRule(operator="equal", formula=['"CHECK"'], fill=PatternFill("solid", fgColor="FFC7CE")))
    rr += 1; wg.cell(rr, 1, "Generator code (verbatim)").font = T; rr += 1
    for line in cfg["code"].splitlines():
        c = wg.cell(rr, 1, line if line.strip() else ""); c.font = Font(name="Courier New", size=9); rr += 1

    # ---------- Source_Key ----------
    wk = sheet("Source_Key", "Source key - which fields are real, which are generated")
    hdr(wk, 4, ["Field", "Status", "Source / rule"], [30, 16, 110])
    for i, (f_, st, src) in enumerate(cfg["source_key"], 5):
        wk.cell(i, 1, f_).font = B; c = wk.cell(i, 2, st); c.font = BB
        c.fill = SYN if st == "SYNTHETIC" else (KEY if st == "ASSUMPTION" else PatternFill("solid", fgColor="C6EFCE"))
        n = wk.cell(i, 3, src); n.font = B; n.alignment = WR

    # ---------- Limitations ----------
    wl = sheet("Limitations", "Limitations")
    for i, t in enumerate(cfg["limits"], 3):
        wl.cell(i, 1, f"{i-2}.").font = BB; c = wl.cell(i, 2, t); c.font = B; c.alignment = WR; wl.row_dimensions[i].height = 30
    wl.column_dimensions["B"].width = 130

    wb.save(out)
    return dict(R0=R0, RN=RN, cC=cC, cS=cS, cI=cI, cR=cR, cDec=cDec, nC=nC, N=N)
