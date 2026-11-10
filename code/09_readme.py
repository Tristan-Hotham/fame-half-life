"""Step 9: README.md filled from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); p = R["prose"]; H = R["H4"]["lr"]; f = R["flow"]
e = lambda v: f"{v['b']:+.0f}% (95% CI {v['lo']:.0f} to {v['hi']:.0f})"
txt = f"""# The half-life of fame

How attention to notable people on English Wikipedia rises and decays after their deaths. Monthly user pageviews for {R['n_main']:,} people with an English Wikipedia article who died between February 2016 and December 2023 (a fixed 30% hash sample of Wikidata), each measured as a share of all English Wikipedia reading and against the person's own level in the year before death, followed for up to five years.

By Dr Tristan Hotham, Independent researcher, 2026.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24095452}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/fame-half-life/}}
Code and data: {REPO}

## Headline results

- The spike: in the month of death the median article is read {p['k0']:.1f} times as much as in the year before (median peak over the month of death and the next: {R['peak']['median']:.1f}, 95% CI {R['peak']['lo']:.1f} to {R['peak']['hi']:.1f}). The month after: {p['k1']:.2f}; a year on: {p['k12']:.2f}.
- The shape: a two-phase (biexponential) model fits best by AIC, with a fast half-life of {p['hl_fast_days']} days and a slow half-life of {p['hl_slow']:.1f} months; a power law predicts later cohorts slightly better out of sample (log RMSE {R['fits']['power law']['oos_rmse']:.3f} against {R['fits']['two-phase']['oos_rmse']:.3f}). Pre-set criterion only partly met.
- The settling point: two to three years after death the median person has {R['lr']['median']:.3f} (95% CI {R['lr']['lo']:.3f} to {R['lr']['hi']:.3f}) of their pre-death share; {R['lr_above1_pc']:.1f}% are above 1. Placebo (fake death 24 months earlier): one-year ratio {R['placebo']['y1']['median']:.3f}. Exploratory: against the pre-death drift people end about {p['vs_drift_pc']:.1f}% higher.
- Age: dying under 50 goes with {e(H['age_u50'])} more long-run attention than dying at 65 to 79; 90 and over {e(H['age_90'])}. Significant in all {R['robust_n']} robustness checks and absent at the placebo date.
- Occupation: performers are the only family whose median ends above 1 ({p['perf_lr']:.2f}); religious figures lowest ({p['rel_lr']:.2f}); sport {e(H['fam_Sport'])} vs performers. Placebo regressions show part of the occupational gaps predates the deaths.
- Sex: women {e(H['women'])}, significant in only {R['robust_nsig']['women']} of {R['robust_n']} checks and {R['H4_nobase']['lr']['women']['b']:+.1f}% without the baseline control: no robust difference.
- Articles created on death: {R['posthumous']['created_k0_k1']:,} of {R['posthumous']['n_eligible']:,} ({R['posthumous']['pc']:.1f}%) were first read in the month of death or the next.
- Observational and descriptive; pageviews measure looking up, not remembering.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: decay chart by occupation, age, sex and citizenship (hover values, group toggles, log or linear, full screen) and a MapLibre world map by citizenship with a layers panel. |
| `header.png` | Social card, 1200 x 630. |
| `data/people.csv` | Person-level measures for the main sample and articles created on death ({R['flow']['main']:,} + posthumous): QID, title, dates, sex, occupation and family, citizenship, sitelinks, baseline, peak, one-year and long-run ratios, placebo measures, flags. No raw series. |
| `data/curves.csv` | Median curves (and 95% bootstrap intervals) by months since death, for everyone and each group; geometric mean and ratio of sums for everyone. |
| `data/models.csv` | Every regression coefficient (main, robustness, placebo). |
| `data/countries.csv`, `data/countries.geojson` | Medians by country of citizenship (30 or more people) and the simplified map layer (Natural Earth). |
| `data/occupations.csv` | Every Wikidata occupation label in the data with its superclass and family. |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/site.json` | Page data. |
| `code/` | Numbered pipeline, templates, `qa.js`. |
| `release/` | Paper (`paper/`, with `cover_note.md`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage, looping GIF, `collage.py` and post text. |
| `NOTES.md` | The analysis plan (written before any post-death measure was computed), the log, and the reference checks. |

## Method in brief

- People: Wikidata humans with an English Wikipedia article and a date of death in 2016 to 2023 ({R['data']['n_people']:,}); one row per person; dates of death on 1 January excluded (possible year precision).
- Sample: hash(QID) mod 10 < 3, h = (h*31 + charCode) >>> 0 over the QID string ({R['data']['n_sample']:,}); monthly user pageviews July 2015 to October 2026.
- Measures: share of all English Wikipedia user views; baseline = months -12 to -2; peak = max of months 0 and 1; one-year = months 10 to 14; long-run = months 24 to 34.
- Models: median curves with bootstrap intervals; exponential, power-law and two-phase decay fits; OLS of log ratios on occupation family, sex, age band, citizenship, log sitelinks, log baseline, year and calendar-month-of-death fixed effects, errors clustered by month of death; {R['robust_n']} robustness checks; placebo at a fake date 24 months before death.

## How to rerun

Python 3 with pandas, numpy, scipy, statsmodels, matplotlib, Pillow, pyproj, shapely; xelatex, pdftotext; node with Playwright for `code/qa.js`. Raw inputs are listed in `code/common.py`; intermediates go to `FH_SCRATCH`.

```
python3 code/01_data.py        # people, occupations, sample, monthly series
python3 code/02_series.py      # event-time series and person-level measures
python3 code/03_models.py      # the planned analysis
python3 code/04_results.py     # results.json and data tables
python3 code/04b_review_checks.py  # exploratory checks added at independent review (results.json["review"])
python3 code/05_figures.py     # figures and the map layer
python3 code/06_build_site.py  # index.html
python3 code/07_paper.py       # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage and header.png
python3 code/09_readme.py      # README
python3 code/08_release.py     # blog post and Zenodo files
node code/qa.js                # screenshots
```

## Sources and licences

- English Wikipedia pageviews, agent "user", from the Wikimedia pageviews API (CC0).
- Wikidata, queried with QLever (CC0).
- Natural Earth country boundaries (public domain). Base map: OpenFreeMap, OpenStreetMap data (ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and derived data CC BY 4.0; code MIT (see `LICENSE`).

## Citation

Hotham, T. (2026). The Half-Life of Fame: How Attention to Notable People on English Wikipedia Rises and Decays after Their Deaths. Zenodo. {{https://doi.org/10.5281/zenodo.24095452}}

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in txt.replace("```", "").replace("|---|---|", ""), (bad, [l for l in txt.splitlines() if bad in l][:3])
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(txt)
print("README", len(txt.split()), "words")
