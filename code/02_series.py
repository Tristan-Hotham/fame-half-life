"""Step 2: event-time series and person-level measures (peak, one-year retention, long-run ratio, first-year excess,
placebo measures), sample flow. Writes SCR/people.csv and SCR/event.npz (share of enwiki views, per million, by
months since death k = KMIN..KMAX; NaN outside the data window or before the article's first month with views)."""
import numpy as np, pandas as pd
from common import *

P = pd.read_csv(f"{SCR}/people_all.csv")
Z = np.load(f"{SCR}/series.npz", allow_pickle=True)
V, qs, en = Z["V"], Z["qid"], Z["en"]
S = P[P["sample"] == 1].set_index("qid").loc[qs].reset_index()
assert len(S) == len(V)
K = np.arange(KMIN, KMAX + 1)
n = len(S)
share = V / en[None, :] * 1e6                       # views per million enwiki views
X = np.full((n, len(K)), np.nan, dtype=np.float64)   # share by event time
XR = np.full((n, len(K)), np.nan, dtype=np.float64)  # raw views by event time
mi = S.mi.values.astype(int); first = S.first_mi.values.astype(int)
for j, k in enumerate(K):
    t = mi + k
    ok = (t >= 0) & (t < NM) & (first >= 0) & (t >= first)
    X[ok, j] = share[np.where(ok)[0], t[ok]]
    XR[ok, j] = V[np.where(ok)[0], t[ok]]
col = {k: j for j, k in enumerate(K)}


def wmean(A, a, b):
    return np.nanmean(A[:, col[a]:col[b] + 1], axis=1)


def wcount(A, a, b):
    return np.sum(~np.isnan(A[:, col[a]:col[b] + 1]), axis=1)


import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
S["base_n"] = wcount(X, *BASE)
S["base_avail"] = [sum(1 for k in range(BASE[0], BASE[1] + 1) if m + k >= 0) for m in mi]
S["preexisting"] = ((first >= 0) & (first <= np.maximum(mi + BASE[0], 0))).astype(int)
S["base"] = wmean(X, *BASE)
S["base_views"] = wmean(XR, *BASE)
S["base_strict"] = (S.base_n == 11).astype(int)
S["peak"] = np.nanmax(X[:, [col[0], col[1]]], axis=1) / S.base
S["peak_k"] = np.where(X[:, col[1]] > X[:, col[0]], 1, 0)
S["peak_views"] = np.nanmax(XR[:, [col[0], col[1]]], axis=1)
S["y1"] = wmean(X, *YEAR1) / S.base
S["lr"] = wmean(X, *LONG) / S.base
S["lr_n"] = wcount(X, *LONG)
S["excess1"] = np.nansum(X[:, col[0]:col[11] + 1], axis=1) / S.base - 12
S["lr_views"] = wmean(XR, *LONG) / S.base_views                     # raw views, no enwiki normalisation
S["peak_views_ratio"] = np.nanmax(XR[:, [col[0], col[1]]], axis=1) / S.base_views
S["lr_alt"] = wmean(X, 18, 30) / S.base                            # alternative long-run window
S["base6"] = wmean(X, -6, -2)
S["lr_b6"] = wmean(X, *LONG) / S.base6
S["peak_b6"] = np.nanmax(X[:, [col[0], col[1]]], axis=1) / S.base6
# bot-like spikes in the baseline: a month > 20x the median of the other baseline months and >= 1000 views
B = XR[:, col[BASE[0]]:col[BASE[1]] + 1]
spike = np.zeros(n, int)
for i in range(n):
    b = B[i][~np.isnan(B[i])]
    if len(b) >= 3:
        for j in range(len(b)):
            o = np.delete(b, j)
            if b[j] >= 1000 and b[j] > 20 * max(np.median(o), 1):
                spike[i] = 1; break
S["bot_spike"] = spike
# placebo: fake death 24 months before the real one
pb = wmean(X, -36, -26); pn = wcount(X, -36, -26)
S["pl_ok"] = ((pn >= 6) & (first >= 0) & (first <= np.maximum(mi - 36, 0)) & (pb > 0)).astype(int)
S["pl_peak"] = np.nanmax(X[:, [col[-24], col[-23]]], axis=1) / pb
S["pl_y1"] = wmean(X, -14, -10) / pb
S["pl_base"] = pb
# exploratory (added after the first run): a fake death 36 months earlier, so that the fake months 24 to 34 are the
# real baseline months -12 to -2: the drift of attention over two to three years with no death
pb36 = wmean(X, -48, -38); pn36 = wcount(X, -48, -38)
S["pl36_ok"] = ((pn36 >= 6) & (first >= 0) & (first <= np.maximum(mi - 48, 0)) & (pb36 > 0)).astype(int)
S["pl36_lr"] = S.base / pb36
# posthumous: article first seen at or after the month of death
S["posthumous"] = ((first >= 0) & (first >= mi)).astype(int)
S["created_km1"] = ((first >= 0) & (first == mi - 1)).astype(int)
S["first_k"] = np.where(first >= 0, first - mi, np.nan)
S["views_k0"] = XR[:, col[0]]
S["lr_views_abs"] = wmean(XR, *LONG)

# sample flow
f = {}
f["sample"] = n
f["fetched"] = int(S.fetched.sum())
f["not_found"] = int(S.not_found.sum())
ok = (S.fetched == 1) & (S.not_found == 0)
f["with_views"] = int(ok.sum())
f["jan1"] = int((ok & (S.dod_jan1 == 1)).sum()); ok &= S.dod_jan1 == 0
f["too_early"] = int((ok & (S.base_avail < MIN_BASE)).sum()); ok &= S.base_avail >= MIN_BASE
f["posthumous"] = int((ok & (S.posthumous == 1)).sum())
f["created_km1"] = int((ok & (S.created_km1 == 1)).sum())
f["not_preexisting"] = int((ok & (S.preexisting == 0)).sum()); ok &= S.preexisting == 1
f["zero_base"] = int((ok & ~(S.base > 0)).sum()); ok &= S.base > 0
f["main"] = int(ok.sum())
S["main"] = ok.astype(int)
# robustness sample including 1 January dates
okj = (S.fetched == 1) & (S.not_found == 0) & (S.base_avail >= MIN_BASE) & (S.preexisting == 1) & (S.base > 0)
S["main_jan1"] = okj.astype(int)
for c in ("peak", "y1", "lr", "excess1", "lr_views", "peak_views_ratio", "lr_alt", "lr_b6", "peak_b6", "pl_peak", "pl_y1"):
    S[c] = S[c].replace([np.inf, -np.inf], np.nan)
keep = S.main_jan1.values.astype(bool) | (S.posthumous.values == 1) | (S.created_km1.values == 1)
np.savez_compressed(f"{SCR}/event.npz", X=X.astype(np.float32), XR=XR.astype(np.float32), K=K, qid=S.qid.values)
S.to_csv(f"{SCR}/people.csv", index=False)
jsave(f, f"{SCR}/flow.json", indent=1)
print(f)
m = S[S.main == 1]
print("bot spikes in main", int(m.bot_spike.sum()), "placebo ok", int(m.pl_ok.sum()), "strict", int(m.base_strict.sum()))
