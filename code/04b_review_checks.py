"""Step 4b (added at independent review; every result here is EXPLORATORY, not part of the written plan).
Adds results.json["review"]:
  drift36     bootstrap 95% interval for the "about 5% above a no-death path" comparison (ratio of the real to the
              placebo median two-to-three-year ratio, same people), and the median person-level ratio.
  rtm         main LR model with the pre-death attention control measured in a separate, earlier window
              (k = -24 to -13) instead of the baseline window that is also the ratio's denominator, so that
              measurement noise in the baseline is not shared with the outcome (regression to the mean).
  cluster_cit main LR model with standard errors clustered by country of citizenship instead of month of death.
  dropped     who the articles first seen 2+ months after death (mostly renamed titles, dropped) are, against the main sample.
  rawviews_note  the raw-views robustness check equals the main model by construction (see text).
"""
import warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20262)
R = jload(f"{DATA}/results.json")
M = pd.read_csv(f"{SCR}/main.csv")
S = pd.read_csv(f"{SCR}/people.csv")
Z = np.load(f"{SCR}/event.npz", allow_pickle=True)
X, K, qz = Z["X"].astype(float), Z["K"], Z["qid"]
col = {int(k): j for j, k in enumerate(K)}
out = {"label": "Exploratory checks added at independent review (not pre-specified)"}

# 1. bootstrap interval for the no-death-path comparison
P = M[(M.pl36_ok == 1)].copy()
real, pl = P.lr.values, P.pl36_lr.values
ok = np.isfinite(real) & np.isfinite(pl) & (pl > 0)
real, pl = real[ok], pl[ok]
bs = []
for _ in range(1000):
    i = rng.integers(0, len(real), len(real))
    bs.append(np.median(real[i]) / np.median(pl[i]))
indiv = np.median(np.log(np.maximum(real, FLOOR)) - np.log(np.maximum(pl, FLOOR)))
bi = []
for _ in range(1000):
    i = rng.integers(0, len(real), len(real))
    bi.append(np.median(np.log(np.maximum(real[i], FLOOR)) - np.log(np.maximum(pl[i], FLOOR))))
out["drift36"] = {"n": int(len(real)), "ratio": round(float(np.median(real) / np.median(pl)), 3),
                  "ratio_lo": round(float(np.percentile(bs, 2.5)), 3), "ratio_hi": round(float(np.percentile(bs, 97.5)), 3),
                  "pc": round(100 * (np.median(real) / np.median(pl) - 1), 1), "pc_lo": round(100 * (np.percentile(bs, 2.5) - 1), 1),
                  "pc_hi": round(100 * (np.percentile(bs, 97.5) - 1), 1),
                  "indiv_pc": round(100 * (np.exp(indiv) - 1), 1), "indiv_lo": round(100 * (np.exp(np.percentile(bi, 2.5)) - 1), 1),
                  "indiv_hi": round(100 * (np.exp(np.percentile(bi, 97.5)) - 1), 1)}

# 2. regression to the mean: control for prior attention measured in k = -24 to -13
idx = {q: i for i, q in enumerate(qz)}
rows = np.array([idx[q] for q in M.qid])
Xm = X[rows]
pre = np.nanmean(Xm[:, col[-24]:col[-13] + 1], axis=1)
npre = np.sum(~np.isnan(Xm[:, col[-24]:col[-13] + 1]), axis=1)
M["lpre"] = np.where((npre >= 6) & (pre > 0), np.log(np.where(pre > 0, pre, 1)), np.nan)
FORM = ("llr ~ C(family, Treatment('Performers')) + C(sex2, Treatment('men')) + C(ageb, Treatment('65 to 79')) + "
        "C(lang, Treatment('other')) + llinks + {ctl} + C(dyear) + C(dmonth)")
T = {"women": "C(sex2, Treatment('men'))[T.women]", "age_u50": "C(ageb, Treatment('65 to 79'))[T.under 50]",
     "age_90": "C(ageb, Treatment('65 to 79'))[T.90 and over]", "english": "C(lang, Treatment('other'))[T.English-speaking]",
     "fam_Sport": "C(family, Treatment('Performers'))[T.Sport]", "fam_Science and academia": "C(family, Treatment('Performers'))[T.Science and academia]"}


def pc(res, t):
    b, se = res.params[t], res.bse[t]
    return {"b": round(100 * (np.exp(b) - 1), 1), "lo": round(100 * (np.exp(b - 1.96 * se) - 1), 1), "hi": round(100 * (np.exp(b + 1.96 * se) - 1), 1)}


D = M.dropna(subset=["llr", "lpre"])
res = smf.ols(FORM.format(ctl="lpre"), D).fit(cov_type="cluster", cov_kwds={"groups": D.dm.values})
res0 = smf.ols(FORM.format(ctl="lbase"), D).fit(cov_type="cluster", cov_kwds={"groups": D.dm.values})
out["rtm"] = {"n": int(res.nobs), "ctl": "log mean share k = -24 to -13",
              "earlier_control": {k: pc(res, t) for k, t in T.items()}, "same_people_main_control": {k: pc(res0, t) for k, t in T.items()}}

# 3. clustering by country of citizenship
D = M.dropna(subset=["llr"]).copy()
D["cl"] = D.cit.fillna("unknown")
res = smf.ols(FORM.format(ctl="lbase"), D).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(D.cl)[0]})
out["cluster_cit"] = {"n": int(res.nobs), "n_clusters": int(D.cl.nunique()), **{k: pc(res, t) for k, t in T.items()}}

# 4. the dropped late-first-seen articles (mostly renamed titles) against the main sample
okb = (S.fetched == 1) & (S.not_found == 0) & (S.dod_jan1 == 0) & (S.base_avail >= MIN_BASE)
late = S[okb & (S.first_k >= 2)]
m = S[S.main == 1]
def desc(d):
    return {"n": int(len(d)), "women_pc": round(100 * (d.sex_label == "female").mean(), 1), "links_med": float(d.links.median()),
            "sport_pc": round(100 * (d.family == "Sport").mean(), 1), "english_pc": round(100 * (d.english == 1).mean(), 1),
            "age_med": round(float(d.age.median()), 1)}
out["dropped"] = {"late": desc(late), "main": desc(m), "late_first_k_med": float(late.first_k.median())}
# 5. titles that look like former redirects: a current title with almost no views before death (under 5 a month on
# average in the baseline) or no rise at all at death (peak ratio below 1) while the long-run ratio is above 5. Such a
# series measures the title, not the person (the article was moved onto a title that had been a redirect).
red = (M.base_views < 5) | ((M.peak < 1) & (M.lr > 5))
D = M[~red].dropna(subset=["llr"])
res = smf.ols(FORM.format(ctl="lbase"), D).fit(cov_type="cluster", cov_kwds={"groups": D.dm.values})
out["redirect_like"] = {"n_flagged": int(red.sum()), "n": int(res.nobs), "lr_median": round(float(D.lr.median()), 3),
                        "peak_median": round(float(D.peak.median()), 2), **{k: pc(res, t) for k, t in T.items()}}
out["rawviews_note"] = ("log LR in raw views differs from log LR in shares by log(mean enwiki total over the LR window / over the baseline), "
                        "which depends only on the month of death; death-year and calendar-month fixed effects together identify the "
                        "month of death, so the coefficients are identical by construction.")
R["review"] = out
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)
print(json.dumps(out, indent=1))
