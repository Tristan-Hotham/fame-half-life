"""Step 3: the planned analysis. Aggregate decay curves with bootstrap intervals, decay model comparison, half-lives,
settling point, regressions with robustness checks, placebo, posthumous articles, representativeness, countries.
Writes SCR/r2.json, data/curves.csv, data/models.csv, data/countries.csv."""
import warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy.optimize import curve_fit
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20261)
S = pd.read_csv(f"{SCR}/people.csv")
Z = np.load(f"{SCR}/event.npz", allow_pickle=True)
X, XR, K = Z["X"].astype(float), Z["XR"].astype(float), Z["K"]
assert (Z["qid"] == S.qid.values).all()
col = {int(k): j for j, k in enumerate(K)}
main = S.main.values == 1
M = S[main].reset_index(drop=True)
R = X[main] / M.base.values[:, None]              # ratio to own baseline, by event time
R2 = {}
NB = 500

# ---------------- aggregate curves
def curve(Rm, stat="median"):
    if stat == "median":
        return np.nanmedian(Rm, axis=0)
    return np.exp(np.nanmean(np.log(np.maximum(Rm, FLOOR)), axis=0))


def boot_curve(Rm, stat="median", nb=NB):
    n = len(Rm); out = np.empty((nb, Rm.shape[1]))
    for b in range(nb):
        out[b] = curve(Rm[rng.integers(0, n, n)], stat)
    return np.percentile(out, [2.5, 97.5], axis=0)


kk = np.arange(-24, 61)
J = [col[k] for k in kk]
med = curve(R[:, J]); lo, hi = boot_curve(R[:, J])
geo = curve(R[:, J], "geo"); glo, ghi = boot_curve(R[:, J], "geo", 200)
nobs = np.sum(~np.isnan(R[:, J]), axis=0)
CA = pd.DataFrame({"group": "All", "k": kk, "median": med, "lo": lo, "hi": hi, "geo": geo, "geo_lo": glo, "geo_hi": ghi, "n": nobs})
# ratio of sums (aggregate attention of the group; dominated by the most famous)
agg = np.nansum(X[main][:, J], axis=0) / np.nansum(M.base.values)
CA["ratio_of_sums"] = agg
curves = [CA]
R2["curve"] = {str(k): {"median": round(float(m), 4), "lo": round(float(a), 4), "hi": round(float(b), 4), "n": int(c)} for k, m, a, b, c in zip(kk, med, lo, hi, nobs) if k in (-12, -6, -2, -1, 0, 1, 2, 3, 6, 12, 24, 34, 36, 48, 60)}
R2["ratio_of_sums"] = {str(k): round(float(a), 3) for k, a in zip(kk, agg) if k in (0, 1, 12, 24, 34)}

# ---------------- decay models (fit on log of the median curve, k = 1..60)
def f_exp(k, c, a, tau): return c + a * np.exp(-k / tau)
def f_pow(k, c, a, b): return c + a * k ** (-b)
def f_bi(k, c, a, t1, b, t2): return c + a * np.exp(-k / t1) + b * np.exp(-k / t2)
MODELS = {"exponential": (f_exp, [1, 20, 1], ([0, 0, 0.05], [10, 1e4, 200])),
          "power law": (f_pow, [1, 20, 1], ([0, 0, 0.01], [10, 1e4, 10])),
          "two-phase": (f_bi, [1, 20, 0.7, 1, 8], ([0, 0, 0.05, 0, 0.5], [10, 1e4, 30, 1e3, 300]))}


def fit(k, y, name, p0=None):
    f, p, bd = MODELS[name]
    g = lambda kx, *a: np.log(np.maximum(f(kx, *a), 1e-9))
    best = None
    starts = [p0 or p] + ([[1, 20, 0.5, 2, 15], [1, 40, 0.4, 3, 30], [0.9, 10, 1.0, 0.5, 6]] if name == "two-phase" else [[1, 5, 3], [1, 50, 0.5]])
    for s in starts:
        try:
            par, _ = curve_fit(g, k, np.log(y), p0=s, bounds=bd, maxfev=40000)
        except Exception:
            continue
        rss = float(np.sum((np.log(y) - g(k, *par)) ** 2))
        if best is None or rss < best[1]:
            best = (par, rss)
    par, rss = best
    n, q = len(k), len(par)
    return {"par": [float(x) for x in par], "rss": rss, "aic": n * np.log(rss / n) + 2 * q, "bic": n * np.log(rss / n) + q * np.log(n), "n": n, "p": q}


def half_life(name, par):
    f = MODELS[name][0]; c = par[0]
    g = np.linspace(1, 400, 400001)
    e = f(g, *par) - c; e1 = f(np.array([1.0]), *par)[0] - c
    i = np.argmax(e <= e1 / 2)
    return float(g[i]) - 1 if e[i] <= e1 / 2 else None   # months after k = 1 for the k = 1 excess to halve


kf = np.arange(1, 61); yf = med[[list(kk).index(k) for k in kf]]
fits = {nm: fit(kf, yf, nm) for nm in MODELS}
kf34 = np.arange(1, 35); yf34 = yf[:34]
fits34 = {nm: fit(kf34, yf34, nm) for nm in MODELS}
gf = geo[[list(kk).index(k) for k in kf]]
fitsg = {nm: fit(kf, gf, nm) for nm in MODELS}
# out of sample: fit on deaths 2016 to 2019, predict deaths 2020 to 2023 (k = 1..34)
early = M.dyear.values <= 2019
ye = np.nanmedian(R[early][:, [col[k] for k in kf34]], axis=0)
yl = np.nanmedian(R[~early][:, [col[k] for k in kf34]], axis=0)
oos = {}
for nm in MODELS:
    ft = fit(kf34, ye, nm)
    pred = MODELS[nm][0](kf34, *ft["par"])
    oos[nm] = float(np.sqrt(np.mean((np.log(yl) - np.log(pred)) ** 2)))
R2["fits"] = {nm: {"aic": round(v["aic"], 1), "bic": round(v["bic"], 1), "rmse_log": round(float(np.sqrt(v["rss"] / v["n"])), 4), "par": [round(x, 4) for x in v["par"]],
                   "half_life": half_life(nm, v["par"]), "aic34": round(fits34[nm]["aic"], 1), "aic_geo": round(fitsg[nm]["aic"], 1),
                   "oos_rmse": round(oos[nm], 4), "c": round(v["par"][0], 3)} for nm, v in fits.items()}
best_aic = min(fits, key=lambda nm: fits[nm]["aic"])
best_oos = min(oos, key=oos.get)
R2["best_aic"] = best_aic; R2["best_oos"] = best_oos
R2["best_aic34"] = min(fits34, key=lambda nm: fits34[nm]["aic"]); R2["best_aic_geo"] = min(fitsg, key=lambda nm: fitsg[nm]["aic"])
bi = fits["two-phase"]["par"]
R2["two_phase"] = {"c": bi[0], "a": bi[1], "t1": bi[2], "b": bi[3], "t2": bi[4],
                   "hl_fast": bi[2] * np.log(2), "hl_slow": bi[4] * np.log(2),
                   "slow_share_k1": bi[3] * np.exp(-1 / bi[4]) / (bi[1] * np.exp(-1 / bi[2]) + bi[3] * np.exp(-1 / bi[4]))}
# empirical half-life of the median excess (relative to the fitted asymptote of the preferred model)
cpref = fits[best_aic]["par"][0]
e1 = yf[0] - cpref
R2["emp_half_k"] = int(kf[np.argmax(yf - cpref <= e1 / 2)])
R2["emp_tenth_k"] = int(kf[np.argmax(yf - cpref <= e1 / 10)])

# bootstrap the two-phase parameters and half-lives (people resampled)
bt = []
for b in range(200):
    ii = rng.integers(0, len(R), len(R))
    yb = np.nanmedian(R[ii][:, [col[k] for k in kf]], axis=0)
    try:
        ft = fit(kf, yb, "two-phase", p0=bi)
        p = ft["par"]
        bt.append([p[0], p[2] * np.log(2), p[4] * np.log(2), half_life("two-phase", p), ft["aic"], fit(kf, yb, "exponential")["aic"], fit(kf, yb, "power law")["aic"]])
    except Exception:
        pass
bt = np.array(bt, dtype=float)
ci = lambda v: [round(float(np.nanpercentile(v, 2.5)), 3), round(float(np.nanpercentile(v, 97.5)), 3)]
R2["two_phase_ci"] = {"c": ci(bt[:, 0]), "hl_fast": ci(bt[:, 1]), "hl_slow": ci(bt[:, 2]), "half_life": ci(bt[:, 3]), "n_boot": len(bt),
                      "share_bi_best": round(float(np.mean((bt[:, 4] < bt[:, 5]) & (bt[:, 4] < bt[:, 6]))), 3)}

# ---------------- settling point (H3) and person-level summaries
def med_ci(v, nb=NB):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    bs = [np.median(v[rng.integers(0, len(v), len(v))]) for _ in range(nb)]
    return {"median": round(float(np.median(v)), 4), "lo": round(float(np.percentile(bs, 2.5)), 4), "hi": round(float(np.percentile(bs, 97.5)), 4), "n": int(len(v))}


R2["peak"] = med_ci(M.peak); R2["y1"] = med_ci(M.y1); R2["lr"] = med_ci(M.lr); R2["excess1"] = med_ci(M.excess1)
R2["lr_above1_pc"] = round(100 * float((M.lr > 1).mean()), 1)
R2["lr_above2_pc"] = round(100 * float((M.lr > 2).mean()), 1)
R2["lr_below_half_pc"] = round(100 * float((M.lr < 0.5).mean()), 1)
R2["y1_above1_pc"] = round(100 * float((M.y1 > 1).mean()), 1)
R2["peak_k1_pc"] = round(100 * float(M.peak_k.mean()), 1)
R2["peak_above10_pc"] = round(100 * float((M.peak > 10).mean()), 1)
R2["peak_quart"] = [round(float(x), 2) for x in np.percentile(M.peak, [25, 50, 75, 90, 99])]
R2["lr_quart"] = [round(float(x), 3) for x in np.percentile(M.lr, [10, 25, 50, 75, 90])]
R2["lr_views"] = med_ci(M.lr_views)
R2["peak_views_med"] = round(float(M.peak_views.median()))
R2["base_views_med"] = round(float(M.base_views.median()), 1)
R2["lr_views_abs_med"] = round(float(M.lr_views_abs.median()), 1)
# placebo (fake death 24 months earlier)
PL = M[M.pl_ok == 1]
R2["placebo"] = {"peak": med_ci(PL.pl_peak), "y1": med_ci(PL.pl_y1), "y1_real_same": med_ci(PL.y1), "lr_real_same": med_ci(PL.lr)}
# exploratory: fake death 36 months earlier (no-death drift over 24 to 34 months)
P36 = M[M.pl36_ok == 1]
R2["placebo36"] = {"lr": med_ci(P36.pl36_lr), "lr_real_same": med_ci(P36.lr),
                   "ratio_real_to_placebo": round(float(np.median(P36.lr) / np.median(P36.pl36_lr)), 3)}
# k = -1 (the month before death)
R2["k_m1"] = R2["curve"]["-1"]

# ---------------- groups: curves and medians
def agebin(a):
    if a != a: return "unknown"
    return "under 50" if a < 50 else "50 to 64" if a < 65 else "65 to 79" if a < 80 else "80 to 89" if a < 90 else "90 and over"


for D in (S, M):
    D["sex2"] = D.sex.map({"Q6581097": "men", "Q6581072": "women"}).fillna("other or unknown")
    D["ageb"] = D.age.map(agebin)
    D["lang"] = np.where(D.cit.isna(), "unknown", np.where(D.cit.isin(list(ENGLISH)), "English-speaking", "other"))
    D["llinks"] = np.log(D.links)
    D["dm"] = D.dyear * 12 + D.dmonth
M["lbase"] = np.log(M.base)
for v in ("peak", "y1", "lr", "lr_views", "lr_alt", "lr_b6", "peak_b6", "peak_views_ratio"):
    M["l" + v] = np.log(np.maximum(M[v], FLOOR))
M["lexcess1"] = np.log(np.maximum(M.excess1 + 12, FLOOR) / 12)   # log of mean first-year ratio
groups = {"family": FAMILIES, "sex2": ["men", "women"], "ageb": ["under 50", "50 to 64", "65 to 79", "80 to 89", "90 and over"], "lang": ["English-speaking", "other"]}
G = {}
for g, levels in groups.items():
    G[g] = {}
    for lv in levels:
        w = (M[g] == lv).values
        if w.sum() < 30: continue
        Rm = R[w][:, J]
        c = curve(Rm); bl, bh = boot_curve(Rm, nb=200)
        curves.append(pd.DataFrame({"group": f"{g}:{lv}", "k": kk, "median": c, "lo": bl, "hi": bh, "n": np.sum(~np.isnan(Rm), axis=0)}))
        try:
            ft = fit(kf, c[[list(kk).index(k) for k in kf]], "two-phase", p0=bi)
            hl = half_life("two-phase", ft["par"]); cc = ft["par"][0]
            hf, hs = ft["par"][2] * np.log(2), ft["par"][4] * np.log(2)
        except Exception:
            hl, cc, hf, hs = None, None, None, None
        G[g][lv] = {"n": int(w.sum()), "peak": med_ci(M.peak[w], 300), "y1": med_ci(M.y1[w], 300), "lr": med_ci(M.lr[w], 300),
                    "lr_above1_pc": round(100 * float((M.lr[w] > 1).mean()), 1), "half_life": hl, "c": cc, "hl_fast": hf, "hl_slow": hs,
                    "k1": round(float(c[list(kk).index(1)]), 3), "k3": round(float(c[list(kk).index(3)]), 3), "k12": round(float(c[list(kk).index(12)]), 3)}
R2["groups"] = G
CC = pd.concat(curves)
CC.round(4).to_csv(f"{DATA}/curves.csv", index=False)

# ---------------- regressions (H4)
FORM = ("{y} ~ C(family, Treatment('Performers')) + C(sex2, Treatment('men')) + C(ageb, Treatment('65 to 79')) + "
        "C(lang, Treatment('other')) + llinks + lbase + C(dyear) + C(dmonth)")
KEYS = {"women": "C(sex2, Treatment('men'))[T.women]", "age_u50": "C(ageb, Treatment('65 to 79'))[T.under 50]",
        "age_50": "C(ageb, Treatment('65 to 79'))[T.50 to 64]", "age_80": "C(ageb, Treatment('65 to 79'))[T.80 to 89]",
        "age_90": "C(ageb, Treatment('65 to 79'))[T.90 and over]", "english": "C(lang, Treatment('other'))[T.English-speaking]",
        "llinks": "llinks", "lbase": "lbase"}
for f in FAMILIES[1:]:
    KEYS["fam_" + f] = f"C(family, Treatment('Performers'))[T.{f}]"
rows = []


def est(res, key, pct=True):
    t = KEYS.get(key, key)
    if t not in res.params.index: return None
    b, se = float(res.params[t]), float(res.bse[t])
    lo_, hi_ = b - 1.96 * se, b + 1.96 * se
    if pct and key not in ("llinks", "lbase"):
        return {"b": round(100 * (np.exp(b) - 1), 1), "lo": round(100 * (np.exp(lo_) - 1), 1), "hi": round(100 * (np.exp(hi_) - 1), 1), "p": round(float(res.pvalues[t]), 4), "coef": round(b, 4), "se": round(se, 4)}
    return {"b": round(b, 3), "lo": round(lo_, 3), "hi": round(hi_, 3), "p": round(float(res.pvalues[t]), 4), "coef": round(b, 4), "se": round(se, 4)}


def run(D, y="llr", label="", group="", form=FORM, cov="cluster", q=None, save=True):
    f = form.format(y=y)
    D = D.dropna(subset=[y])
    if "Performers" not in set(D.family):
        f = f.replace("Treatment('Performers')", "Treatment('Writers and artists')")
    if q is not None:
        res = smf.quantreg(f, D).fit(q=q, max_iter=5000)
    elif cov == "cluster":
        res = smf.ols(f, D).fit(cov_type="cluster", cov_kwds={"groups": D.dm.values})
    else:
        res = smf.ols(f, D).fit(cov_type="HC1")
    out = {"label": label, "group": group, "n": int(res.nobs), "y": y}
    for k in KEYS:
        out[k] = est(res, k)
    if save:
        for t in res.params.index:
            rows.append({"model": label, "term": t, "b": res.params[t], "se": res.bse[t], "p": res.pvalues[t], "n": int(res.nobs),
                         "r2": getattr(res, "rsquared", np.nan), "y": y})
    return out, res


H4 = {}
for y, nm in (("llr", "lr"), ("lpeak", "peak"), ("ly1", "y1")):
    H4[nm], res = run(M, y, f"Main: log {nm}")
    H4[nm]["r2"] = round(float(res.rsquared), 3)
    terms = [KEYS["fam_" + f] for f in FAMILIES[1:]]
    w = res.wald_test(", ".join(f"{t} = 0" for t in [f"C(family, Treatment('Performers'))[T.{f}]" for f in FAMILIES[1:]]), scalar=True)
    H4[nm]["wald_family_F"] = round(float(w.statistic), 2); H4[nm]["wald_family_p"] = float(w.pvalue)
R2["H4"] = H4
# without log baseline (exploratory: the baseline enters both sides of the ratio)
FORM_NB = FORM.replace(" + lbase", "")
R2["H4_nobase"] = {nm: run(M, y, f"No baseline control: log {nm}", form=FORM_NB)[0] for y, nm in (("llr", "lr"), ("lpeak", "peak"))}

# ---------------- robustness for log LR (and log peak)
RB = []
def rb(D, label, group, y="llr", **kw):
    o, _ = run(D, y, label, group, **kw)
    o["median_lr"] = round(float(np.nanmedian(np.exp(D[y]))), 3) if y.startswith("llr") or y.startswith("llr_") else None
    RB.append(o)


rb(M, "Median regression (q = 0.5)", "Alternative specification", q=0.5)
Mw = M.copy(); lo_, hi_ = M.llr.quantile([0.01, 0.99]); Mw["llr"] = M.llr.clip(lo_, hi_)
rb(Mw, "OLS, log LR winsorised 1/99", "Alternative specification")
rb(M, "Robust (HC1) standard errors", "Alternative specification", cov="hc1")
rb(M[M.peak < M.peak.quantile(0.99)], "Drop top 1% by peak", "Outliers")
rb(M[M.base < M.base.quantile(0.99)], "Drop top 1% by baseline attention", "Outliers")
rb(M[M.cit != "Q30"], "Leave out US citizens", "Leave one out")
for yv in range(2016, 2024):
    rb(M[M.dyear != yv], f"Leave out deaths in {yv}", "Leave one out")
rb(M.assign(llr=M.llr_views), "Raw views, not share of enwiki", "Measurement", y="llr")
rb(M.assign(llr=M.llr_b6), "Baseline months -6 to -2", "Measurement")
rb(M.assign(llr=M.llr_alt), "Long-run window months 18 to 30", "Measurement")
rb(M[M.base_strict == 1], "Full 11-month baseline only", "Measurement")
rb(M[M.bot_spike == 0], "Drop series with bot-like baseline spikes", "Measurement")
Mf = M.copy(); Mf["family"] = M.family_first
rb(Mf, "Occupation: first in file order", "Measurement")
# including 1 January dates of death
J1 = S[S.main_jan1 == 1].copy()
J1["base"] = J1.base; J1["lbase"] = np.log(J1.base); J1["llr"] = np.log(np.maximum(J1.lr, FLOOR))
rb(J1, "Include 1 January dates of death", "Measurement")
R2["robust"] = RB
# placebo regressions: the same model on the placebo one-year ratio and peak
PLm = M[M.pl_ok == 1].copy()
PLm["lpl_y1"] = np.log(np.maximum(PLm.pl_y1, FLOOR)); PLm["lpl_peak"] = np.log(np.maximum(PLm.pl_peak, FLOOR)); PLm["lbase"] = np.log(PLm.pl_base)
R2["placebo_reg"] = {"y1": run(PLm, "lpl_y1", "Placebo: log one-year ratio at fake death")[0],
                     "peak": run(PLm, "lpl_peak", "Placebo: log peak at fake death")[0],
                     "y1_real": run(PLm, "ly1", "Real one-year ratio, placebo sample")[0]}
# exploratory: the real one-year ratio relative to the person's own placebo one-year ratio (own pre-existing drift)
PLm["ldid_y1"] = PLm.ly1 - PLm.lpl_y1
R2["did_y1"] = run(PLm, "ldid_y1", "Exploratory: log one-year ratio minus log placebo one-year ratio")[0]
P36m = M[M.pl36_ok == 1].copy(); P36m["ldid_lr"] = P36m.llr - np.log(np.maximum(P36m.pl36_lr, FLOOR))
R2["did_lr"] = run(P36m, "ldid_lr", "Exploratory: log LR minus log no-death drift (fake death 36 months earlier)")[0]
R2["placebo36_reg"] = run(P36m.assign(lpl36=np.log(np.maximum(P36m.pl36_lr, FLOOR))), "lpl36", "Placebo: log two-to-three-year drift before death")[0]
# leave one family out for sex and age estimates
R2["lofo"] = []
for f in FAMILIES:
    o, _ = run(M[M.family != f], "llr", f"Leave out {f}", save=False)
    R2["lofo"].append({"left_out": f, "n": o["n"], "women": o["women"], "age_u50": o["age_u50"], "age_90": o["age_90"], "english": o["english"]})
pd.DataFrame(rows).to_csv(f"{DATA}/models.csv", index=False)

# ---------------- posthumous articles (descriptive)
O = S[(S.fetched == 1) & (S.not_found == 0) & (S.dod_jan1 == 0) & (S.base_avail >= MIN_BASE)].copy()
PO = O[(O.posthumous == 1) & (O.first_k <= 1)].copy()
xi = np.where(S.qid.isin(PO.qid))[0]
pm = {q: i for i, q in enumerate(S.qid)}
idx = [pm[q] for q in PO.qid]
first_full = [XR[i, col[int(fk) + 1]] for i, fk in zip(idx, PO.first_k)]
PO["first_full"] = first_full
PO["lr_abs"] = [np.nanmean(XR[i, col[24]:col[34] + 1]) for i in idx]
PO["keep_ratio"] = PO.lr_abs / PO.first_full.replace(0, np.nan)
late = O[(O.posthumous == 1) & (O.first_k >= 2)]
R2["posthumous"] = {"n_eligible": int(len(O)), "created_k0_k1": int(len(PO)), "pc": round(100 * len(PO) / len(O), 1),
                    "created_km1": int(O.created_km1.sum()), "first_seen_k2plus": int(len(late)),
                    "first_seen_k12plus": int((late.first_k >= 12).sum()),
                    "median_first_full": round(float(np.nanmedian(PO.first_full))), "median_lr_abs": round(float(np.nanmedian(PO.lr_abs)), 1),
                    "median_keep_ratio": round(float(np.nanmedian(PO.keep_ratio)), 3),
                    "women_pc": round(100 * float((PO.sex == "Q6581072").mean()), 1), "women_pc_pre": round(100 * float((M.sex == "Q6581072").mean()), 1),
                    "links_med": float(PO.links.median()), "links_med_pre": float(M.links.median()),
                    "family_pc": {f: round(100 * float((PO.family == f).mean()), 1) for f in FAMILIES},
                    "family_pc_pre": {f: round(100 * float((M.family == f).mean()), 1) for f in FAMILIES}}
# ---------------- representativeness of the hash sample
A = S  # sample only
full = pd.read_csv(f"{SCR}/people_all.csv")
full["sex2"] = full.sex.map({"Q6581097": "men", "Q6581072": "women"}).fillna("other or unknown")
rep = {"n_full": int(len(full)), "n_sample": int(len(A))}
for nm, D in (("full", full), ("sample", A), ("main", M)):
    rep[nm] = {"women_pc": round(100 * float((D.sex2 == "women").mean()), 2), "links_median": float(D.links.median()), "links_mean": round(float(D.links.mean()), 2),
               "family_pc": {f: round(100 * float((D.family == f).mean()), 1) for f in FAMILIES},
               "year_pc": {str(y): round(100 * float((D.dyear == y).mean()), 1) for y in range(2016, 2024)},
               "english_pc": round(100 * float(D.cit.isin(list(ENGLISH)).mean()), 1), "age_median": round(float(D.age.median()), 1)}
R2["rep"] = rep
R2["n_main"] = int(len(M)); R2["n_clusters"] = int(M.dm.nunique()); R2["n_placebo"] = int(len(PLm))
R2["main_desc"] = {"women_pc": rep["main"]["women_pc"], "english_pc": rep["main"]["english_pc"], "age_median": rep["main"]["age_median"],
                   "n_women": int((M.sex2 == "women").sum()), "n_men": int((M.sex2 == "men").sum()), "us_pc": round(100 * float((M.cit == "Q30").mean()), 1),
                   "n_family": {f: int((M.family == f).sum()) for f in FAMILIES}, "n_age": {a: int((M.ageb == a).sum()) for a in groups["ageb"] + ["unknown"]},
                   "n_lang": {a: int((M.lang == a).sum()) for a in ("English-speaking", "other", "unknown")}}

# ---------------- countries (citizenship) for the map
lab = pd.read_csv(f"{RAW}/fame_labels.tsv", sep="\t", dtype=str, quoting=3); lab.columns = ["x", "l", "c"]
lab["x"] = lab.x.map(qid); lab["l"] = lab.l.map(lit); labd = dict(zip(lab.x, lab.l))
cr = []
for c, g in M.groupby("cit"):
    if len(g) < 30: continue
    ci_ = med_ci(g.lr, 300); cp = med_ci(g.peak, 300)
    cr.append({"cit": c, "name": labd.get(c, c), "n": len(g), "lr": ci_["median"], "lr_lo": ci_["lo"], "lr_hi": ci_["hi"], "peak": cp["median"],
               "y1": round(float(g.y1.median()), 3), "lr_above1_pc": round(100 * float((g.lr > 1).mean()), 1), "women_pc": round(100 * float((g.sex2 == "women").mean()), 1),
               "top_family": g.family.value_counts().index[0]})
CT = pd.DataFrame(cr).sort_values("n", ascending=False)
CT.to_csv(f"{DATA}/countries.csv", index=False)
R2["countries"] = {"n": int(len(CT)), "people": int(CT.n.sum()), "rows": CT.to_dict("records")}
M.to_csv(f"{SCR}/main.csv", index=False)
jsave(R2, f"{SCR}/r2.json", indent=1)
print("fits", {k: (v["aic"], v["oos_rmse"], v["half_life"]) for k, v in R2["fits"].items()}, "best", best_aic, best_oos)
print("two-phase", R2["two_phase"], R2["two_phase_ci"])
print("peak", R2["peak"], "y1", R2["y1"], "lr", R2["lr"], "lr>1", R2["lr_above1_pc"])
print("placebo", R2["placebo"])
for k in ("women", "age_u50", "age_90", "english", "llinks", "lbase") + tuple("fam_" + f for f in FAMILIES[1:]):
    print(k, H4["lr"][k], "| peak", H4["peak"][k])
print("wald", H4["lr"]["wald_family_p"], H4["peak"]["wald_family_p"])
