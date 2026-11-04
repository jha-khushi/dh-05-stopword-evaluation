"""
============================================================
Topic: Evaluating Indic Stop-Word Lists on Real Text
       (extension of Assignment 01)
============================================================
Author Name(s): Khushi Jha
Short Description: Applies the Hindi, Bengali, Gujarati and Tamil
stop-word lists from Assignment 01 to comparable real texts: the
same four Wikipedia articles (India, Rabindranath Tagore, Monsoon,
Ganges) in each language. For each language it measures
  1. coverage: what share of all word tokens the list removes;
  2. which grammatical categories of stop words do that work;
  3. how much of the list is actually used in the texts;
  4. the most frequent words the list does NOT remove, which shows
     what is missing and how joined case endings (agglutination)
     escape a whitespace-based list.
Semester: Monsoon Semester 2026
Affiliation: Department of Humanities and Social Sciences,
Indian Institute of Technology (Indian School of Mines) Dhanbad

Requirements: matplotlib
Run:  python evaluate_stopwords.py
Outputs: results/coverage.json, results/top_words.md, figures/*.png
============================================================
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
# The four lists from Assignment 01 (copied into stopword_lists/ so that this
# repository runs on its own; the originals are in dh-01-indic-stopwords).
STOPWORD_DIR = HERE / "stopword_lists"
TEXTS = HERE / "texts"
RESULTS = HERE / "results"
FIGURES = HERE / "figures"

LANGUAGES = ["hindi", "bengali", "gujarati", "tamil"]
SCRIPTS = {"hindi": "Devanagari", "bengali": "Bengali",
           "gujarati": "Gujarati", "tamil": "Tamil"}

# The comment headings in the stop-word files, folded into five groups.
GROUPS = ["Pronouns", "Postpositions", "Verbs and auxiliaries",
          "Conjunctions", "Other function words"]


def group_of(heading):
    h = heading.lower()
    if "pronoun" in h or "possessive" in h or "demonstrative" in h:
        return "Pronouns"
    if "postposition" in h:
        return "Postpositions"
    if "verb" in h:
        return "Verbs and auxiliaries"
    if "conjunction" in h or "quotative" in h:
        return "Conjunctions"
    return "Other function words"


def load_stopwords(language):
    """Read <language>_stopwords.py and return {word: group} using its comments."""
    source = (STOPWORD_DIR / f"{language}_stopwords.py").read_text(encoding="utf-8")
    body = source[source.index(f"{language}_stopwords = ["):]
    body = body[:body.index("\n]")]
    words, heading = {}, "Other"
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            heading = line.lstrip("# ")
            continue
        for word in re.findall(r'"([^"]+)"', line):
            word = unicodedata.normalize("NFC", word)
            words.setdefault(word, group_of(heading))
    return words


# Letters and vowel signs of the four scripts (Devanagari to Tamil blocks),
# plus zero-width joiners; dandas and Indic digits are excluded below.
INDIC_WORD = re.compile(r"[ऀ-௿‌‍]+")
NOT_LETTERS = re.compile(r"[।॥०-९০-৯૦-૯௦-௯]")


def tokens(language):
    words = []
    for path in sorted(TEXTS.glob(f"{language}_*.txt")):
        text = unicodedata.normalize("NFC", path.read_text(encoding="utf-8"))
        text = NOT_LETTERS.sub(" ", text)
        words += INDIC_WORD.findall(text)
    return words


def evaluate(language):
    stopwords = load_stopwords(language)
    toks = tokens(language)
    counts = Counter(toks)
    stop_tokens = sum(n for w, n in counts.items() if w in stopwords)
    by_group = defaultdict(int)
    for w, n in counts.items():
        if w in stopwords:
            by_group[stopwords[w]] += n
    used = [w for w in stopwords if w in counts]
    top_stop = [(w, n) for w, n in counts.most_common() if w in stopwords][:15]
    top_missed = [(w, n) for w, n in counts.most_common() if w not in stopwords][:15]
    return {
        "language": language,
        "script": SCRIPTS[language],
        "tokens": len(toks),
        "types": len(counts),
        "stopword_tokens": stop_tokens,
        "coverage_percent": round(100 * stop_tokens / len(toks), 1),
        "list_size": len(stopwords),
        "list_words_found": len(used),
        "list_used_percent": round(100 * len(used) / len(stopwords), 1),
        "tokens_by_group": {g: by_group.get(g, 0) for g in GROUPS},
        "top_stopwords": top_stop,
        "top_words_not_in_list": top_missed,
    }


# ---- Charts --------------------------------------------------------------
# Categorical palette (fixed order) and text inks from the dataviz reference.
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
GROUP_COLOURS = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]
CONTENT_GREY = "#d9d8d4"
INK, INK_2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "Helvetica", "text.color": INK,
                     "axes.labelcolor": INK_2, "xtick.color": INK_2,
                     "ytick.color": INK_2, "figure.facecolor": "white"})


def coverage_pies(results):
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.9))
    for ax, r in zip(axes, results):
        stop, rest = r["stopword_tokens"], r["tokens"] - r["stopword_tokens"]
        ax.pie([stop, rest], colors=[BLUE, CONTENT_GREY], startangle=90,
               counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "white",
                                               "linewidth": 2})
        ax.text(0, 0.08, f'{r["coverage_percent"]}%', ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(0, -0.22, "stop words", ha="center", va="center", fontsize=9, color=INK_2)
        ax.set_title(f'{r["language"].title()}\n{r["tokens"]:,} tokens',
                     fontsize=11, color=INK)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BLUE),
                        plt.Rectangle((0, 0), 1, 1, color=CONTENT_GREY)],
               labels=["Removed as stop words", "Kept (content words)"],
               loc="lower center", ncol=2, frameon=False, fontsize=10)
    fig.suptitle("Share of word tokens removed by each stop-word list",
                 fontsize=13, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(FIGURES / "coverage_pies.png", dpi=200)
    plt.close(fig)


def group_pies(results):
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.1))
    for ax, r in zip(axes, results):
        values = [r["tokens_by_group"][g] for g in GROUPS]
        total = sum(values)
        ax.pie(values, colors=GROUP_COLOURS, startangle=90, counterclock=False,
               wedgeprops={"edgecolor": "white", "linewidth": 2},
               autopct=lambda p: f"{p:.0f}%" if p >= 8 else "",
               pctdistance=0.72, textprops={"fontsize": 9, "color": INK})
        ax.set_title(f'{r["language"].title()}\n{total:,} stop-word tokens', fontsize=11)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in GROUP_COLOURS],
               labels=GROUPS, loc="lower center", ncol=5, frameon=False, fontsize=10)
    fig.suptitle("Which kinds of stop words do the work",
                 fontsize=13, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(FIGURES / "category_pies.png", dpi=200)
    plt.close(fig)


def list_use_bars(results):
    fig, ax = plt.subplots(figsize=(8, 3.4))
    names = [r["language"].title() for r in results][::-1]
    found = [r["list_words_found"] for r in results][::-1]
    size = [r["list_size"] for r in results][::-1]
    ax.barh(names, size, color=CONTENT_GREY, height=0.55, label="Words in the list")
    ax.barh(names, found, color=BLUE, height=0.55, label="Found in the texts")
    for y, (f, s) in enumerate(zip(found, size)):
        ax.text(s + 3, y, f"{f} of {s} ({100 * f / s:.0f}%)", va="center",
                fontsize=10, color=INK)
    ax.set_xlim(0, max(size) * 1.32)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c3")
    ax.tick_params(left=False)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.set_title("How much of each list is actually used", loc="left",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "list_usage.png", dpi=200)
    plt.close(fig)


def write_tables(results):
    lines = ["# Most frequent words in each language's texts", "",
             "Stop words the list removed, and the most frequent words it did",
             "not remove. The second list shows what the list misses: content",
             "words (expected), but also case endings joined to nouns and",
             "function words that could be added.", ""]
    for r in results:
        lines += [f"## {r['language'].title()} ({r['script']} script)", "",
                  f"Tokens: {r['tokens']:,} · stop-word coverage: {r['coverage_percent']}%",
                  "", "| Top stop words | Count | Top words not in the list | Count |",
                  "|---|---|---|---|"]
        for i in range(15):
            a = r["top_stopwords"][i] if i < len(r["top_stopwords"]) else ("", "")
            b = r["top_words_not_in_list"][i]
            lines.append(f"| {a[0]} | {a[1]} | {b[0]} | {b[1]} |")
        lines.append("")
    (RESULTS / "top_words.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    results = [evaluate(lang) for lang in LANGUAGES]
    (RESULTS / "coverage.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_tables(results)
    coverage_pies(results)
    group_pies(results)
    list_use_bars(results)
    for r in results:
        print(f'{r["language"]:9} {r["tokens"]:6,} tokens  coverage {r["coverage_percent"]:4}%  '
              f'list used {r["list_words_found"]}/{r["list_size"]}')


if __name__ == "__main__":
    main()
