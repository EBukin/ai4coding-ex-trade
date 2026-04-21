# Code

How to run all the code, stage by stage.

- Run every command from the project root, the folder that holds `README.md`.
- All paths in the scripts are relative to the project root.
- Scripts are numbered in the order they run.
- One master script per language runs its other scripts, in order.

## Stages, in run order

- `00_data_prep/`: data preparation. Optional: the clean data are already made.
- R: gravity model of farm trade.
- Each analysis stage reads `data/clean/` and writes to `outputs/`.

## `00_data_prep/`: data preparation (optional)

Run: `python code/00_data_prep/prepare_data.py`

- `prepare_data.py`: downloads the raw data, cleans it and makes the synthetic subsidy data. See [`00_data_prep/README.md`](00_data_prep/README.md).
- You do not need to run it: the clean data are already in `data/clean/`.

## R: gravity model of farm trade

Run: `Rscript code/00_master.R`

- `00_master.R`: runs the scripts below, in order.
- `01_gravity.R`: PPML gravity model. PPML is a regression method that keeps the zero trade flows. Fixed effects for each exporter-year and importer-year (a separate constant for each) absorb GDP and prices.
- `02_coef_plot.R`: coefficient plot with 95% confidence intervals.
