"""
Heatmap: share of all tokens removed by each kind of stop word, per language.

Run after evaluate_stopwords.py:  python heatmaps.py   (needs matplotlib)
Writes figures/category_heatmap.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).parent
INK = "#1b1f2a"
BLUE = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
plt.rcParams.update({"font.family": "Helvetica", "text.color": INK, "xtick.color": INK,
                     "ytick.color": INK, "figure.facecolor": "white"})

results = json.loads((HERE / "results/coverage.json").read_text(encoding="utf-8"))
groups = ["Pronouns", "Postpositions", "Verbs and auxiliaries", "Conjunctions", "Other function words"]
M = np.array([[100 * r["tokens_by_group"][g] / r["tokens"] for g in groups] for r in results])

fig, ax = plt.subplots(figsize=(8.5, 3.4))
ax.imshow(M, cmap=BLUE, vmin=0, vmax=M.max(), aspect="auto")
ax.set_xticks(range(len(groups)), ["Pronouns", "Postpositions", "Verbs and\nauxiliaries", "Conjunctions", "Other"])
ax.set_yticks(range(len(results)), [r["language"].title() for r in results])
ax.set_xticks(np.arange(-.5, len(groups), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(results), 1), minor=True)
ax.grid(which="minor", color="white", linewidth=2)
ax.tick_params(which="both", length=0)
for s in ax.spines.values():
    s.set_visible(False)
for i in range(len(results)):
    for j in range(len(groups)):
        ax.text(j, i, f"{M[i, j]:.1f}%", ha="center", va="center", fontsize=10,
                color="white" if M[i, j] > 0.55 * M.max() else INK)
ax.set_title("Share of all tokens removed, by kind of stop word", loc="left", fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(HERE / "figures/category_heatmap.png", dpi=200)
plt.close(fig)
for r, row in zip(results, M):
    print(f'{r["language"]:9}', " ".join(f"{v:5.1f}%" for v in row))
