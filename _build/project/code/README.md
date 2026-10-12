# Code

- Scripts are numbered in the order they run.
- One master script per language runs all the others, in order.
- Run each master script from the project root, the folder that holds `README.md`.
- Paths are relative to the project root.

## Python: who trades with whom

Run: `python code/00_master.py`

| Script | Does |
|---|---|
| `00_master.py` | Runs the scripts below, in order |
| `01_bloc_trade.py` | Adds up farm trade by year and bloc pair |
| `02_bloc_trend.py` | Chart of trade between blocs over time |
| `03_bloc_heatmap.py` | Heatmap of trade between blocs in 2019 |

## R: gravity model of farm trade

Run: `Rscript code/00_master.R`

| Script | Does |
|---|---|
| `00_master.R` | Runs the scripts below, in order |
| `01_gravity.R` | PPML gravity model with exporter-year and importer-year fixed effects |
| `02_coef_plot.R` | Coefficient plot with 95% confidence intervals |

## Stata: subsidy pass-through

Run: in Stata, `cd` to the project root, then `do code/00_master.do`

| Script | Does |
|---|---|
| `00_master.do` | Runs the do-files below, in order |
| `01_prepare.do` | Loads the farm support data and takes logs |
| `02_figure.do` | Scatter of log output against log subsidy |
| `03_sem.do` | Path model with `sem`, effects with `estat teffects`, Excel and CSV tables |
