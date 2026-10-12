# app.py: Shiny dashboard for the farm trade and farm support project.
#
# One page. Pick countries and years in the left sidebar, then click Run.
# The page shows the bloc charts, the PPML gravity model and the subsidy
# path model for that filter. The analysis functions live in prototype.py
# in this folder; this file only builds the page around them.
#
# Start (from the project root):  python -m shiny run --reload code/py-shiny/app.py
# Data: ../../data/clean/ (project layout) or ./data/clean/ (deployed copy).
# Stop: Ctrl+C in the terminal.
# Layout: code/py-shiny/README.md

import sys
from pathlib import Path

import pandas as pd
from shiny import App, reactive, render, ui

# Find prototype.py next to this file, whatever folder the app starts from.
# prototype.py finds the data relative to its own location too.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prototype as proto  # noqa: E402

# Smaller text in figures: they are drawn at the size of their box on screen
proto.plt.rcParams.update({"font.size": 8})

trade, support, countries = proto.load_data()
ALL_ISOS = countries["iso3"].tolist()
# First and last year in the data, for the year slider
YEARS = (int(trade["year"].min()), int(trade["year"].max()))

# Country choices grouped by bloc: {"EU": {"BEL": "Belgium (BEL)", ...}, ...}
CHOICES = {
    bloc: {r.iso3: f"{r.country} ({r.iso3})" for r in rows.itertuples()}
    for bloc, rows in countries.groupby("bloc")
}
# Button id for each bloc, for example "add_east_asia"
BLOC_IDS = {bloc: "add_" + bloc.lower().replace(" ", "_") for bloc in proto.BLOCS}


# ---- Page ---------------------------------------------------------------------

def card(title, *body, footer=None):
    """A box with a header, its content and an optional small footer."""
    parts = [ui.card_header(title), *body]
    if footer:
        parts.append(ui.card_footer(footer))
    return ui.card(*parts, full_screen=True)


app_ui = ui.page_sidebar(
    ui.sidebar(
        # Keep the country box short: scroll inside it when many are selected
        ui.tags.style(".selectize-input { max-height: 170px; overflow-y: auto; }"),
        ui.input_selectize(
            "countries", "Countries", choices=CHOICES, selected=ALL_ISOS,
            multiple=True, options={"plugins": ["remove_button"]},
        ),
        ui.p("Add a whole bloc to the selection:", class_="mb-1 small"),
        ui.div(
            *[ui.input_action_button(BLOC_IDS[b], b, class_="btn-sm btn-outline-secondary")
              for b in proto.BLOCS],
            class_="d-flex flex-wrap gap-1",
        ),
        ui.div(
            ui.input_action_button("select_all", "All", class_="btn-sm btn-outline-secondary"),
            ui.input_action_button("clear", "Clear", class_="btn-sm btn-outline-secondary"),
            class_="d-flex gap-1",
        ),
        ui.input_slider("years", "Years", min=YEARS[0], max=YEARS[1], value=YEARS,
                        step=1, sep=""),
        ui.input_action_button("run", "Run", class_="btn-primary"),
        ui.output_ui("status"),
        width=300,
    ),
    ui.layout_columns(
        card("Bloc trade over time", ui.output_ui("bloc_msg"),
             ui.output_plot("trend", height="420px")),
        card("Who trades with whom", ui.output_plot("heatmap", height="420px")),
        col_widths=(7, 5),
    ),
    ui.layout_columns(
        card(
            "Gravity model (PPML)",
            ui.output_ui("gravity_msg"),
            ui.output_plot("gravity_plot", height="260px"),
            ui.output_table("gravity_tab"),
            ui.output_text("gravity_n"),
            footer="Associations, not causal effects. Exporter-year and importer-year "
                   "fixed effects; standard errors clustered by country pair.",
        ),
        card(
            "Subsidy path model",
            ui.output_ui("sem_msg"),
            ui.output_table("sem_tab"),
            ui.output_text("sem_n"),
            footer="Synthetic data: not real subsidies or output. Elasticities. "
                   "Standard error for the direct path only.",
        ),
        col_widths=(7, 5),
    ),
    card(
        "Trade and distance",
        ui.output_ui("distance_msg"),
        ui.output_plot("trade_distance", height="400px"),
        footer="One point per country pair: mean yearly exports over the chosen years. "
               "Line: slope from the gravity model above.",
    ),
    title="Farm trade and farm support",
    fillable=False,
)


# ---- Server -------------------------------------------------------------------

def server(input, output, session):

    # Bloc buttons add the bloc's countries to the current selection.
    # (No single bloc can run the gravity model on its own.)
    def add_bloc(bloc):
        @reactive.effect
        @reactive.event(input[BLOC_IDS[bloc]])
        def _():
            new = countries.loc[countries["bloc"] == bloc, "iso3"].tolist()
            current = list(input.countries())
            ui.update_selectize("countries",
                                selected=current + [i for i in new if i not in current])

    for bloc in proto.BLOCS:
        add_bloc(bloc)

    @reactive.effect
    @reactive.event(input.select_all)
    def _():
        ui.update_selectize("countries", selected=ALL_ISOS)

    @reactive.effect
    @reactive.event(input.clear)
    def _():
        ui.update_selectize("countries", selected=[])

    # All results are computed here, once per click on Run.
    # ignore_none=False: also run once when the page opens (default filter).
    @reactive.calc
    @reactive.event(input.run, ignore_none=False)
    def results():
        isos = list(input.countries())
        years = input.years()
        if not isos:
            msg = "No country selected. Pick countries, then click Run."
            return {"note": "no countries", "bt": None, "bloc_msg": msg,
                    "coefs": None, "gravity_msg": msg, "effects": None, "sem_msg": msg}

        note = proto.describe_filter(isos, countries, years)
        trade_f, support_f = proto.filter_data(trade, support, isos, years)
        busy = ui.notification_show(
            "Running the models. The first run takes about 20 seconds.",
            duration=None, close_button=False)
        try:
            bt = proto.bloc_trade(trade_f, countries)
            coefs, gravity_msg = proto.gravity_safe(trade_f, len(isos))  # guard runs before any fit
            effects, sem_msg = proto.sem_safe(support_f)
        finally:
            ui.notification_remove(busy)
        return {
            "note": note,
            "bloc_note": proto.bloc_note(isos, countries, years),
            "bt": None if bt.empty else bt,
            "bloc_msg": "Bloc charts need at least 2 countries." if bt.empty else None,
            "trade_f": trade_f,
            "coefs": coefs, "gravity_msg": gravity_msg,
            "n_obs": len(trade_f),
            "n_pairs": trade_f[["exporter", "importer"]].drop_duplicates().shape[0],
            "effects": effects, "sem_msg": sem_msg, "n_sem": len(support_f),
        }

    def message(text):
        """Plain message in place of an output."""
        return ui.div(text, class_="alert alert-warning") if text else None

    @render.ui
    def status():
        return ui.p(f"Showing: {results()['note']}", class_="small text-muted")

    # Bloc charts
    @render.ui
    def bloc_msg():
        return message(results()["bloc_msg"])

    @render.plot
    def trend():
        r = results()
        return None if r["bt"] is None else proto.plot_trend(r["bt"], r["bloc_note"])

    @render.plot
    def heatmap():
        r = results()
        return None if r["bt"] is None else proto.plot_heatmap(r["bt"], r["bloc_note"])

    # Gravity model
    @render.ui
    def gravity_msg():
        return message(results()["gravity_msg"])

    @render.plot
    def gravity_plot():
        r = results()
        return None if r["coefs"] is None else proto.plot_gravity(r["coefs"], r["note"])

    @render.table
    def gravity_tab():
        r = results()
        if r["coefs"] is None:
            return None
        return proto.gravity_table(r["coefs"])

    @render.text
    def gravity_n():
        r = results()
        if r["coefs"] is None:
            return ""
        return f"{r['n_obs']:,} observations, {r['n_pairs']:,} country pairs."

    # Trade against distance, with the fitted gravity line (if the model ran)
    @render.ui
    def distance_msg():
        r = results()
        if r["bt"] is None and r["note"] == "no countries":
            return message(r["bloc_msg"])
        if r["bt"] is None:
            return message("Trade and distance chart needs at least 2 countries.")
        return None

    @render.plot
    def trade_distance():
        r = results()
        if r["bt"] is None:
            return None
        return proto.plot_trade_distance(r["trade_f"], r["coefs"], countries, r["note"])

    # Subsidy path model
    @render.ui
    def sem_msg():
        return message(results()["sem_msg"])

    @render.table
    def sem_tab():
        r = results()
        if r["effects"] is None:
            return None
        e = r["effects"]
        return pd.DataFrame({
            "Effect of subsidy on output": ["Direct", "Indirect (through fertiliser)", "Total"],
            "Elasticity": [f"{v:.3f}" for v in e["estimate"]],
            "Std. error": [f"{e['std_error'][0]:.3f}", "not computed", "not computed"],
        })

    @render.text
    def sem_n():
        r = results()
        return "" if r["effects"] is None else f"{r['n_sem']} country-years."


app = App(app_ui, server)
