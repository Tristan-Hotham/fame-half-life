# fame-half-life: working notes

Brief: /home/claude/work/new12/BRIEFS.md section 5 (+ shared rules new11 > new8/new9/new10, house brief newdata/BRIEF.md).
Format refs: /home/claude/studies/pm-streets/ and /home/claude/studies/wiki-vs-hansard/.
Scratch: /home/claude/scratch/fame-half-life (delete by exact path at the end).

## Data construction (checked before any outcome was computed)

- fame_wd.tsv: 100,689 rows, 98,246 distinct QIDs (rows repeat where Wikidata has two dates of birth, two dates of
  death or several occupations; one occupation and one citizenship were sampled per row by the query).
  Rule: one row per QID; date of death = earliest value; date of birth = earliest value, `dob_conflict` = values more
  than one year apart (age then set missing); occupation = the first occupation in file order whose family is not
  "other", else the first; all distinct occupations kept in `occs` for a multi-occupation check.
- Dates of death recorded as 1 January (YYYY-01-01) may be year-precision values in Wikidata (the export does not carry
  precision). Rule: excluded from the main sample (`dod_jan1`), included in a robustness check.
- Sample: hash(QID) mod 10 < 3 with h = (h*31 + charCode) >>> 0 over the QID string: reproduces exactly 29,384 QIDs.
  29,364 fetched; 9 returned [] (title not found at fetch time: renamed or deleted, reported); 20 failed fetches absent.
- fame_pageviews.json: monthly user-agent views, months with no views are absent (1,406 series have gaps): treated as 0
  between the first and last month. A series that starts after 2015-07 is an article that did not exist (or had no
  views) before that month. 14,595 series start in 2015-07 (the first month the API serves).
- enwiki_monthly.json: 136 months 2015-07 to 2026-10, all-access user views.

## Analysis plan (written before computing any post-death outcome)

Question: after a notable person dies, how big is the rise in attention to their English Wikipedia article, how fast
does it fade, and where does it settle relative to before the death? Who is forgotten fastest and who gains?

Unit: a person in the 30% hash sample with an English Wikipedia article, who died February 2016 to December 2023.

Attention measure: share of English Wikipedia traffic, s_t = views_t / enwiki_t (scaled per million enwiki views).
Normalising by the enwiki total removes the long decline in overall traffic (and changes in what counts as user traffic).

Event time: k = months since the calendar month of death (k = 0 is the month of death). Because the death month
contains days before the death, the spike is defined over k = 0 and k = 1.

Baseline: mean share over k = -12 to -2 (k = -1 excluded: illness and news before death). Require at least 6 of these
11 months inside the data window (so deaths from February 2016 can enter with a short baseline) and the article to
exist at the start of the available baseline (`preexisting`). Baseline zero: excluded from ratios (counted).

Person-level outcomes (all as ratios to the person's own baseline, analysed on the log scale):
- Peak: max(s_0, s_1) / baseline.
- One-year retention: mean share k = 10 to 14 / baseline.
- Long-run ratio (LR): mean share k = 24 to 34 / baseline. (The brief says 24 to 36 months; 34 is the longest
  follow-up every death in the sample has, since the data end in October 2026 and the last deaths are December 2023.)
- Excess cumulative attention in the first year: sum over k = 0..11 of (s_k / baseline - 1).

Aggregate decay curve: for each k = 0..60, the median across people of R_k = s_k / baseline (and the geometric mean,
mean of log R_k with R_k floored at 0.05), with bootstrap 95% intervals (people resampled, 500 draws). Excess
E_k = R_k - R_inf where R_inf is estimated with the model.

Decay models (fitted to the median curve and to the geometric mean curve, k = 1..60, least squares on log R_k,
following Candia et al. 2019, who fit a biexponential to attention decay and compare it with exponential and log-normal forms; the power law is the usual
alternative in forgetting and online-attention work):
- M-exp: R_k = c + a exp(-k / tau)            (3 parameters)
- M-pow: R_k = c + a k^(-b)                    (3 parameters)
- M-bi:  R_k = c + a exp(-k / t1) + b exp(-k / t2)   (5 parameters; two-phase: "communicative" fast and slower decay)
Compare by AIC and BIC on the residuals and by out-of-sample error on deaths 2020 to 2023 when fitted on 2016 to 2019.
Half-life: months for the excess (R_k - c) to fall to half of its value at k = 1, from the preferred model, and the
empirical first month in which the median excess falls below half of the k = 1 excess.

Hypotheses (and what would count against them):
- H1 spike: the median peak ratio is above 1. Report its size. (Trivially expected; the interest is in magnitude.)
- H2 shape: the two-phase model fits better than the single exponential and the power law (lower AIC and lower
  out-of-sample error). Against: either one-component model wins on both criteria.
- H3 settling point: two-sided. Does attention settle above the pre-death baseline? Median LR with a bootstrap 95%
  interval and the share of people with LR > 1. "Above" if the CI of the median lies above 1, "back to baseline" if it
  includes 1, "below" if it lies below 1. Alongside, the placebo LR (below) tells us what the drift would be with no death.
- H4 who keeps attention: OLS of log LR (and log peak, log one-year retention) on occupation family (reference:
  performers), sex (reference: men), age at death bands (<50, 50-64, 65-79 reference, 80-89, 90+), English-speaking
  citizenship (US, UK, Canada, Australia, New Zealand, Ireland), log Wikidata sitelinks, log baseline share (pre-death
  attention), death-year fixed effects and calendar month of death fixed effects. Standard errors clustered by month of
  death (up to 95 clusters). Two-sided expectations: (a) occupation families differ (joint Wald test); (b) women vs
  men: no prior sign; (c) younger deaths have bigger peaks and higher LR (unexpected deaths, careers cut short);
  (d) English-speaking citizens have bigger peaks on English Wikipedia; (e) sitelinks: more famous people have smaller
  relative peaks. Against: CIs including 0. Effects reported as percentage differences exp(b) - 1 with 95% CIs.
- Posthumous notability (descriptive): articles first seen at or after the month of death (k >= 0; and k = -1),
  how many, who, and how their views in months 24 to 34 compare with their first full month.

Robustness (pre-specified):
- R1 alternative specification: median (quantile) regression of log LR; OLS on winsorised log LR (1st/99th pct);
  HC1 standard errors instead of clustered.
- R2 placebo / falsification: a fake death 24 months before the real one. Baseline fake k = -12 to -2 (real k = -36
  to -26), placebo peak at fake k = 0 and 1, placebo "retention" at fake k = 10 to 14 (real k = -14 to -10): the
  drift over one year with no death. Needs deaths from about August 2018 with the article in place by real k = -36.
  Expect a placebo peak and retention near 1, and group differences in the placebo near 0 (if the occupation, sex or
  age differences in LR showed up in the placebo too, they would reflect pre-existing trends, not the death).
- R3 outliers: drop the top 1% by peak; drop people with baseline share in the top 1%; median curves (already robust).
- R4 leave-one-out: leave out each death year; leave out US citizens (the largest group); leave out each occupation
  family for the sex and age estimates.
- R5 measurement: raw views instead of enwiki share; baseline k = -6 to -2; LR window k = 18 to 30; include 1 January
  dates of death; strict baseline (all 11 months); drop series with bot-like spikes (any baseline month more than
  20 times the median of the other baseline months and at least 1,000 views); occupation = first occupation in file order.
- Weighting: the main analysis gives each person equal weight. A "ratio of sums" version (aggregate views of the group)
  is reported descriptively because it is dominated by the most famous people.
- Representativeness: compare the hash sample with the full 98,246 on sex, occupation family, year of death, sitelinks.
- Everything else is exploratory and labelled so.

Design honesty: observational and descriptive. Death is not randomly timed, and causes of death (sudden vs expected)
are not in the data. Pageviews measure looking up, not remembering or valuing. English Wikipedia readers are a
specific, English-reading, online audience. The sample is people with an English article who died 2016 to 2023 per
Wikidata, so people who became notable only through their death, and people whose article was later deleted, are in or
out in ways the data cannot fully show. One occupation and one citizenship were sampled per person.

## Log

- Plan written and data construction checked before any post-death measure was computed (steps 01 and 02 above).
- First run of the plan (03): flow 29,384 sampled; 29,355 with views; 2,827 1 January dates dropped; 292 too early (before
  Feb 2016); 9,421 without an article by the start of the baseline (8,650 first seen at or after the death month: 4,126 in
  the month of death or the next, so "created on death"; 4,524 first seen 2 or more months after death, most of them probably
  renamed titles, for example a disambiguated footballer's title first seen 17 months after his death); 418 zero baseline.
  Main sample N = 16,397 (95 death-month clusters).
- Fixes after the first run, before reading any regression: occupation rules used substring matches ("rector" inside
  "director", "polo" inside "anthropologist", "archer" inside "researcher"); changed to word-start matches plus a short
  override list (data/occupations.csv lists every label and its family). Labels were read with the TSV quote characters;
  fixed with quoting=3. A variable named C shadowed the patsy C(); renamed.
- Half-life definition: the planned "months for the k = 1 excess to halve" came out as 0.5 months (15 days), which is
  better described by the two phases of the preferred model: fast phase half-life 11 days, slow phase 6.9 months. The
  paper reports both and the empirical medians by month.
- Exploratory additions (labelled so everywhere): (a) a second placebo with a fake death 36 months earlier, so the fake
  months 24 to 34 are the real baseline: the drift over 2 to 3 years without a death (median 0.95); (b) the person-level
  difference between the real and the placebo one-year ratio, regressed on the same covariates; (c) the main models
  without the log baseline control.

## Results (main specification as planned)
- Peak median 16.5x baseline [16.0, 16.9]; month of death median 14.9x, month after 2.77x, k = 2 1.44x, k = 6 1.12x,
  k = 12 1.07x, k = 24 0.97x, k = 34 0.93x (single-month medians are about 0.95 before death because months are skewed).
- H2: two-phase best by AIC (also on k = 1..34 and the geometric-mean curve); power law best out of sample (RMSE 0.058 vs
  two-phase 0.060 vs exponential 0.068). Partial support, as pre-set (two-phase did not win both).
- H3: median LR 0.978 [0.971, 0.988]: back to (slightly below) the pre-death level; 47.8% above 1. Placebo one-year ratio
  0.966 (real 1.062). Exploratory: no-death drift over 24 to 34 months 0.952 vs real 0.998 in the same people (ratio 1.048).
- H4 (log LR, OLS, death-year and calendar-month FE, clustered by death month): under 50 +63% [51, 77]; 90+ -15% [-17, -12];
  English-speaking +23% [19, 27] (but +1% n.s. without the baseline control, and +6% in the median regression);
  log sitelinks 0.22; women -2.9% [-5.6, -0.1] (not robust: 6 of 21 checks exclude 0; +1% without baseline control);
  every occupation family below performers (sport -31%, politics -24%, science -24%, religion -34%); joint p < 1e-50.
  Peaks: under 50 +347%; journalists +49%, religion +30%; science -32%.
- Placebo regressions: sport, politics, science and English-speaking have pre-existing one-year drifts in the same direction
  (sport -13%, science -11%, English +7%), so part of the family gaps in LR is not the death. Age effects are absent in the
  placebo (under 50: -3%, n.s.) and survive the person-level difference (under 50 +94%, 90+ -19%).
- Posthumous: 4,126 of 26,236 eligible (15.7%) articles first seen in the month of death or the next; median views two to
  three years later 23% of their first full month.

## References: verification (WebSearch/WebFetch, 2026)
Checked online (publisher, RePEc/IDEAS, arXiv, repository or library records): Candia et al. 2019 (NHB 3(1) 82-91,
abstract read: biexponential beats log-normal and exponential); Keegan & Brubaker 2015 (CSCW 533-546); Garcia-Gavilanes et
al. 2017 (Sci Adv 3(4) e1602368, abstract read); Yu et al. 2016 (Sci Data 3 150075); Mestyan et al. 2013 (PLoS ONE 8(8)
e71226); Wagner et al. 2015 (ICWSM 9(1) 454-463); Wagner et al. 2016 (EPJ DS 5:5); Graells-Garrido et al. 2015 (HT 165-174);
Konieczny & Klein 2018 (NMS 20(12) 4608-4633); Ekelund et al. 2000 (JCE 24(4) 283-300); Rubin & Wenzel 1996 (Psych Rev
103(4) 734-760); Wixted & Ebbesen 1991 (Psych Sci 2(6), from 409; end page not confirmed); Roediger & DeSoto 2014 (Science
346(6213) 1106-1109); Zhang et al. 2023 (PNAS 120(35) e2302269120); Crane & Sornette 2008 (PNAS 105(41) 15649-15653);
Wu & Huberman 2007 (PNAS 104(45) 17599-17601); Ratkiewicz et al. 2010 (PRL 105 158701); Lehmann et al. 2012 (WWW 251-260);
West, Leskovec & Potts 2021 (PNAS 118(38) e2106152118, abstract read); Downs 1972 (Public Interest 28, from 38);
Halbwachs 1992 (ed. Coser, Chicago); Assmann & Czaplicka 1995 (NGC 65 125-133); Olick & Robbins 1998 (ARS 24, from 105);
Kanhabua et al. 2014 (JCDL 341-350); Michel et al. 2011 (Science 331(6014) 176-182); Laouenan et al. 2022 (Sci Data 9 290);
Gergaud et al. 2016 (Sciences Po working paper hal-03393214); Skiena & Ward 2013 (CUP); Koenker & Bassett 1978 (Econometrica
46(1) 33-50); Merton 1968 (Science 159(3810) 56-63); Samora 2018 (The Pudding, web essay). Reused from the reviewed
wiki-vs-hansard list: Vrandecic & Krotzsch 2014; Cameron & Miller 2015; Abadie et al. 2023; Lemmerich et al. 2019;
Singer et al. 2017; Seabold & Perktold 2010.
Dropped as not verifiable here: Pentzold 2009 (Memory Studies; repository blocked), Assmann 2008 (chapter; blocked),
Akaike 1974 (pages not confirmed), Lang & Lang 1988 (record paywalled), Jara-Figueroa et al. on a PNAS gender gap (not found).

## Deliverables
index.html + js/page.js (interactive decay chart with group toggles, scale and window switches, hover values, table;
MapLibre world map by citizenship with layers panel, metric chips, popups; full-screen on both; site-nav.js); header.png;
data/* (people.csv measures only, no raw series); code/01..09 + templates + qa.js; release/paper (PDF 21 pp, about 8,350
words before references, abstract 249 words, 36 references, cover_note.md), release/blog (post.html, 6 figures,
meta.json), release/zenodo; reddit/collage.py + collage + post.md + GIF (script /home/claude/gifs/scripts/fame-half-life.py).
QA: qa/*.jpg, 0 console errors at 1280 and 390 px. Scratch deleted at the end.

## Independent review (referee-style, 2026)

Reproduction. Ran 01 to 04 from the raw inputs (raw_new12: fame_wd.tsv, fame_pageviews.json, fame_labels.tsv,
enwiki_monthly.json) in a separate copy of the code: results.json, curves.csv, models.csv, countries.csv, people.csv and
occupations.csv came out identical (no numeric differences). Hash sample reproduces 29,384; flow 29,355 / 16,397 main.
Paper tables are filled from results.json; spot-checked the flow, family, fits, main, robustness and placebo tables.

Named examples checked against the data and public record: Prince (died 21 April 2016, 17,545,455 views that month),
Chadwick Boseman (28 August 2020), Stephen Hawking (14 March 2018), Carrie Fisher (27 December 2016), Prince Philip
(9 April 2021). All correct; used only in the paper's introduction and appendix, in neutral wording. Fine.

References spot-checked online (WebSearch/WebFetch, abstract or record read): Candia et al. 2019 (NHB 3(1) 82-91;
biexponential beats log-normal and exponential; biographies longest in communicative memory, 20 to 30 years: supports
the paper's use), Keegan and Brubaker 2015 (Crossref: CSCW '15, 533-546; about editors, not readers, as the paper says),
García-Gavilanes, Mollgaard, Tsvetkova and Yasseri 2017 (Sci Adv 3(4) e1602368; attention flows to past aviation
accidents; note the brief's "Mollett" is wrong, the paper's "Mollgaard" is right), West, Leskovec and Potts 2021
(2,362 figures, news and Twitter, young/unnatural deaths and anglophones largest boosts, artists largest and leaders
smallest long-term boosts: supports text), Zhang et al. 2023 (PNAS 120(35) e2302269120; 3,300+ artists, peak right
before death, decline also for young/unexpected deaths), Laouenan et al. 2022 (Sci Data 9, 290; abstract documents an
Anglo-Saxon bias in the English edition), Ekelund, Ressler and Watson 2000 (JCE 24(4) 283-300), Roediger and DeSoto
2014 (Science 346(6213) 1106-1109), Rubin and Wenzel 1996 (105 functions, 210 data sets), Wagner et al. 2016 (EPJ DS
5:5; women more notable, glass ceiling), Crane and Sornette 2008 (PNAS; power-law relaxation, YouTube), Kanhabua,
Nguyen and Niederée 2014 (JCDL 341-350), Konieczny and Klein 2018 (NMS 20(12) 4608-4633), Graells-Garrido et al. 2015
(HT 165-174), Mestyán et al. 2013, Lemmerich et al. 2019, Yu et al. 2016, Wixted and Ebbesen 1991 (2(6); end page still
not confirmed), Samora 2018. Fixed: Samora's essay is titled "Life After Death on Wikipedia" (was cited under an
invented descriptive title). Removed the attribution to Wu and Huberman 2007 of the claim that mixtures of exponentials
produce power-law aggregates (not what that paper shows); the claim is now stated without a citation.
Journal word limits (JCA, Memory Studies, SSCR) still could not be confirmed online (author pages blocked); cover note
says so and now suggests moving appendix and review checks to a supplement if a cap is near 8,000 to 9,000 words.

Fixes to text (paper, blog, page, post.md):
- "about 5% above a no-death path" was described in the blog and page as if it came from the two-year placebo; it comes
  from the exploratory 36-month placebo. Rewritten in both, labelled exploratory, bootstrap interval added (3.3 to 6.3%).
- Abstract now says pageviews are looking up, not remembering; says the women and English-speaking estimates are not
  robust; "stable in 21 checks" became "present in all 21". 246 words.
- The 4,524 articles first seen 2+ months after death were called "mostly renamed titles". Their median first month is
  28 months after death and they are more often women (24.6% vs 15.0%) and non-English-speaking (27.9% English-speaking
  vs 50.0%), so many are probably articles written later. Paper, page and blog now say renamed or written later, cannot
  separate, and that the dropout is not random.
- Blog/page listed "the made-up earlier date" among the 21 checks; it is a separate test. Fixed.
- Speculative sentences softened ("their films and songs keep circulating" now "perhaps ... the data cannot show";
  "this matches" the communicative/cultural memory idea now "loosely echoes", with the looking-up caveat).
- Out-of-sample RMSE printed to 4 decimals (0.0595 had printed as 0.059 against 0.060 in the notes).
- Year-only dates in public copy (blog, page, collage footer, post.md); "random 30%" now "fixed pseudo-random 30%".
- Blog heading and collage panel "Dying young leaves the longest trace" replaced with plainer wording.
- Collage: no-data grey (#E2DCCD) was indistinguishable from the neutral midpoint of the scale (#E5E0D6); now a darker
  grey (#C4C0B8) with its own swatch, same on the page map and the paper/blog map. Age labels coloured to match lines.
- GIF: the N in the subtitle is read from results.json; "1 months after" fixed. Stills checked: final frame clean.

Exploratory checks added (code/04b_review_checks.py, results.json["review"], paper section 6.1):
- Raw-views robustness check is identical to the main model by construction (the enwiki normalisation term depends only
  on the month of death, absorbed by year + calendar-month FE). It and the HC1 check cannot change coefficients, so the
  "21 checks" are really 19 informative ones. Said so in the paper.
- Regression to the mean: control for log attention in k = -24..-13 instead of the baseline window: under 50 +59%
  [46, 74], 90+ -15%; English +14% [11, 18]; women -1.7% [-4.3, 1.0].
- Clustering by citizenship (236 clusters): age intervals still clear of zero; women [-6.2, 0.6].
- 182 main-sample series look like former redirects (baseline under 5 views a month, or no rise at death with LR > 5;
  e.g. LR in the hundreds or thousands). Dropping them: median LR 0.97, under 50 +60%, English +16%, women -1.1%.
- Bootstrap interval for the no-death-path comparison: +4.8% [3.3, 6.3]; person-level median +6.5% [4.6, 8.2].

What a referee would still ask for: page creation and move logs (to separate late-created from renamed articles and to
recover pre-move views under redirects); cause of death or a sudden/expected proxy for the age result; other language
editions; an event-study with matched not-yet-dead controls instead of own-history placebos; a principled multiple
occupations treatment; a pre-registration in the formal sense (the plan here is in the project notes, dated only by the
pipeline).

Outputs regenerated: results.json (+review), figures, index.html, paper PDF/tex, blog post/meta, collage, header,
GIF, README, Zenodo zip. Scratch at /home/claude/scratch/fhl-review deleted at the end.
