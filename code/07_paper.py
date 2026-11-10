"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds the tables, compiles with xelatex.
Output: release/paper/Hotham_Half_Life_of_Fame.pdf and .tex beside the f_*.pdf figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24095452 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Half_Life_of_Fame"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "abs": return f"{abs(float(v)):.0f}"
    for k in ("f0", "f1", "f2", "f3", "f4"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


pc = lambda v: (f"{v['b']:.0f} [{v['lo']:.0f}, {v['hi']:.0f}]".replace("-", "$-$")) if v else ""
fl = R["flow"]; d = R["data"]
# claims in the text that depend on which check is the extreme
mr = next(x for x in R["robust"] if x["label"].startswith("Median regression"))
assert abs(mr["english"]["b"] - R["robust_range"]["english"][0]) < 1e-9 and abs(mr["fam_Sport"]["b"] - R["robust_range"]["fam_Sport"][1]) < 1e-9
assert R["H4"]["lr"]["wald_family_p"] < 1e-10 and R["H4"]["peak"]["wald_family_p"] < 1e-10
assert R["did_y1"]["fam_Sport"]["hi"] < 0 and R["did_y1"]["fam_Politics and law"]["hi"] < 0 and R["did_y1"]["fam_Religion"]["hi"] < 0 and R["did_y1"]["fam_Military"]["hi"] < 0
assert R["placebo_reg"]["y1"]["fam_Science and academia"]["hi"] < 0 and R["placebo_reg"]["y1"]["english"]["lo"] > 0

assert max(abs(R["rep"]["full"]["family_pc"][f] - R["rep"]["sample"]["family_pc"][f]) for f in FAMILIES) <= 0.5
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{From the Wikidata population to the analysis sample.}\\label{tab:flow}\\begin{tabular}{lr}\\toprule Step & People\\\\\\midrule\n"
      f"English Wikipedia articles, died 2016 to 2023 (Wikidata) & {d['n_people']:,}\\\\\n"
      f"30\\% hash sample & {fl['sample']:,}\\\\\n"
      f"\\quad with monthly pageviews (fetched, article found) & {fl['with_views']:,}\\\\\n"
      f"\\quad less: date of death on 1 January (possible year precision) & $-${fl['jan1']:,}\\\\\n"
      f"\\quad less: died before February 2016 (under six baseline months) & $-${fl['too_early']:,}\\\\\n"
      f"\\quad less: article not yet read at the start of the baseline & $-${fl['not_preexisting']:,}\\\\\n"
      f"\\qquad of which first read in or after the month of death & {fl['posthumous']:,}\\\\\n"
      f"\\quad less: no views in the baseline months & $-${fl['zero_base']:,}\\\\\\midrule\n"
      f"Main sample & {fl['main']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = ""
G = R["groups"]
for f in R["prose"]["fam_lr_order"]:
    v = G["family"][f]
    rows += (f"{tex(f)} & {v['n']:,} & {v['peak']['median']:.1f} & {v['y1']['median']:.2f} & {v['lr']['median']:.2f} [{v['lr']['lo']:.2f}, {v['lr']['hi']:.2f}] & {v['lr_above1_pc']:.0f} & "
             f"{v['hl_fast'] * 30.44:.0f} & {v['hl_slow']:.1f}\\\\\n")
rows += f"\\midrule All & {R['n_main']:,} & {R['peak']['median']:.1f} & {R['y1']['median']:.2f} & {R['lr']['median']:.2f} [{R['lr']['lo']:.2f}, {R['lr']['hi']:.2f}] & {R['lr_above1_pc']:.0f} & {R['prose']['hl_fast_days']} & {R['prose']['hl_slow']:.1f}\\\\\n"
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{Medians by occupation family: peak, one-year ratio and long-run ratio (LR, with 95\\% bootstrap interval), share of people with LR above 1, and the half-lives of the fast (days) and slow (months) components of a two-phase model fitted to each family's median curve (point estimates).}\\label{tab:desc}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{lrrrlrrr}\\toprule Family & $N$ & Peak & Year 1 & LR & LR$>$1 (\\%) & Fast (d) & Slow (mo)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
F = R["fits"]
rows = "".join(f"{nm} & {len(F[nm]['par'])} & {F[nm]['aic']:.1f} & {F[nm]['bic']:.1f} & {F[nm]['aic34']:.1f} & {F[nm]['aic_geo']:.1f} & {F[nm]['rmse_log']:.4f} & {F[nm]['oos_rmse']:.4f}\\\\\n".replace("-", "$-$")
               for nm in ("exponential", "power law", "two-phase"))
TFIT = ("\\begin{table}[tbp]\\centering\\small\\caption{Decay models fitted to the median curve ($k = 1$ to 60 unless stated). AIC and BIC on log residuals; out-of-sample: fitted to deaths in 2016 to 2019, predicting 2020 to 2023 ($k = 1$ to 34), log RMSE.}\\label{tab:fits}"
        "\\begin{tabular}{lrrrrrrr}\\toprule Model & Par. & AIC & BIC & AIC ($k\\le34$) & AIC (geo. mean) & RMSE & Out-of-sample\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
LAB = [("Writers and artists", "fam_Writers and artists"), ("Sport", "fam_Sport"), ("Politics and law", "fam_Politics and law"), ("Science and academia", "fam_Science and academia"),
       ("Business", "fam_Business"), ("Military", "fam_Military"), ("Religion", "fam_Religion"), ("Journalism and media", "fam_Journalism and media"), ("Other occupation", "fam_Other"),
       ("Woman", "women"), ("Died under 50", "age_u50"), ("Died 50 to 64", "age_50"), ("Died 80 to 89", "age_80"), ("Died 90 or over", "age_90"),
       ("English-speaking citizenship", "english"), ("log sitelinks", "llinks"), ("log baseline share", "lbase")]
cols = [R["H4"]["lr"], R["H4"]["peak"], R["H4"]["y1"], R["H4_nobase"]["lr"]]
def cell(v):
    if not v: return "", ""
    st = "^{***}" if v["p"] < .001 else "^{**}" if v["p"] < .01 else "^{*}" if v["p"] < .05 else ""
    return f"${v['coef']:.3f}{st}$", f"({v['se']:.3f})"
body = ""
for lab, k in LAB:
    cs = [cell(c.get(k)) for c in cols]
    body += tex(lab) + " & " + " & ".join(a for a, _ in cs) + "\\\\\n & " + " & ".join(b for _, b in cs) + "\\\\\n"
body += "\\midrule Year and month-of-death FE & yes & yes & yes & yes\\\\\n"
body += "$R^2$ & " + " & ".join(f"{c['r2']:.3f}" if c.get('r2') else "" for c in cols) + "\\\\\n"
body += "$N$ & " + " & ".join(f"{c['n']:,}" for c in cols) + "\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Main regressions (OLS on log outcomes). Columns: log LR (main), log peak, log one-year ratio, and log LR without the baseline control (exploratory). Coefficients on the log scale; standard errors clustered by month of death in parentheses. Reference: performers, men, died aged 65 to 79, non-English-speaking citizenship; unknown age and citizenship have their own indicators. $^{*}p<.05$, $^{**}p<.01$, $^{***}p<.001$.}\\label{tab:main}"
      "\\begin{tabular}{lcccc}\\toprule & Log LR & Log peak & Log year 1 & Log LR, no baseline\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")
KEYS = [("women", "Women"), ("age_u50", "Under 50"), ("age_90", "90+"), ("english", "English-sp."), ("fam_Sport", "Sport"), ("fam_Politics and law", "Politics"), ("fam_Science and academia", "Science")]
rows = ""; grp = None
for x in R["robust"]:
    if x["group"] != grp:
        rows += f"\\multicolumn{{9}}{{l}}{{\\textit{{{tex(x['group'])}}}}}\\\\\n"; grp = x["group"]
    rows += f"\\quad {tex(x['label'])} & {x['n']:,} & " + " & ".join(pc(x.get(k)) for k, _ in KEYS) + "\\\\\n"
H = R["H4"]["lr"]
rows += "\\midrule Main model & " + f"{H['n']:,} & " + " & ".join(pc(H.get(k)) for k, _ in KEYS) + "\\\\\n"
TB = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness checks for log LR. Percentage differences with 95\\% intervals for women (vs men), death under 50 and at 90 or over (vs 65 to 79), English-speaking citizenship, and sport, politics and law, and science and academia (vs performers).}\\label{tab:robust}"
      "\\setlength{\\tabcolsep}{1.8pt}\\resizebox{\\textwidth}{!}{\\begin{tabular}{p{4.4cm}rlllllll}\\toprule Check & $N$ & " + " & ".join(n for _, n in KEYS) + "\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
PR = R["placebo_reg"]
prow = lambda lab, x: f"{lab} & {x['n']:,} & " + " & ".join(pc(x.get(k)) for k, _ in KEYS) + "\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Placebo regressions (same model, same people): placebo peak and one-year ratio at a fake date 24 months before death; the real one-year ratio for the same people; and (exploratory) the person-level difference between real and placebo log one-year ratios. Percentage differences with 95\\% intervals.}\\label{tab:placebo}"
      "\\setlength{\\tabcolsep}{1.8pt}\\resizebox{\\textwidth}{!}{\\begin{tabular}{p{4.0cm}rlllllll}\\toprule Outcome & $N$ & " + " & ".join(n for _, n in KEYS) + "\\\\\\midrule\n"
      + prow("Placebo peak", PR["peak"]) + prow("Placebo one-year ratio", PR["y1"]) + prow("Real one-year ratio", PR["y1_real"]) + prow("Real minus placebo (exploratory)", R["did_y1"]) + "\\bottomrule\\end{tabular}}\\end{table}")
rows = "".join(f"{tex(x['left_out'])} & {x['n']:,} & {pc(x['women'])} & {pc(x['age_u50'])} & {pc(x['age_90'])} & {pc(x['english'])}\\\\\n" for x in R["lofo"])
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{Leave one occupation family out: log LR model re-estimated without each family (percentage differences, 95\\% intervals).}\\label{tab:lofo}"
      "\\begin{tabular}{lrllll}\\toprule Family left out & $N$ & Women & Under 50 & 90+ & English-speaking\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rep = R["rep"]
rows = f"Women (\\%) & {rep['full']['women_pc']:.1f} & {rep['sample']['women_pc']:.1f} & {rep['main']['women_pc']:.1f}\\\\\n"
rows += f"Median sitelinks & {rep['full']['links_median']:.0f} & {rep['sample']['links_median']:.0f} & {rep['main']['links_median']:.0f}\\\\\n"
rows += f"English-speaking citizenship (\\%) & {rep['full']['english_pc']:.1f} & {rep['sample']['english_pc']:.1f} & {rep['main']['english_pc']:.1f}\\\\\n"
rows += f"Median age at death & {rep['full']['age_median']:.1f} & {rep['sample']['age_median']:.1f} & {rep['main']['age_median']:.1f}\\\\\n"
for f in FAMILIES:
    rows += f"{tex(f)} (\\%) & {rep['full']['family_pc'][f]:.1f} & {rep['sample']['family_pc'][f]:.1f} & {rep['main']['family_pc'][f]:.1f}\\\\\n"
rows += f"$N$ & {rep['n_full']:,} & {rep['n_sample']:,} & {R['n_main']:,}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Representativeness: the full Wikidata population, the 30\\% hash sample and the main analysis sample.}\\label{tab:rep}"
      "\\begin{tabular}{lrrr}\\toprule & Population & Hash sample & Main sample\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_FLOW", TF), ("TABLE_DESC", TD), ("TABLE_FITS", TFIT), ("TABLE_MAIN", TM), ("TABLE_ROBUST", TB), ("TABLE_PLACEBO", TP), ("TABLE_LOFO", TL), ("TABLE_REP", TR)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24095452", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1)
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
cites = set(re.findall(r"\\cite\w*\{([^}]+)\}", t)); cites = {c.strip() for x in cites for c in x.split(",")}
bibs = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
print("uncited:", bibs - cites, "missing:", cites - bibs, "refs:", len(bibs))
print("unreferenced labels:", [l for l in re.findall(r"\\label\{([^}]+)\}", t) if "\\ref{" + l + "}" not in t])
