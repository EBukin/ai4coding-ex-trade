# Python dashboard

A Shiny app that shows the three parts of the project for any choice of countries and years: the bloc charts, the PPML gravity model, the subsidy path model, and trade against distance.

- Live version: <https://datanalytics.worldbank.org/ai4coding-ex2-3-py-shiny/>. It was deployed on 2026-10-12 from an earlier copy of the data with 27 countries, so its numbers differ from the files here.
- The app reads `data/clean/` and writes nothing.

## Files

- `app.py`: the page. It only builds the page around the functions in `prototype.py`.
- `prototype.py`: the analysis functions. Run on its own, it writes the same outputs as files, to check them before they go on the page.

## What you need

- Python with `shiny`, `pandas`, `matplotlib`, `statsmodels` and `pyfixest`:

```sh
python -m pip install shiny pandas matplotlib statsmodels pyfixest
```

- Tested with Python 3.13, shiny 1.8.0, pyfixest 0.60.0, statsmodels 0.14.6, pandas 2.3.3, matplotlib 3.10.8.

## Run it

- In Positron or VS Code with the Shiny extension: open `code/py-shiny/app.py` and click **Run Shiny App**.
- Or in a terminal, from the project root: `python -m shiny run --reload code/py-shiny/app.py`. Open the address it prints, usually <http://127.0.0.1:8000>.
- Pick countries and years in the left sidebar, then click **Run**. Nothing changes until you click **Run**.
- The first load takes up to a minute while the gravity package loads.
- Stop it with **Stop Shiny App**, or `Ctrl+C` in the terminal.

## Check the numbers

- `python code/py-shiny/prototype.py --all`: all countries, 2000-2019. It compares the results with `outputs/data/`.
  - Bloc totals and gravity coefficients match exactly.
  - The path model matches the Stata estimates. Its direct-path standard error is a little larger: OLS divides by n - k, Stata `sem` by n.
- `python code/py-shiny/prototype.py`: EU and Mercosur, 2010-2019.
- Both write to `outputs/prototype/`, which is for checking only. Do not commit it.

## Layout

- One page, for economists, on a laptop screen. Main use: compare blocs.
- Left sidebar:
  - Countries: a multi-select grouped by bloc. All countries at the start.
  - One button per bloc. It adds the bloc to the selection; it does not replace it, because no single bloc can run the gravity model on its own.
  - **All** and **Clear**.
  - Years: a slider over the years in the data.
  - **Run**, and a line that says which filter the results use.
- Main area:
  - Row 1: bloc trend chart, one panel per exporting bloc; bloc heatmap for the last year of the filter.
  - Row 2: gravity model, a coefficient plot and table; subsidy path model table.
  - Row 3: trade against distance, one point per country pair, with the gravity line.

## Rules on the page

- Bloc totals cover the selected countries only. Chart titles say so.
- The gravity model needs at least 6 countries, and each regressor must vary across pairs. If not, its box shows a plain message.
- The path model needs at least 20 country-years.
- The gravity coefficients are associations, not causal effects.
- The subsidy data are synthetic.
