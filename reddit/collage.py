"""Reddit collage (reddit/fame_half_life_collage.png, 2700 px wide) and the social card (header.png, 1200 x 630).
Every number comes from data/results.json. Light paper background; labels on paper, never over data."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Polygon as MP
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE = "#B4442E", "#2F6A9E"
plt.rcParams.update({"font.family": SERIF, "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT, "axes.facecolor": PAPER,
                     "figure.facecolor": PAPER, "axes.spines.top": False, "axes.spines.right": False, "axes.unicode_minus": False})
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json"); p = R["prose"]
C = pd.read_csv(f"{DATA}/curves.csv")
A = C[(C.group == "All") & (C.k >= -12) & (C.k <= 36)]


def logy(ax, ticks):
    ax.set_yscale("log"); ax.set_yticks(ticks); ax.set_yticklabels([f"{t:g}x" for t in ticks]); ax.minorticks_off()
    ax.grid(axis="y", color=RULE, lw=0.8); ax.set_axisbelow(True)


fig = plt.figure(figsize=(18, 13.5), dpi=150)
fig.text(0.035, 0.965, "The half-life of fame", fontsize=46, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.035, 0.905, f"Attention to the English Wikipedia articles of {R['n_main']:,} notable people who died 2016 to 2023, against each person's own level in the year before",
         fontsize=17, color=MUT, va="top")
# A: decay
ax = fig.add_axes([0.05, 0.47, 0.42, 0.37])
ax.fill_between(A.k, A.lo, A.hi, color=RED, alpha=0.2, lw=0); ax.plot(A.k, A["median"], color=RED, lw=3)
ax.axhline(1, color=INK, lw=1, ls=(0, (4, 3))); logy(ax, (0.8, 1, 1.5, 2, 3, 5, 10, 15)); ax.set_ylim(0.75, 19); ax.set_xlim(-12, 36)
ax.set_xticks([-12, 0, 12, 24, 36]); ax.tick_params(labelsize=13); ax.set_xlabel("months since death", fontsize=13, color=MUT)
ax.set_title("1  A month of looking up, then back to where they were", fontsize=17, color=INK, loc="left", pad=12)
ax.text(1.5, 13.5, f"month of death: {p['k0']:.1f}x", fontsize=14, color=INK, path_effects=HALO)
ax.text(3, 2.8, f"next month: {p['k1']:.2f}x", fontsize=14, color=INK, path_effects=HALO)
ax.text(13, 1.55, f"two to three years on (average): {R['lr']['median']:.2f}", fontsize=14, color=INK, path_effects=HALO)
ax.text(-11.5, 1.12, "before death", fontsize=12, color=MUT)
# B: age
ax = fig.add_axes([0.55, 0.47, 0.32, 0.37])
ages = ["under 50", "50 to 64", "65 to 79", "80 to 89", "90 and over"]; acol = ["#7F1D22", "#B3202A", "#D3735F", "#E3A58F", "#2F6A9E"]
ly = []
for ag, c in zip(ages, acol):
    g = C[(C.group == "ageb:" + ag) & (C.k >= -6) & (C.k <= 36)]
    ax.plot(g.k, g["median"], color=c, lw=2.6); ly.append(np.log(g["median"].iloc[-1]))
for i in range(1, 5): ly[i] = min(ly[i], ly[i - 1] - 0.2)
tcol = ["#7F1D22", "#B3202A", "#A84A37", "#A86A52", "#2F6A9E"]  # text versions of the line colours, dark enough to read
for ag, yv, c in zip(ages, ly, tcol):
    ax.text(37, np.exp(yv), f"died {ag}: {R['groups']['ageb'][ag]['lr']['median']:.2f}", fontsize=13, va="center", color=c, fontweight="bold")
ax.axhline(1, color=INK, lw=1, ls=(0, (4, 3))); logy(ax, (0.7, 1, 2, 5, 10, 20, 50, 100)); ax.set_ylim(0.6, 130); ax.set_xlim(-6, 36)
ax.set_xticks([0, 12, 24, 36]); ax.tick_params(labelsize=13); ax.set_xlabel("months since death", fontsize=13, color=MUT)
ax.set_title("2  By age at death: the young kept the most", fontsize=17, color=INK, loc="left", pad=12)
# C: occupations
ax = fig.add_axes([0.2, 0.11, 0.27, 0.28])
fams = R["prose"]["fam_lr_order"][::-1]
for i, f in enumerate(fams):
    v = R["groups"]["family"][f]["lr"]
    c = RED if v["lo"] > 1 else BLUE if v["hi"] < 1 else MUT
    ax.plot([v["lo"], v["hi"]], [i, i], color=c, lw=3); ax.scatter([v["median"]], [i], color=c, s=60, zorder=3)
    fig.text(0.19, 0.11 + 0.28 * (i + 0.5) / len(fams), f, ha="right", va="center", fontsize=13.5, color=INK)
ax.axvline(1, color=INK, lw=1); ax.set_yticks([]); ax.set_ylim(-0.5, len(fams) - 0.5); ax.spines["left"].set_visible(False)
ax.tick_params(labelsize=12); ax.set_xlabel("two to three years on (1 = as before; 95% interval)\nred: above 1, blue: below 1, grey: interval includes 1", fontsize=12, color=MUT)
ax.set_title("3  Performers keep it; most do not", fontsize=17, color=INK, loc="left", pad=12, x=-0.55)
# D: map
G = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
CT = pd.read_csv(f"{DATA}/countries.csv").set_index("cit"); ALIAS = {"Q29999": "Q55", "Q756617": "Q35"}
ct = {ALIAS.get(c, c): r for c, r in CT.iterrows()}
TR = Transformer.from_crs(4326, 8857, always_xy=True)
CM = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#E5E0D6", "#E3A58F", RED]); NORM = TwoSlopeNorm(vmin=0.8, vcenter=1.0, vmax=1.2)
ax = fig.add_axes([0.52, 0.1, 0.46, 0.28]); ax.set_facecolor(PAPER)
for ft in G["features"]:
    if ft["properties"]["ADMIN"] == "Antarctica": continue
    r = ct.get(ft["properties"]["WIKIDATAID"]); fc = CM(NORM(r["lr"])) if r is not None else "#C4C0B8"
    gp = stransform(lambda x, y, z=None: TR.transform(x, y), shape(ft["geometry"]))
    for pg in (gp.geoms if gp.geom_type == "MultiPolygon" else [gp]):
        ax.add_patch(MP(np.asarray(pg.exterior.coords), closed=True, fc=fc, ec="#FBF5E4", lw=0.3))
ax.set_xlim(-1.35e7, 1.6e7); ax.set_ylim(-6.3e6, 8.6e6); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for s_ in ax.spines.values(): s_.set_visible(False)
ax.set_title("4  By country of citizenship (30+ people)", fontsize=17, color=INK, loc="left", pad=12)
cax = fig.add_axes([0.53, 0.12, 0.1, 0.012])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=NORM, cmap=CM), cax=cax, orientation="horizontal", ticks=[0.8, 1.0, 1.2]); cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=11); cax.set_title("two to three years on", fontsize=11.5, color=INK, loc="left")
fig.patches.append(plt.Rectangle((0.53, 0.083), 0.012, 0.012, transform=fig.transFigure, fc="#C4C0B8", ec="#9A958C", lw=0.5))
fig.text(0.546, 0.083, "grey: fewer than 30 people", fontsize=11, color=MUT)
fig.text(0.035, 0.016, f"Source: English Wikipedia user pageviews (Wikimedia, CC0), Wikidata (CC0), Natural Earth. Medians across people; 30% hash sample of Wikidata;\ndeaths 2016 to 2023, views 2015 to 2026. Dr Tristan Hotham  ·  maps.tristanhotham.com/fame-half-life",
         fontsize=11.5, family=MONO, color=MUT)
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
fig.savefig(os.path.join(ROOT, "reddit", "fame_half_life_collage.png"), dpi=150, facecolor=PAPER)
plt.close(fig)

# header card
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(0.05, 0.86, "The half-life", fontsize=54, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.05, 0.69, "of fame", fontsize=54, fontweight="bold", family=DISP, color=RED, va="top")
fig.text(0.05, 0.47, f"{R['n_main']:,} notable deaths, 2016 to 2023,\nfollowed on English Wikipedia", fontsize=17, color=INK, va="top", linespacing=1.35)
fig.text(0.05, 0.3, f"Month of death: {p['k0']:.1f}x usual attention\nTwo to three years on: {R['lr']['median']:.2f}", fontsize=15, family=MONO, color=MUT, va="top", linespacing=1.5)
fig.text(0.05, 0.06, "Dr Tristan Hotham · maps.tristanhotham.com/fame-half-life", fontsize=11, family=MONO, color=MUT)
ax = fig.add_axes([0.6, 0.15, 0.36, 0.73])
ax.plot(A.k, A["median"], color=RED, lw=3.5); ax.axhline(1, color=INK, lw=1, ls=(0, (4, 3)))
logy(ax, (1, 2, 5, 10)); ax.set_ylim(0.75, 19); ax.set_xlim(-12, 36); ax.set_xticks([-12, 0, 12, 24, 36]); ax.tick_params(labelsize=12)
ax.set_xlabel("months since death", fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")); assert im.size == (1200, 630), im.size
print("collage and header done", Image.open(os.path.join(ROOT, "reddit", "fame_half_life_collage.png")).size)
