# Code

How to run all the code, stage by stage.

- Run every command from the project root, the folder that holds `README.md`.
- All paths in the scripts are relative to the project root.
- Scripts are numbered in the order they run.
- One master script per language runs its other scripts, in order.

## Stages, in run order

- `00_data_prep/`: data preparation. Optional: the clean data are already made.
- `python/`: who trades with whom.
- `r/`: gravity model of farm trade.
- `stata/`: subsidy pass-through.
- The analysis stages are independent: run one, two or all three, in any order. Each reads `data/clean/` and writes to `outputs/`.
- `py-shiny/` and `r-shiny/` are dashboards, not stages: you start them by hand. They read `data/clean/` and write nothing.

## `00_data_prep/`: data preparation (optional)

Run: `python code/00_data_prep/prepare_data.py`

- `prepare_data.py`: downloads the raw data, cleans it and makes the synthetic subsidy data. See [`00_data_prep/README.md`](00_data_prep/README.md).
- You do not need to run it: the clean data are already in `data/clean/`.

## `python/`: who trades with whom

Run: `python code/python/00_master.py`

- `00_master.py`: runs the scripts below, in order.
- `01_bloc_trade.py`: adds up farm trade by year and bloc pair.
- `02_bloc_trend.py`: chart of trade between blocs over time.
- `03_bloc_heatmap.py`: heatmap of trade between blocs in 2019.

## `r/`: gravity model of farm trade

Run: `Rscript code/r/00_master.R`

- `00_master.R`: runs the scripts below, in order.
- `01_gravity.R`: PPML gravity model. PPML is a regression method that keeps the zero trade flows. Fixed effects for each exporter-year and importer-year (a separate constant for each) absorb GDP and prices.
- `02_coef_plot.R`: coefficient plot with 95% confidence intervals.

## `stata/`: subsidy pass-through

Run: in Stata, `cd` to the project root, then `do code/stata/00_master.do`

- `00_master.do`: runs the do-files below, in order.
- `01_prepare.do`: loads the farm support data and takes logs.
- `02_figure.do`: scatter of log output against log subsidy.
- `03_sem.do`: path model with `sem` (linked equations estimated together), effects with `estat teffects`, Excel and CSV tables.

## `py-shiny/` and `r-shiny/`: dashboards (optional)

The same dashboard in Python and in R: bloc charts, gravity model, subsidy path model and trade against distance, for any countries and years.

- Python: `python -m shiny run --reload code/py-shiny/app.py`. See [`py-shiny/README.md`](py-shiny/README.md).
- R: in the R console, `shiny::runApp("code/r-shiny")`. See [`r-shiny/README.md`](r-shiny/README.md).
- Live versions: [Python](https://datanalytics.worldbank.org/ai4coding-ex2-3-py-shiny/) and [R](https://datanalytics.worldbank.org/ai4coding-ex2-3-r-shiny/). They run on an earlier copy of the data with 27 countries.
