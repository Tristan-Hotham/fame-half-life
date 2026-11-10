"""Step 4: data/results.json (every number quoted anywhere), data/people.csv (person-level measures for the main and
posthumous samples) and data/site.json (page data: curves by group, countries). Asserts check claims made in words."""
import numpy as np, pandas as pd
from common import *

R = {"data": jload(f"{SCR}/r1.json"), "flow": jload(f"{SCR}/flow.json")}
R.update(jload(f"{SCR}/r2.json"))
S = pd.read_csv(f"{SCR}/people.csv")
M = pd.read_csv(f"{SCR}/main.csv")
H = R["H4"]["lr"]; HP = R["H4"]["peak"]
fam = {f: R["groups"]["family"][f] for f in FAMILIES if f in R["groups"]["family"]}
ages = R["groups"]["ageb"]
tp = R["two_phase"]
# prose numbers
pr = {}
pr["hl_fast_days"] = round(tp["hl_fast"] * 30.44)
pr["hl_fast_days_lo"] = round(R["two_phase_ci"]["hl_fast"][0] * 30.44); pr["hl_fast_days_hi"] = round(R["two_phase_ci"]["hl_fast"][1] * 30.44)
pr["hl_slow"] = round(tp["hl_slow"], 1)
pr["half_life_days"] = round(R["fits"]["two-phase"]["half_life"] * 30.44)   # days after month 1 for the month-1 excess to halve
pr["slow_share_k1_pc"] = round(100 * tp["slow_share_k1"])
pr["lr_pc_change"] = round(100 * (R["lr"]["median"] - 1), 1)
pr["lr_pc_lo"] = round(100 * (R["lr"]["lo"] - 1), 1); pr["lr_pc_hi"] = round(100 * (R["lr"]["hi"] - 1), 1)
pr["y1_pc"] = round(100 * (R["y1"]["median"] - 1), 1)
pr["placebo_y1_pc"] = round(100 * (R["placebo"]["y1"]["median"] - 1), 1)
pr["placebo36_pc"] = round(100 * (R["placebo36"]["lr"]["median"] - 1), 1)
pr["vs_drift_pc"] = round(100 * (R["placebo36"]["ratio_real_to_placebo"] - 1), 1)
pr["k0"] = round(R["curve"]["0"]["median"], 1); pr["k1"] = round(R["curve"]["1"]["median"], 2); pr["k2"] = round(R["curve"]["2"]["median"], 2)
pr["k3"] = round(R["curve"]["3"]["median"], 2); pr["k6"] = round(R["curve"]["6"]["median"], 2); pr["k12"] = round(R["curve"]["12"]["median"], 2)
pr["k24"] = round(R["curve"]["24"]["median"], 2); pr["k34"] = round(R["curve"]["34"]["median"], 2)
pr["kpre"] = round(R["curve"]["-2"]["median"], 2)
pr["peak_x"] = round(R["peak"]["median"], 1)
pr["u50_lr"] = round(ages["under 50"]["lr"]["median"], 2); pr["o90_lr"] = round(ages["90 and over"]["lr"]["median"], 2)
pr["u50_peak"] = round(ages["under 50"]["peak"]["median"]); pr["o90_peak"] = round(ages["90 and over"]["peak"]["median"])
pr["perf_lr"] = round(fam["Performers"]["lr"]["median"], 2); pr["rel_lr"] = round(fam["Religion"]["lr"]["median"], 2)
pr["sport_lr"] = round(fam["Sport"]["lr"]["median"], 2); pr["pol_lr"] = round(fam["Politics and law"]["lr"]["median"], 2)
pr["sci_lr"] = round(fam["Science and academia"]["lr"]["median"], 2); pr["wri_lr"] = round(fam["Writers and artists"]["lr"]["median"], 2)
pr["sport_peak"] = round(fam["Sport"]["peak"]["median"], 1); pr["sci_peak"] = round(fam["Science and academia"]["peak"]["median"], 1)
pr["jour_peak"] = round(fam["Journalism and media"]["peak"]["median"], 1); pr["perf_peak"] = round(fam["Performers"]["peak"]["median"], 1)
pr["women_lr"] = round(R["groups"]["sex2"]["women"]["lr"]["median"], 2); pr["men_lr"] = round(R["groups"]["sex2"]["men"]["lr"]["median"], 2)
pr["en_lr"] = round(R["groups"]["lang"]["English-speaking"]["lr"]["median"], 2); pr["oth_lr"] = round(R["groups"]["lang"]["other"]["lr"]["median"], 2)
pr["en_peak"] = round(R["groups"]["lang"]["English-speaking"]["peak"]["median"], 1); pr["oth_peak"] = round(R["groups"]["lang"]["other"]["peak"]["median"], 1)
pr["links_double_lr"] = round(100 * (2 ** H["llinks"]["b"] - 1), 1)
pr["links_double_lr_lo"] = round(100 * (2 ** H["llinks"]["lo"] - 1), 1); pr["links_double_lr_hi"] = round(100 * (2 ** H["llinks"]["hi"] - 1), 1)
pr["links_double_peak"] = round(100 * (2 ** HP["llinks"]["b"] - 1), 1)
pr["base_double_lr"] = round(100 * (2 ** H["lbase"]["b"] - 1), 1)
hls = [v["hl_slow"] for v in fam.values() if v["hl_slow"]]
pr["fam_hl_min"] = round(min(hls), 1); pr["fam_hl_max"] = round(max(hls), 1)
hfs = [v["hl_fast"] for v in fam.values() if v["hl_fast"]]
pr["fam_hf_min_days"] = round(min(hfs) * 30.44); pr["fam_hf_max_days"] = round(max(hfs) * 30.44)
pr["women_pc"] = round(R["main_desc"]["women_pc"]); pr["posthumous_keep_pc"] = round(100 * R["posthumous"]["median_keep_ratio"])
pr["n_fams"] = len(fam)
fam_lr = sorted(((v["lr"]["median"], f) for f, v in fam.items()), reverse=True)
pr["fam_lr_order"] = [f for _, f in fam_lr]
pr["fam_above1"] = [f for v, f in fam_lr if fam[f]["lr"]["lo"] > 1]
R["prose"] = pr
# robustness ranges across checks
rb = R["robust"]
def rng_(key):
    v = [x[key]["b"] for x in rb if x.get(key)]
    return [min(v), max(v)]
def nsig(key):
    return sum(1 for x in rb if x.get(key) and (x[key]["lo"] > 0 or x[key]["hi"] < 0))
R["robust_range"] = {k: rng_(k) for k in ("women", "age_u50", "age_90", "english", "fam_Sport", "fam_Politics and law", "fam_Science and academia", "fam_Religion", "llinks")}
R["robust_nsig"] = {k: nsig(k) for k in R["robust_range"]}
R["robust_n"] = len(rb)
# largest absolute peaks (paper only)
top = M.sort_values("peak_views", ascending=False).head(5)
R["top_peaks"] = [{"title": t, "year": int(y), "views": int(v), "ratio": round(float(p), 1)} for t, y, v, p in zip(top.title, top.dyear, top.peak_views, top.peak)]

# exploratory: anniversary months (12, 24, 36) against the average of the months either side
Cv = pd.read_csv(f"{DATA}/curves.csv"); Ca = Cv[Cv.group == "All"].set_index("k")["median"]
R["anniv"] = {str(k): {"m": round(float(Ca[k]), 3), "nb": round(float((Ca[k - 1] + Ca[k + 1]) / 2), 3), "pc": round(100 * (Ca[k] / ((Ca[k - 1] + Ca[k + 1]) / 2) - 1), 1)} for k in (12, 24, 36)}
assert all(v["pc"] > 0 for v in R["anniv"].values())
R["n_bot"] = int(M.bot_spike.sum())
R["prose"]["bi_boot_pc"] = round(100 * R["two_phase_ci"]["share_bi_best"])
_ct = {r["cit"]: r for r in R["countries"]["rows"]}
R["country_us"] = _ct["Q30"]; R["country_uk"] = _ct["Q145"]
R["n_override"] = len(OVERRIDE)
_pv = jload(f"{RAW}/fame_pageviews.json")
R["n_gappy"] = sum(1 for v in _pv.values() if v and (int(v[-1][0][:4]) * 12 + int(v[-1][0][4:]) - int(v[0][0][:4]) * 12 - int(v[0][0][4:]) + 1) != len(v))
del _pv
_en = jload(f"{RAW}/enwiki_monthly.json")["items"]
R["enwiki_change_pc"] = round(100 * (_en[-1]["views"] / _en[0]["views"] - 1), 1)
# ---- claims made in words
assert R["best_aic"] == "two-phase" and R["best_oos"] == "power law", "text: two-phase best by AIC, power law best out of sample"
assert R["lr"]["hi"] < 1, "text: settles slightly below the baseline"
assert R["placebo"]["y1"]["hi"] < 1 and R["y1"]["lo"] > 1
assert R["placebo36"]["lr"]["hi"] < R["placebo36"]["lr_real_same"]["lo"]
assert H["age_u50"]["lo"] > 0 and H["age_90"]["hi"] < 0 and R["robust_nsig"]["age_u50"] == R["robust_n"] and R["robust_nsig"]["age_90"] == R["robust_n"]
assert H["women"]["hi"] < 0 and R["robust_nsig"]["women"] < R["robust_n"] / 2, "women: borderline, not robust"
assert R["H4_nobase"]["lr"]["women"]["lo"] < 0 < R["H4_nobase"]["lr"]["women"]["hi"]
assert H["english"]["lo"] > 0 and R["H4_nobase"]["lr"]["english"]["lo"] < 0 < R["H4_nobase"]["lr"]["english"]["hi"]
assert all(H["fam_" + f]["hi"] < 0 for f in FAMILIES[1:]), "every family below performers"
assert R["H4"]["lr"]["wald_family_p"] < 1e-6
assert fam_lr[0][1] == "Performers" and fam_lr[-1][1] == "Religion"
assert R["placebo_reg"]["y1"]["fam_Sport"]["hi"] < 0, "placebo shows a sport drift (text says so)"
assert R["placebo_reg"]["y1"]["age_u50"]["lo"] < 0 < R["placebo_reg"]["y1"]["age_u50"]["hi"]
assert R["did_y1"]["age_u50"]["lo"] > 0 and R["did_y1"]["age_90"]["hi"] < 0
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)

# ---- person-level table (main + posthumous): no raw series, measures only
keepc = ["qid", "title", "dod", "dyear", "sex_label", "age", "occ_label", "family", "cit_label", "english", "links", "main", "posthumous", "first_k",
         "base_views", "base", "peak", "peak_k", "peak_views", "y1", "lr", "excess1", "pl_ok", "pl_peak", "pl_y1", "bot_spike", "dod_jan1"]
O = S[(S.main == 1) | ((S.posthumous == 1) & (S.dod_jan1 == 0))][keepc].copy()
O = O.rename(columns={"sex_label": "sex", "occ_label": "occupation", "cit_label": "citizenship", "base": "base_share_per_million"})
for c in ("base_share_per_million",):
    O[c] = O[c].round(5)
for c in ("base_views", "peak", "y1", "lr", "excess1", "pl_peak", "pl_y1", "age"):
    O[c] = O[c].round(3)
O.to_csv(f"{DATA}/people.csv", index=False)

# ---- page data
C = pd.read_csv(f"{DATA}/curves.csv")
site = {"curves": {}, "n_main": R["n_main"]}
for g, d in C.groupby("group"):
    d = d[(d.k >= -12) & (d.k <= 60)]
    site["curves"][g] = {"k": d.k.tolist(), "m": d["median"].round(4).tolist(), "lo": d.lo.round(4).tolist(), "hi": d.hi.round(4).tolist(), "n": d.n.astype(int).tolist()}
gs = {}
for g, d in R["groups"].items():
    for lv, v in d.items():
        gs[f"{g}:{lv}"] = {"n": v["n"], "peak": round(v["peak"]["median"], 1), "y1": round(v["y1"]["median"], 3), "lr": round(v["lr"]["median"], 3),
                           "lr_lo": round(v["lr"]["lo"], 3), "lr_hi": round(v["lr"]["hi"], 3), "hl": round(v["hl_slow"], 1) if v["hl_slow"] else None,
                           "hf": round(v["hl_fast"] * 30.44) if v["hl_fast"] else None,
                           "above": v["lr_above1_pc"]}
site["groups"] = gs
site["all"] = {"peak": R["peak"]["median"], "lr": R["lr"]["median"], "lr_lo": R["lr"]["lo"], "lr_hi": R["lr"]["hi"], "y1": R["y1"]["median"], "n": R["n_main"],
               "above": R["lr_above1_pc"], "hl": pr["hl_slow"], "hf": pr["hl_fast_days"]}
kk = np.arange(1, 61)
site["fits"] = {nm: {"k": kk.tolist(), "y": None} for nm in R["fits"]}
from importlib import import_module
f_exp = lambda k, c, a, tau: c + a * np.exp(-k / tau)
f_pow = lambda k, c, a, b: c + a * k ** (-b)
f_bi = lambda k, c, a, t1, b, t2: c + a * np.exp(-k / t1) + b * np.exp(-k / t2)
for nm, f in (("exponential", f_exp), ("power law", f_pow), ("two-phase", f_bi)):
    site["fits"][nm]["y"] = [round(float(x), 4) for x in f(kk, *R["fits"][nm]["par"])]
CT = pd.read_csv(f"{DATA}/countries.csv")
site["countries"] = CT[["cit", "name", "n", "lr", "lr_lo", "lr_hi", "peak", "y1", "lr_above1_pc", "women_pc", "top_family"]].to_dict("records")
jsave(site, f"{DATA}/site.json")
print("results.json ok;", len(O), "people rows; prose", {k: pr[k] for k in ("half_life_days", "hl_fast_days", "hl_slow", "lr_pc_change", "vs_drift_pc", "u50_lr", "o90_lr")})
print("robust", R["robust_range"], R["robust_nsig"], R["robust_n"])
