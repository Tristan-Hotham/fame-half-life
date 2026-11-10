"""Step 1: people table (one row per Wikidata person), occupation families, the 30% hash sample and the monthly
pageview series aligned on months since death. Writes SCR/people.parquet-like CSV and SCR/series.npz (views per month
for every sampled person) plus data/occupations.csv (the occupation to family table, for checking).
No post-death outcome is computed here."""
import numpy as np, pandas as pd
from common import *

d = pd.read_csv(f"{RAW}/fame_wd.tsv", sep="\t", dtype=str, quoting=3)
d.columns = [c.lstrip("?") for c in d.columns]
n_rows = len(d)
d["q"] = d.p.map(qid)
d["title"] = d.title.map(lit)
for c in ("sex", "occ1", "cit1"):
    d[c] = d[c].map(lambda x: qid(x) if isinstance(x, str) else None)
d["links"] = d.links.astype(int)
L = pd.read_csv(f"{RAW}/fame_labels.tsv", sep="\t", dtype=str, quoting=3)
L.columns = ["x", "l", "cls"]
L["x"] = L.x.map(qid); L["l"] = L.l.map(lit); L["cls"] = L.cls.map(lambda x: qid(x) if isinstance(x, str) else None)
lab = dict(zip(L.x, L.l)); sup = dict(zip(L.x, L.cls))
d["occ_label"] = d.occ1.map(lab)
d["occ_sup"] = d.occ1.map(lambda q: lab.get(sup.get(q)) if q else None)
occ_tab = d.drop_duplicates("occ1")[["occ1", "occ_label", "occ_sup"]].dropna(subset=["occ1"]).copy()
occ_tab["family"] = [family(a, b) for a, b in zip(occ_tab.occ_label, occ_tab.occ_sup)]
fam = dict(zip(occ_tab.occ1, occ_tab.family))
d["fam_row"] = d.occ1.map(lambda q: fam.get(q, "Other") if q else "Other")


def first_date(s):
    v = sorted(x[:10] for x in s.dropna() if isinstance(x, str) and re.match(r"^\d{4}-\d\d-\d\d", x))
    return v


rows = []
for q, g in d.groupby("q", sort=False):
    dods = first_date(g.dod); dobs = first_date(g.dob)
    fams = list(g.fam_row)
    ok = [i for i, f in enumerate(fams) if f != "Other"]
    i = ok[0] if ok else 0
    occs = sorted(set(x for x in g.occ1 if isinstance(x, str)))
    cits = [x for x in g.cit1 if isinstance(x, str)]
    dob_conf = len(dobs) > 1 and abs(int(dobs[-1][:4]) - int(dobs[0][:4])) > 1
    rows.append({"qid": q, "title": g.title.iloc[0], "dod": dods[0] if dods else None, "dod_n": len(set(dods)),
                 "dob": dobs[0] if dobs else None, "dob_conflict": int(dob_conf), "sex": g.sex.dropna().iloc[0] if g.sex.notna().any() else None,
                 "occ": g.occ1.iloc[i], "occ_first": g.occ1.iloc[0], "family": fams[i], "family_first": fams[0],
                 "n_occ": len(occs), "fams_all": "|".join(sorted(set(fams))), "cit": cits[0] if cits else None,
                 "cit_multi": int(len(set(cits)) > 1), "links": int(g.links.max())})
P = pd.DataFrame(rows)
P["occ_label"] = P.occ.map(lab)
P["cit_label"] = P.cit.map(lab)
P["sex_label"] = P.sex.map(lab)
P["sample"] = P.qid.map(hsample).astype(int)
P["dod_jan1"] = P.dod.str[5:].eq("01-01").astype(int)
y, m = P.dod.str[:4].astype(int), P.dod.str[5:7].astype(int)
P["dyear"] = y; P["dmonth"] = m; P["dday"] = P.dod.str[8:10].astype(int)
P["mi"] = y * 12 + m - 1 - M0                     # month index of death in the series (0 = 2015-07)
by = pd.to_numeric(P.dob.str[:4], errors="coerce")
bm = pd.to_numeric(P.dob.str[5:7], errors="coerce")
P["age"] = np.where(P.dob_conflict == 1, np.nan, (y + (m - 1) / 12) - (by + (bm.fillna(7) - 1) / 12))
P.loc[(P.age < 0) | (P.age > 120), "age"] = np.nan
P["english"] = P.cit.isin(ENGLISH).astype(int)
P.loc[P.cit.isna(), "english"] = np.nan

# pageviews: dense monthly arrays for the sample
pv = jload(f"{RAW}/fame_pageviews.json")
samp = set(P.qid[P["sample"] == 1])
assert len(samp) == 29384, len(samp)
assert set(pv) <= samp
V = np.zeros((len(P), NM), dtype=np.int64)
first = np.full(len(P), -1); fetched = np.zeros(len(P), int); empty = np.zeros(len(P), int)
idx = {q: i for i, q in enumerate(P.qid)}
for q, ser in pv.items():
    i = idx[q]; fetched[i] = 1
    if not ser:
        empty[i] = 1; continue
    for ym, v in ser:
        j = int(ym[:4]) * 12 + int(ym[4:]) - 1 - M0
        V[i, j] = v
    first[i] = int(ser[0][0][:4]) * 12 + int(ser[0][0][4:]) - 1 - M0
P["fetched"] = fetched; P["not_found"] = empty; P["first_mi"] = first
P["first_k"] = np.where(first >= 0, first - P.mi, np.nan)
E = jload(f"{RAW}/enwiki_monthly.json")["items"]
en = np.array([e["views"] for e in E], dtype=float)
assert len(en) == NM and E[0]["timestamp"].startswith("201507") and E[-1]["timestamp"].startswith("202610")
P["views_total"] = V.sum(1)
keep = P["sample"].eq(1).values
np.savez_compressed(f"{SCR}/series.npz", V=V[keep], qid=P.qid[keep].values, en=en)
P.to_csv(f"{SCR}/people_all.csv", index=False)
occ_tab["n"] = occ_tab.occ1.map(P.occ.value_counts()).fillna(0).astype(int)
occ_tab.sort_values("n", ascending=False).to_csv(f"{DATA}/occupations.csv", index=False)
info = {"n_rows": n_rows, "n_people": len(P), "n_sample": int(keep.sum()), "n_fetched": int(fetched.sum()), "n_not_found": int(empty.sum()),
        "n_failed": int(keep.sum() - fetched.sum()), "n_dod_multi": int((P.dod_n > 1).sum()), "n_dob_conflict": int(P.dob_conflict.sum()),
        "n_multi_occ": int((P.n_occ > 1).sum()), "n_jan1": int(P.dod_jan1.sum()), "n_occ_labels": int(len(occ_tab))}
jsave(info, f"{SCR}/r1.json", indent=1)
print(info)
print(P.family.value_counts())
