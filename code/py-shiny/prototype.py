# prototype.py: rebuild the dashboard outputs for one fixed filter.
#
# The dashboard will show three parts of this project for any choice of
# countries and years:
#   1. bloc charts (from code/python/01_bloc_trade.py, 02_bloc_trend.py,
#      03_bloc_heatmap.py)
#   2. PPML gravity model (from code/r/01_gravity.R), here with pyfixest
#   3. subsidy path model (from code/stata/03_sem.do), here as two OLS regressions
#
# This script tries the outputs on one filter before any dashboard exists.
# The dashboard (code/py-shiny/app.py) imports the functions below.
#
# Run from the project root:
#   python code/py-shiny/prototype.py          EU and Mercosur, 2010-2019
#   python code/py-shiny/prototype.py --all    all countries, 2000-2019, and
#                                              a check against outputs/data/
#   python code/py-shiny/prototype.py --mockup trade vs distance mockup
# Output: outputs/prototype/<filter>/  figures (PNG) and tables (CSV).
# These files are only for checking; they are not committed.
#
# Packages: pandas, matplotlib, statsmodels, pyfixest (approved by the user).

import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Project root = two folders above this one (code/py-shiny/). Paths work from
# any folder. A deployed copy has data/clean/ next to this file instead, so
# look there too.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] if (HERE.parents[1] / "data/clean/farm_trade.csv").exists() else HERE
if not (ROOT / "data/clean/farm_trade.csv").exists():
    sys.exit("Cannot find data/clean/ next to this folder or inside it.")

BLOCS = ["ASEAN", "East Asia", "EU", "Mercosur", "Oceania", "USMCA"]
# One fixed colour per bloc, so a bloc has the same colour in every chart
BLOC_COLOURS = dict(zip(BLOCS, plt.get_cmap("tab10").colors))

TERMS = ["log(dist_km)", "contig", "comlang", "rta"]
TERM_LABELS = {
    "log(dist_km)": "Log distance",
    "contig": "Shared border",
    "comlang": "Common language",
    "rta": "Trade agreement",
}


# ---- Data ------------------------------------------------------------------

def load_data():
    """Read the clean data. Returns trade, support and countries."""
    trade = pd.read_csv(ROOT / "data/clean/farm_trade.csv")
    support = pd.read_csv(ROOT / "data/clean/farm_support.csv")
    countries = pd.read_csv(ROOT / "data/clean/countries.csv")
    return trade, support, countries


def filter_data(trade, support, isos, years):
    """Keep the chosen countries and years.
    Trade keeps a flow only if both exporter and importer are chosen."""
    first, last = years
    t = trade[
        trade["exporter"].isin(isos)
        & trade["importer"].isin(isos)
        & trade["year"].between(first, last)
    ]
    s = support[support["iso3"].isin(isos) & support["year"].between(first, last)]
    return t, s


def describe_filter(isos, countries, years):
    """Short text for chart titles, for example 'EU, Mercosur, 2010-2019'."""
    blocs = countries.set_index("iso3").loc[list(isos), "bloc"]
    whole = [b for b in BLOCS
             if b in set(blocs) and (countries["bloc"] == b).sum() == (blocs == b).sum()]
    if len(isos) == len(countries):
        who = f"all {len(countries)} countries"
    elif len(whole) == blocs.nunique():
        who = ", ".join(whole)
    elif len(isos) == 1:
        who = "1 selected country"
    else:
        who = f"{len(isos)} selected countries"
    span = str(years[0]) if years[0] == years[1] else f"{years[0]}-{years[1]}"
    return f"{who}, {span}"


def bloc_note(isos, countries, years):
    """Title text for the bloc charts. Under a country filter the bloc totals
    cover only the chosen countries, so the title says so."""
    note = describe_filter(isos, countries, years)
    if len(isos) < len(countries):
        note += "\n(bloc totals for the selected countries only)"
    return note


# ---- Part 1: bloc charts -----------------------------------------------------

def bloc_trade(trade_f, countries):
    """Add up trade for each year and pair of blocs (as 01_bloc_trade.py)."""
    bloc_of = countries.set_index("iso3")["bloc"]
    t = trade_f.assign(bloc_from=trade_f["exporter"].map(bloc_of),
                       bloc_to=trade_f["importer"].map(bloc_of))
    return (t.groupby(["year", "bloc_from", "bloc_to"], as_index=False)["trade_usd"]
            .sum()
            .sort_values(["year", "bloc_from", "bloc_to"]))


def year_ticks(first, last):
    """Three or four year ticks that always include the first and last year."""
    step = max(1, (last - first) // 2)
    ticks = list(range(first, last + 1, step))
    if ticks[-1] != last:
        if last - ticks[-1] < step / 2:
            ticks[-1] = last  # too close to the previous tick: replace it
        else:
            ticks.append(last)
    return ticks


def plot_trend(bt, title_note):
    """One panel per exporting bloc, one line per importing bloc, USD billions."""
    exporters = [b for b in BLOCS if b in set(bt["bloc_from"])]
    ncol = min(3, len(exporters))
    nrow = int(np.ceil(len(exporters) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow + 0.8),
                             sharex=True, squeeze=False)
    first, last = bt["year"].min(), bt["year"].max()
    for ax, b in zip(axes.flat, exporters):
        rows = bt[bt["bloc_from"] == b]
        for to, r in rows.groupby("bloc_to"):
            ax.plot(r["year"], r["trade_usd"] / 1e9, color=BLOC_COLOURS[to], lw=2,
                    marker="o" if first == last else None)  # one year: show a dot
        ax.set_title(f"From {b}")
        ax.set_ylim(bottom=0)
        ax.set_xticks(year_ticks(first, last))
        ax.set_xlim(first, last)
    for ax in list(axes.flat)[len(exporters):]:
        ax.set_visible(False)
    fig.supylabel("USD billions")
    # One legend for the whole figure, right of the panels, so it hides no line
    labels = [b for b in BLOCS if b in set(bt["bloc_to"])]
    handles = [plt.Line2D([], [], color=BLOC_COLOURS[b], lw=2) for b in labels]
    fig.legend(handles, labels, title="Importing bloc", loc="center right", frameon=False)
    fig.set_layout_engine("tight", rect=(0, 0, 0.82, 1))  # room for the legend
    fig.suptitle(f"Farm exports by bloc, {title_note}")
    return fig


def plot_heatmap(bt, title_note):
    """Exporting bloc in rows, importing bloc in columns, last year of the filter."""
    year = bt["year"].max()
    table = (bt[bt["year"] == year]
             .pivot(index="bloc_from", columns="bloc_to", values="trade_usd")
             .fillna(0) / 1e9)
    # Same bloc order as the trend chart
    table = table.reindex(index=[b for b in BLOCS if b in table.index],
                          columns=[b for b in BLOCS if b in table.columns])
    fig, ax = plt.subplots(figsize=(7, 5.5), layout="tight")
    # Colour on a log scale, so one large cell does not wash out the others.
    # Cells with no trade stay white. The numbers in the cells are USD billions.
    values = table.values
    shown = np.ma.masked_less_equal(values, 0)  # log of 0: leave the cell blank
    one_value = shown.count() == 0 or shown.min() == shown.max()
    norm = None if one_value else LogNorm(vmin=shown.min(), vmax=shown.max())
    image = ax.imshow(shown, cmap="Blues", norm=norm)
    ax.set_xticks(range(len(table.columns)), labels=table.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(table.index)), labels=table.index)
    ax.set_xlabel("Importing bloc")
    ax.set_ylabel("Exporting bloc")
    # White text on the darker half of the log colour range
    threshold = np.sqrt(shown.min() * shown.max()) if shown.count() else np.inf
    for i in range(len(table.index)):
        for j in range(len(table.columns)):
            value = values[i, j]
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize="small",
                    color="white" if value > threshold else "black")
    if not one_value:
        fig.colorbar(image, ax=ax, label="Farm trade (USD billions, log scale)")
    fig.suptitle(f"Farm trade between blocs, {year}, USD billions\n"
                 f"{title_note}")
    return fig


# ---- Part 2: gravity model ---------------------------------------------------

def gravity(trade_f):
    """PPML gravity model, same as code/r/01_gravity.R (fixest::fepois):
    exporter-year and importer-year fixed effects, errors clustered by pair.
    Returns one row per regressor."""
    import pyfixest as pf  # slow first import (about 20 s); later calls are fast

    d = trade_f.assign(
        log_dist=np.log(trade_f["dist_km"]),
        pair=trade_f["exporter"] + "_" + trade_f["importer"],
        ex_year=trade_f["exporter"] + "_" + trade_f["year"].astype(str),
        im_year=trade_f["importer"] + "_" + trade_f["year"].astype(str),
    )
    m = pf.fepois(
        "trade_usd ~ log_dist + contig + comlang + rta | ex_year + im_year",
        data=d,
        vcov={"CRV1": "pair"},
    )
    t = m.tidy()
    return pd.DataFrame({
        "term": t.index.str.replace("log_dist", "log(dist_km)"),
        "estimate": t["Estimate"].to_numpy(),
        "std_error": t["Std. Error"].to_numpy(),
        "p_value": t["Pr(>|t|)"].to_numpy(),
    })


def gravity_safe(trade_f, n_countries, min_countries=6):
    """Return (table, None) if the model runs, or (None, message) if not.
    The country check comes first: pyfixest 0.60 crashes the whole Python
    process on 2 countries or fewer, and try/except cannot catch that.
    n_countries is the number of selected countries, not those left in trade_f."""
    n_cty = n_countries
    if n_cty < min_countries:
        return None, (f"Gravity model needs at least {min_countries} countries; "
                      f"the filter keeps {n_cty}. Add countries.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # pyfixest warns when it drops a regressor
            out = gravity(trade_f)
    except ValueError:  # "All variables are collinear"
        out = pd.DataFrame({"term": [], "std_error": []})
    missing = [v for v in TERMS if v not in set(out["term"])]
    if missing:
        names = ", ".join(TERM_LABELS[v].lower() for v in missing)
        return None, (f"Gravity model cannot estimate {names}: it does not vary "
                      "enough across country pairs in this filter. "
                      "Add countries from another bloc.")
    if not (np.isfinite(out["std_error"]).all() and (out["std_error"] < 10).all()):
        return None, "Gravity estimates are unstable for this filter. Add countries."
    return out, None


def gravity_table(coefs):
    """Readable version of the gravity table: labels, rounding, p < 0.001."""
    return pd.DataFrame({
        "Regressor": coefs["term"].map(TERM_LABELS),
        "Estimate": [f"{v:.3f}" for v in coefs["estimate"]],
        "Std. error": [f"{v:.3f}" for v in coefs["std_error"]],
        "p-value": [("< 0.001" if p < 0.001 else f"{p:.3f}") for p in coefs["p_value"]],
    })


def plot_gravity(coefs, title_note):
    """Gravity coefficients with 95% confidence intervals (as 02_coef_plot.R)."""
    c = coefs.set_index("term").loc[TERMS]
    lower = c["estimate"] - 1.96 * c["std_error"]
    upper = c["estimate"] + 1.96 * c["std_error"]
    y = np.arange(len(c))[::-1]  # first regressor on top
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.hlines(y, lower, upper, color="#1f4e79", lw=2)
    ax.plot(c["estimate"], y, "o", color="#1f4e79")
    ax.axvline(0, color="grey", ls="--", lw=1)
    ax.set_yticks(y, labels=[TERM_LABELS[t] for t in TERMS])
    ax.set_xlabel("PPML coefficient (95% CI, clustered by country pair)")
    ax.set_title(f"Gravity model of farm trade, {title_note}")
    fig.text(0.01, 0.01, "Associations, not causal effects.", fontsize="small", color="grey")
    fig.set_layout_engine("tight", rect=(0, 0.05, 1, 1))  # room for the note
    return fig


def plot_trade_distance(trade_f, coefs, countries, title_note):
    """Scatter of trade against distance, one point per country pair (mean over
    the years of the filter), log scales. The line has the slope of the PPML
    distance coefficient. If the gravity model did not run, coefs is None and
    the chart shows the points only."""
    bloc_of = countries.set_index("iso3")["bloc"]
    pairs = (trade_f.groupby(["exporter", "importer"], as_index=False)
             .agg(trade_usd=("trade_usd", "mean"), dist_km=("dist_km", "first")))
    pairs = pairs[pairs["trade_usd"] > 0]  # log scale: drop pairs that never trade
    same = pairs["exporter"].map(bloc_of) == pairs["importer"].map(bloc_of)
    y = pairs["trade_usd"] / 1e6  # USD millions

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(pairs.loc[~same, "dist_km"], y[~same], s=12, alpha=0.5,
               color="#7f7f7f", label="Pair in different blocs")
    ax.scatter(pairs.loc[same, "dist_km"], y[same], s=16, alpha=0.8,
               color="#d62728", label="Pair in the same bloc")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Distance between the two countries (km, log scale)")
    ax.set_ylabel("Farm exports, mean per year (USD millions, log scale)")

    if coefs is not None:
        # Slope = PPML distance coefficient. The line goes through the centre of
        # the points; it leaves out the other regressors and the fixed effects.
        slope = coefs.set_index("term").loc["log(dist_km)", "estimate"]
        lx, ly = np.log(pairs["dist_km"]), np.log(y)
        intercept = ly.mean() - slope * lx.mean()
        xs = np.linspace(lx.min(), lx.max(), 50)
        ax.plot(np.exp(xs), np.exp(intercept + slope * xs), color="#1f4e79", lw=2,
                label=f"Gravity model: distance elasticity {slope:.2f}")
        note = ("Line: slope from the PPML gravity model, drawn through the centre of "
                "the points. Associations, not causal effects.")
    else:
        note = "No fitted line: the gravity model cannot run for this filter."
    ax.legend(frameon=False, loc="lower left")
    ax.set_title(f"Farm trade and distance, {title_note}\n"
                 f"{len(pairs)} country pairs with trade")
    fig.text(0.01, 0.01, note, fontsize="small", color="grey")
    fig.set_layout_engine("tight", rect=(0, 0.05, 1, 1))  # room for the note
    return fig


# ---- Part 3: subsidy path model ---------------------------------------------

def sem_effects(support_f):
    """Recursive path model of code/stata/03_sem.do as two OLS regressions.
    Same point estimates as Stata sem. Standard error for the direct path only;
    the indirect effect needs a delta method or bootstrap."""
    d = support_f.assign(ln_subsidy=np.log(support_f["subsidy"]),
                         ln_fert=np.log(support_f["fertiliser"]),
                         ln_output=np.log(support_f["farm_output"]))
    m1 = smf.ols("ln_fert ~ ln_subsidy", data=d).fit()              # subsidy -> fertiliser
    m2 = smf.ols("ln_output ~ ln_subsidy + ln_fert", data=d).fit()  # direct paths
    a, b, c = m1.params["ln_subsidy"], m2.params["ln_fert"], m2.params["ln_subsidy"]
    return pd.DataFrame({
        "effect": ["direct", "indirect", "total"],
        "estimate": [c, a * b, c + a * b],
        "std_error": [m2.bse["ln_subsidy"], np.nan, np.nan],
    })


def sem_safe(support_f, min_rows=20):
    """Return (table, None) if the path model runs, or (None, message) if not."""
    if len(support_f) < min_rows:
        return None, (f"Path model needs at least {min_rows} country-years; the filter "
                      f"keeps {len(support_f)}. Add countries or years.")
    return sem_effects(support_f), None


# ---- Run the prototype -------------------------------------------------------

def run(isos, years, out_dir):
    """Make every output for one filter and save it in out_dir."""
    trade, support, countries = load_data()
    trade_f, support_f = filter_data(trade, support, isos, years)
    note = describe_filter(isos, countries, years)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Filter: {note}. Trade rows: {len(trade_f)}; support rows: {len(support_f)}")

    # Part 1: bloc charts
    bt = bloc_trade(trade_f, countries)
    bt.to_csv(out_dir / "bloc_trade.csv", index=False, lineterminator="\n")
    bnote = bloc_note(isos, countries, years)
    for name, fig in [("bloc_trend.png", plot_trend(bt, bnote)),
                      ("bloc_heatmap.png", plot_heatmap(bt, bnote))]:
        fig.savefig(out_dir / name, dpi=150)
        plt.close(fig)

    # Part 2: gravity model. The guard runs before any fit.
    print("Gravity model (the first run takes about 20 seconds) ...")
    coefs, msg = gravity_safe(trade_f, len(isos))
    if msg:
        print("GRAVITY MODEL NOT RUN:", msg)
        (out_dir / "gravity_message.txt").write_text(msg + "\n")
    else:
        coefs.to_csv(out_dir / "gravity_coefs.csv", index=False, lineterminator="\n")
        print(gravity_table(coefs).to_string(index=False))
        fig = plot_gravity(coefs, note)
        fig.savefig(out_dir / "gravity_coefs.png", dpi=150)
        plt.close(fig)

    # Part 3: path model (synthetic data)
    effects, msg = sem_safe(support_f)
    if msg:
        print("PATH MODEL NOT RUN:", msg)
        (out_dir / "sem_message.txt").write_text(msg + "\n")
    else:
        effects.to_csv(out_dir / "sem_effects.csv", index=False, lineterminator="\n")
        print("Path model (synthetic data):")
        print(effects.round(6).to_string(index=False))

    print(f"Saved to {out_dir.relative_to(ROOT)}")
    return bt, coefs, effects


def compare_with_reference(bt, coefs, effects):
    """Full sample only: compare with the shipped tidy files in outputs/data/."""
    ref_bt = pd.read_csv(ROOT / "outputs/data/bloc_trade.csv")
    m = ref_bt.merge(bt, on=["year", "bloc_from", "bloc_to"])
    print(f"\nBloc trade: {len(m)} of {len(ref_bt)} rows matched; "
          f"max abs diff {np.abs(m['trade_usd_x'] - m['trade_usd_y']).max():.0f} USD")

    ref_g = pd.read_csv(ROOT / "outputs/data/gravity_coefs.csv")
    g = ref_g.merge(coefs, on="term", suffixes=("_ref", "_py"))
    print("Gravity, max abs diff: estimate "
          f"{np.abs(g['estimate_ref'] - g['estimate_py']).max():.1e}, std_error "
          f"{np.abs(g['std_error_ref'] - g['std_error_py']).max():.1e}")

    ref_s = pd.read_csv(ROOT / "outputs/data/sem_effects.csv")
    ref_s = ref_s[ref_s["path"] == "subsidy -> output"]
    s = ref_s.merge(effects, on="effect", suffixes=("_stata", "_py"))
    print("Path model, subsidy -> output:")
    print(s[["effect", "estimate_stata", "estimate_py", "std_error_stata", "std_error_py"]]
          .round(6).to_string(index=False))


if __name__ == "__main__":
    trade, support, countries = load_data()
    if "--mockup" in sys.argv:
        # Step 4 mockup: trade against distance, all countries, 2000-2019
        trade_f, _ = filter_data(trade, support, countries["iso3"].tolist(), (2000, 2019))
        coefs, msg = gravity_safe(trade_f, len(countries))
        fig = plot_trade_distance(trade_f, coefs, countries,
                                  describe_filter(countries["iso3"], countries, (2000, 2019)))
        out = ROOT / "outputs/prototype/trade_distance_mockup.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=150)
        print(f"Saved {out.relative_to(ROOT)}")
    elif "--all" in sys.argv:
        isos = countries["iso3"].tolist()
        bt, coefs, effects = run(isos, (2000, 2019), ROOT / "outputs/prototype/all_2000-2019")
        compare_with_reference(bt, coefs, effects)
    else:
        isos = countries.loc[countries["bloc"].isin(["EU", "Mercosur"]), "iso3"].tolist()
        run(isos, (2010, 2019), ROOT / "outputs/prototype/eu-mercosur_2010-2019")
