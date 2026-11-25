"""Too Good To Go: key financial ratios and charts.

Reads the figures in data/, which come from Too Good To Go Holding ApS's
consolidated annual report 2025, computes the ratios used in the analysis
and writes the charts to charts/ and the results to output/metrics.csv.

Run:  python analysis.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
CHARTS = ROOT / "charts"
OUTPUT = ROOT / "output"

# Palette
INK = "#1d1d1f"
MUTED = "#6e6e73"
ACCENT = "#0071e3"
HAIRLINE = "#d2d2d7"
NEGATIVE = "#ae1800"

plt.rcParams.update({
    "font.family": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "text.color": INK,
    "axes.labelcolor": MUTED,
    "axes.edgecolor": HAIRLINE,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "svg.fonttype": "none",
})


def load():
    figures = pd.read_csv(DATA / "key_figures.csv").set_index("year")
    cash = pd.read_csv(DATA / "cash_and_working_capital_2025.csv")
    uk = pd.read_csv(DATA / "unit_economics_uk.csv").set_index("item")["value_gbp"]
    return figures, cash, uk


def ratios(figures):
    df = figures.copy()
    df["gross_margin_pct"] = (df["revenue_meur"] - df["cost_of_sales_meur"]) / df["revenue_meur"] * 100
    df["recurring_ebitda_margin_pct"] = df["recurring_ebitda_meur"] / df["revenue_meur"] * 100
    df["operating_margin_pct"] = df["operating_result_meur"] / df["revenue_meur"] * 100
    df["operating_result_ex_special_meur"] = df["operating_result_meur"] - df["special_items_meur"]
    return df


def growth(df, col, a=2024, b=2025):
    return (df.loc[b, col] / df.loc[a, col] - 1) * 100


def finish(fig, ax, title, subtitle, name):
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=INK, pad=28)
    ax.text(0, 1.04, subtitle, transform=ax.transAxes, fontsize=10, color=MUTED)
    fig.text(0.01, 0.01, "Source: Too Good To Go Holding ApS, Annual report 2025. Own calculations.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(CHARTS / f"{name}.svg")
    plt.close(fig)


def chart_revenue_vs_cost(df):
    d = df.loc[[2024, 2025]]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(d))
    w = 0.36
    ax.bar([i - w / 2 for i in x], d["revenue_meur"], w, color=ACCENT, label="Revenue")
    ax.bar([i + w / 2 for i in x], d["cost_of_sales_meur"], w, color=MUTED, label="Cost of sales")
    for i, (r, c) in enumerate(zip(d["revenue_meur"], d["cost_of_sales_meur"])):
        ax.text(i - w / 2, r + 4, f"{r:.1f}", ha="center", fontsize=10)
        ax.text(i + w / 2, c + 4, f"{c:.1f}", ha="center", fontsize=10)
    ax.set_xticks(list(x), [str(y) for y in d.index])
    ax.set_ylabel("EUR million")
    ax.set_ylim(0, 300)
    ax.legend(frameon=False, loc="upper left", ncol=2)
    finish(fig, ax, "Cost of sales grew faster than revenue",
           f"Revenue +{growth(df, 'revenue_meur'):.1f}%, cost of sales +{growth(df, 'cost_of_sales_meur'):.1f}% (2024 to 2025)",
           "revenue_vs_cost_of_sales")


def chart_margins(df):
    d = df.loc[[2024, 2025]]
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["Gross margin", "Recurring EBITDA margin", "Operating margin"]
    cols = ["gross_margin_pct", "recurring_ebitda_margin_pct", "operating_margin_pct"]
    y = range(len(labels))
    h = 0.36
    for j, (year, color) in enumerate([(2024, HAIRLINE), (2025, ACCENT)]):
        vals = [d.loc[year, c] for c in cols]
        ax.barh([i + (j - 0.5) * h for i in y], vals, h, color=color, label=str(year))
        for i, v in enumerate(vals):
            ax.text(v + (1 if v >= 0 else -1), i + (j - 0.5) * h, f"{v:.1f}%",
                    va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_xlabel("% of revenue")
    ax.set_xlim(-16, 88)
    ax.legend(frameon=False, loc="lower right")
    finish(fig, ax, "More efficient, but thinner gross margin",
           "Recurring EBITDA margin up, gross margin down 6.2 points", "margins_2024_2025")


def chart_operating_bridge(df):
    d = df.loc[2025]
    steps = [("Recurring\nEBITDA", d["recurring_ebitda_meur"]),
             ("Special\nitems", d["special_items_meur"]),
             ("D&A and\nother", d["operating_result_meur"] - d["recurring_ebitda_meur"] - d["special_items_meur"])]
    fig, ax = plt.subplots(figsize=(7, 4))
    running = 0.0
    for i, (label, v) in enumerate(steps):
        color = ACCENT if v >= 0 else NEGATIVE
        ax.bar(i, v, bottom=running, color=color, width=0.55)
        ax.text(i, max(running, running + v) + 0.6, f"{v:+.1f}", ha="center", fontsize=10)
        running += v
    ax.bar(len(steps), running, color=INK, width=0.55)
    ax.text(len(steps), 0.6, f"{running:.1f}", ha="center", fontsize=10)
    ax.set_ylim(-8, 20)
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.set_xticks(range(len(steps) + 1), [s[0] for s in steps] + ["Operating\nresult"])
    ax.set_ylabel("EUR million")
    finish(fig, ax, "Without one-off costs, 2025 would have been profitable",
           f"Operating result {d['operating_result_meur']:.1f} M EUR; excluding special items {d['operating_result_meur'] - d['special_items_meur']:+.1f} M EUR", "operating_bridge_2025")


def main():
    CHARTS.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    figures, cash, uk = load()
    df = ratios(figures)

    c = cash.set_index(["metric", "year"])["value_meur"]
    take_rate = uk["platform_fee_per_bag"] / uk["bag_price"] * 100
    partners_share = c[("payables_to_partners", 2025)] / c[("cash", 2025)] * 100
    wc_share = c[("change_in_working_capital", 2025)] / c[("operating_cash_flow", 2025)] * 100

    df.round(2).to_csv(OUTPUT / "metrics.csv")

    chart_revenue_vs_cost(df)
    chart_margins(df)
    chart_operating_bridge(df)

    print("Key metrics, 2024 vs 2025")
    print(df.loc[[2024, 2025], ["gross_margin_pct", "recurring_ebitda_margin_pct", "operating_margin_pct",
                                "operating_result_ex_special_meur"]].round(1).to_string())
    print(f"\nRevenue growth:            {growth(df, 'revenue_meur'):.1f}%")
    print(f"Cost of sales growth:      {growth(df, 'cost_of_sales_meur'):.1f}%")
    print(f"Recurring EBITDA growth:   {growth(df, 'recurring_ebitda_meur'):.1f}%")
    print(f"Working capital / OCF:     {wc_share:.0f}%")
    print(f"Partner payables / cash:   {partners_share:.0f}%")
    print(f"UK take rate on a GBP 4 bag: {take_rate:.0f}%")


if __name__ == "__main__":
    main()
