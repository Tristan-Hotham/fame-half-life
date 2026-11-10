"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and the map layer (data/countries.geojson). Light paper background; categorical colours in a fixed order per
occupation family (validated with the dataviz checker: CVD worst adjacent dE 8.7, all lines direct-labelled)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform as stransform
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE, GREY = "#B4442E", "#2F6A9E", "#C9C2B4"
FCOL = {"Performers": "#B3202A", "Sport": "#2F7FB8", "Politics and law": "#D08A1E", "Science and academia": "#3B8B5A", "Writers and artists": "#7A4FA0",
        "Journalism and media": "#C2577F", "Religion": "#2E9C9C", "Business": "#8A6A3B", "Military": "#55606B", "Other": "#9A9283"}
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
C = pd.read_csv(f"{DATA}/curves.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
FOOT = "Data: English Wikipedia user pageviews (Wikimedia, CC0); Wikidata (CC0). maps.tristanhotham.com/fame-half-life"


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.055, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=FOOT):
    fig.text(0.04, 0.015, s, fontsize=8.5, family=MONO, color=MUT)


def logy(ax, ticks=(0.5, 0.7, 1, 1.5, 2, 3, 5, 10, 20)):
    ax.set_yscale("log"); ax.set_yticks(ticks); ax.set_yticklabels([f"{t:g}x" for t in ticks]); ax.minorticks_off()
    ax.grid(axis="y", color=RULE, lw=0.6); ax.set_axisbelow(True)


A = C[C.group == "All"]
pr = R["prose"]
# ---------- 1. the decay curve
fig = plt.figure(figsize=(11, 7.2))
title(fig, "A month of mourning, then back to where they were",
      f"Median attention to a person's English Wikipedia article by months since their death, against their own level before it ({R['n_main']:,} people)")
ax = fig.add_axes([0.08, 0.11, 0.88, 0.72])
a = A[(A.k >= -12) & (A.k <= 60)]
ax.fill_between(a.k, a.lo, a.hi, color=RED, alpha=0.18, lw=0)
ax.plot(a.k, a["median"], color=RED, lw=2.2)
ax.axhline(1, color=INK, lw=0.8, ls=(0, (4, 3)))
ax.axvline(0, color=MUT, lw=0.6)
logy(ax, (0.7, 1, 1.5, 2, 3, 5, 10, 15))
ax.set_xlim(-12, 60); ax.set_ylim(0.75, 19)
ax.set_xlabel("Months since the month of death"); ax.set_ylabel("Share of Wikipedia attention, relative to the year before")
ax.annotate(f"Month of death: {pr['k0']:.1f} times\nthe usual level (median)", (0, pr["k0"]), (5, 12), fontsize=11.5, color=INK, path_effects=HALO,
            arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
ax.annotate(f"Next month: {pr['k1']:.1f}x", (1, pr["k1"]), (6, 4.2), fontsize=11.5, color=INK, path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
ax.annotate(f"A year on: {pr['k12']:.2f}x", (12, pr["k12"]), (14, 1.75), fontsize=11.5, color=INK, path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
ax.annotate(f"Two to three years on: {R['lr']['median']:.2f} of the\npre-death level (11-month average)", (30, pr["k34"]), (31, 1.45), fontsize=11.5, color=INK,
            path_effects=HALO, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
ax.text(-11.5, 1.12, "before death: single months sit just\nunder 1 because months vary", fontsize=10, color=MUT)
ax.text(59.5, 1.03, "pre-death level", fontsize=10, color=MUT, ha="right")
ax.text(59.5, 0.78, "after month 34: deaths 2016 to 2021 only", fontsize=9.5, color=MUT, ha="right")
foot(fig)
out(fig, "decay")

# ---------- 2. model fits (log-log)
fig = plt.figure(figsize=(11, 6.6))
title(fig, "Two speeds of forgetting", "Median curve for months 1 to 60 after death, and the three decay models fitted to it (least squares on the log scale)")
ax = fig.add_axes([0.08, 0.12, 0.56, 0.7])
k = A[(A.k >= 1) & (A.k <= 60)]
ax.scatter(k.k, k["median"], s=26, color=INK, zorder=3, label="median, all people")
S = jload(f"{DATA}/site.json")
cols = {"exponential": "#2F7FB8", "power law": "#D08A1E", "two-phase": "#B3202A"}
for nm, f in S["fits"].items():
    ax.plot(f["k"], f["y"], color=cols[nm], lw=2, label=f"{nm}")
ax.set_xscale("log"); logy(ax, (0.8, 0.9, 1, 1.2, 1.5, 2, 3))
ax.set_xticks([1, 2, 3, 6, 12, 24, 48]); ax.set_xticklabels(["1", "2", "3", "6", "12", "24", "48"])
ax.set_xlabel("Months since death (log scale)"); ax.set_ylabel("Relative attention")
lg = ax.legend(frameon=False, loc="upper right", fontsize=11)
fx = R["fits"]; tp = R["two_phase"]
txt = (f"Fit (AIC, lower is better)\n"
       f"  two-phase    {fx['two-phase']['aic']:.0f}\n  power law    {fx['power law']['aic']:.0f}\n  exponential  {fx['exponential']['aic']:.0f}\n\n"
       f"Out of sample (fit 2016 to 2019,\npredict 2020 to 2023, log RMSE)\n"
       f"  power law    {fx['power law']['oos_rmse']:.3f}\n  two-phase    {fx['two-phase']['oos_rmse']:.3f}\n  exponential  {fx['exponential']['oos_rmse']:.3f}\n\n"
       f"Two-phase model\n  fast half-life {pr['hl_fast_days']} days\n  slow half-life {pr['hl_slow']:.1f} months\n  settles at {tp['c']:.2f}")
fig.text(0.68, 0.8, txt, fontsize=11, family=MONO, color=INK, va="top")
foot(fig)
out(fig, "fits")

# ---------- 3. families: small multiples
fams = [f for f in pr["fam_lr_order"]]
fig = plt.figure(figsize=(12, 8.6))
title(fig, "Who keeps the attention", "Median relative attention by months since death, by occupation family (grey line: everyone)")
for i, f in enumerate(fams):
    ax = fig.add_axes([0.06 + (i % 5) * 0.188, 0.5 - (i // 5) * 0.4, 0.165, 0.3])
    g = C[(C.group == "family:" + f) & (C.k >= -6) & (C.k <= 36)]
    ax.plot(a[(a.k >= -6) & (a.k <= 36)].k, a[(a.k >= -6) & (a.k <= 36)]["median"], color=GREY, lw=1.6)
    ax.fill_between(g.k, g.lo, g.hi, color=FCOL[f], alpha=0.2, lw=0)
    ax.plot(g.k, g["median"], color=FCOL[f], lw=2)
    ax.axhline(1, color=INK, lw=0.6, ls=(0, (4, 3)))
    logy(ax, (0.7, 1, 2, 5, 10, 20)); ax.set_ylim(0.6, 30); ax.set_xlim(-6, 36); ax.set_xticks([0, 12, 24, 36])
    if i % 5: ax.set_yticklabels([])
    v = R["groups"]["family"][f]
    ax.set_title(f"{f}\n\n", fontsize=11.5, color=INK, loc="left")
    ax.text(0, 1.04, f"N {v['n']:,} · peak {v['peak']['median']:.0f}x\n2 to 3 years on {v['lr']['median']:.2f}", transform=ax.transAxes, fontsize=8.8, family=MONO, color=MUT)
    if i // 5: ax.set_xlabel("months since death", fontsize=10)
foot(fig)
out(fig, "families")

# ---------- 4. effects (regression)
H = R["H4"]
rows = [("Died under 50", "age_u50"), ("Died 50 to 64", "age_50"), ("Died 80 to 89", "age_80"), ("Died 90 or over", "age_90"),
        ("Women (vs men)", "women"), ("English-speaking citizenship", "english")] + [(f + " (vs performers)", "fam_" + f) for f in FAMILIES[1:]]
fig = plt.figure(figsize=(11, 8.4))
title(fig, "What goes with lasting attention", "Percentage difference in attention two to three years after death (left) and in the peak (right), same model, 95% intervals")
for j, (key, lab) in enumerate((("lr", "Two to three years on"), ("peak", "Peak (month of death or next)"))):
    ax = fig.add_axes([0.33 + j * 0.34, 0.15, 0.3, 0.69])
    for i, (nm, kk) in enumerate(rows):
        e = H[key][kk]; y = len(rows) - i
        c = RED if e["lo"] > 0 else BLUE if e["hi"] < 0 else MUT
        ax.plot([1 + e["lo"] / 100, 1 + e["hi"] / 100], [y, y], color=c, lw=2); ax.scatter([1 + e["b"] / 100], [y], color=c, s=30, zorder=3)
        if j == 0:
            fig.text(0.31, 0.15 + 0.69 * (y - 0.5) / len(rows), nm, ha="right", va="center", fontsize=11, color=INK)
    ax.axvline(1, color=INK, lw=0.8); ax.set_yticks([]); ax.set_ylim(0.3, len(rows) + 0.7)
    ax.set_xscale("log"); tk = [0.5, 0.75, 1, 1.5, 2, 3, 5] if key == "peak" else [0.6, 0.8, 1, 1.25, 1.5, 2]
    ax.set_xticks(tk); ax.set_xticklabels([f"{100 * (t - 1):+.0f}%" if t != 1 else "0" for t in tk], fontsize=9); ax.minorticks_off()
    ax.set_title(lab, fontsize=12, color=INK, loc="left")
    ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True); ax.spines["left"].set_visible(False)
fig.text(0.04, 0.04, f"OLS on the log ratio, N = {R['n_main']:,}, also controlling for log sitelinks, log attention before death, year and calendar month of death; errors clustered\nby month of death. Reference: performers, men, aged 65 to 79. Red: higher, blue: lower, grey: interval includes zero. Log scale.", fontsize=9, color=MUT)
foot(fig)
out(fig, "effects")

# ---------- 5. age
ages = ["under 50", "50 to 64", "65 to 79", "80 to 89", "90 and over"]
acol = ["#7F1D22", "#B3202A", "#D3735F", "#E3A58F", "#EDCBB9"]
fig = plt.figure(figsize=(11, 6.8))
title(fig, "Dying young leaves the longest trace", "Median relative attention by months since death, by age at death")
ax = fig.add_axes([0.08, 0.11, 0.62, 0.71])
ly = []
for ag, c in zip(ages, acol):
    g = C[(C.group == "ageb:" + ag) & (C.k >= -6) & (C.k <= 36)]
    ax.plot(g.k, g["median"], color=c, lw=2.2)
    ly.append(np.log(g["median"].iloc[-1]))
ly = np.array(ly); 
for i in range(1, 5):          # spread labels: at least 0.09 apart in log space, going down
    ly[i] = min(ly[i], ly[i - 1] - 0.17)
for (ag, c), yv in zip(zip(ages, acol), ly):
    v = R["groups"]["ageb"][ag]
    ax.text(36.5, np.exp(yv), f"{ag}: {v['lr']['median']:.2f}", fontsize=10.5, va="center", color=INK, path_effects=HALO)
ax.text(36.5, np.exp(ly[0]) * 1.25, "2 to 3 years on", fontsize=10, color=MUT)
ax.axhline(1, color=INK, lw=0.7, ls=(0, (4, 3)))
logy(ax, (0.7, 1, 1.5, 2, 5, 10, 20, 50, 100)); ax.set_xlim(-6, 36); ax.set_ylim(0.65, 120)
ax.set_xlabel("Months since death"); ax.set_ylabel("Relative attention")
ax2 = fig.add_axes([0.5, 0.5, 0.15, 0.27]); ax2.set_facecolor(PAPER)
pk = [R["groups"]["ageb"][a_]["peak"]["median"] for a_ in ages]
ax2.barh(range(5)[::-1], pk, color=acol, height=0.7)
for i, v in enumerate(pk):
    ax2.text(v + 2, 4 - i, f"{v:.0f}x", va="center", fontsize=10, family=MONO, color=INK)
ax2.set_yticks(range(5)[::-1]); ax2.set_yticklabels(ages, fontsize=9.5); ax2.set_xticks([]); ax2.spines["bottom"].set_visible(False)
ax2.set_title("Median peak", fontsize=11, loc="left", color=INK)
foot(fig)
out(fig, "age")

# ---------- 6. placebo: real death vs a fake death 24 months earlier
Sx = pd.read_csv(f"{DATA}/people.csv")
Zx = np.load(f"{SCR}/event.npz", allow_pickle=True)
X, K = Zx["X"].astype(float), Zx["K"]
P = pd.read_csv(f"{SCR}/people.csv")
col = {int(k_): j for j, k_ in enumerate(K)}
w = ((P.main == 1) & (P.pl_ok == 1)).values
real = X[w] / P.base.values[w][:, None]; fake = X[w] / P.pl_base.values[w][:, None]
kr = np.arange(-12, 13)
mr = [np.nanmedian(real[:, col[k_]]) for k_ in kr]; mf = [np.nanmedian(fake[:, col[k_ - 24]]) for k_ in kr]
fig = plt.figure(figsize=(11, 6.4))
title(fig, "The spike is the death, not the season", f"Same {int(w.sum()):,} people: around the real death, and around a made-up date two years earlier")
ax = fig.add_axes([0.08, 0.12, 0.86, 0.7])
ax.plot(kr, mr, color=RED, lw=2.2); ax.plot(kr, mf, color=BLUE, lw=2.2, ls=(0, (5, 2)))
ax.text(1.5, mr[13], "real date of death", color=INK, fontsize=11.5, path_effects=HALO)
ax.text(2, 0.8, f"placebo date two years earlier: a year on, {R['placebo']['y1']['median']:.2f}x", color=INK, fontsize=11.5, path_effects=HALO)
ax.axhline(1, color=INK, lw=0.7, ls=(0, (4, 3))); logy(ax, (0.7, 1, 1.5, 2, 5, 10, 15)); ax.set_ylim(0.7, 19)
ax.set_xlabel("Months since the (real or placebo) date"); ax.set_ylabel("Relative attention")
foot(fig)
out(fig, "placebo")

# ---------- 7. world map of median long-run ratio by citizenship + geojson for the page
G = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
CT = pd.read_csv(f"{DATA}/countries.csv").set_index("cit")
ALIAS = {"Q29999": "Q55", "Q756617": "Q35"}   # Kingdom of the Netherlands, Kingdom of Denmark
ct = {ALIAS.get(c, c): r for c, r in CT.iterrows()}
TR = Transformer.from_crs(4326, 8857, always_xy=True)
CM = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#E5E0D6", "#E3A58F", RED])
NORM = TwoSlopeNorm(vmin=0.8, vcenter=1.0, vmax=1.2)
fig = plt.figure(figsize=(12, 7.0))
title(fig, "Where fame lasts", "Median attention two to three years after death against before it, by country of citizenship (30 or more people)")
ax = fig.add_axes([0.01, 0.08, 0.98, 0.78]); ax.set_facecolor(PAPER)
from matplotlib.patches import Polygon as MP
feats = []
for f in G["features"]:
    pz = f["properties"]; q = pz["WIKIDATAID"]
    g = shape(f["geometry"])
    if pz["ADMIN"] == "Antarctica": continue
    r = ct.get(q)
    fc = CM(NORM(r["lr"])) if r is not None else "#C4C0B8"
    gp = stransform(lambda x, y, z=None: TR.transform(x, y), g)
    for p in (gp.geoms if gp.geom_type == "MultiPolygon" else [gp]):
        ax.add_patch(MP(np.asarray(p.exterior.coords), closed=True, fc=fc, ec="#FBF5E4", lw=0.3))
    gs = g.simplify(0.08, preserve_topology=True)
    prop = {"name": pz["NAME"], "q": q}
    if r is not None:
        prop.update({"lab": r["name"], "n": int(r["n"]), "lr": r["lr"], "lo": r["lr_lo"], "hi": r["lr_hi"], "pk": r["peak"], "y1": r["y1"],
                     "ab": r["lr_above1_pc"], "wo": r["women_pc"], "tf": r["top_family"]})
    gj = mapping(gs)
    def rnd(o):
        return [rnd(x) for x in o] if isinstance(o, (list, tuple)) and o and isinstance(o[0], (list, tuple)) else [round(o[0], 2), round(o[1], 2)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "properties": prop, "geometry": gj})
ax.set_xlim(-1.35e7, 1.6e7); ax.set_ylim(-6.3e6, 8.6e6); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for s_ in ax.spines.values(): s_.set_visible(False)
cax = fig.add_axes([0.035, 0.36, 0.13, 0.022])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CM), cax=cax, orientation="horizontal", ticks=[0.8, 0.9, 1.0, 1.1, 1.2])
cb.ax.set_xticklabels(["0.8", "0.9", "1.0", "1.1", "1.2"], fontsize=9); cb.outline.set_visible(False)
cax.set_title("below 1: less than before\ndeath; above 1: more", fontsize=9.5, color=INK, loc="left")
fig.text(0.035, 0.2, "Grey: fewer than 30 people.\nHistoric states (Soviet Union,\nBritish Raj, Empire of Japan,\nYugoslavia and others) are in\nthe data but not on this map.", fontsize=9, color=MUT)
foot(fig)
out(fig, "map")
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/countries.geojson")
print("figures done; geojson", os.path.getsize(f"{DATA}/countries.geojson") // 1024, "KB")
