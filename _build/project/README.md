# Farm trade and farm support

## Purpose and why

This project looks at farm trade and farm support in 27 countries, grouped in 6 trade blocs, from 2000 to 2019.
Each part of the story uses a different language, so the team can work in the tool each analyst knows best.

| Part | Question | Language | Data |
|---|---|---|---|
| 1 | Who trades farm goods with whom? | Python | `farm_trade.csv` (real) |
| 2 | How do distance, borders, language and trade agreements relate to farm trade? PPML gravity model | R | `farm_trade.csv` (real) |
| 3 | How do subsidies pass through to farm output? Path model with `sem` | Stata | `farm_support.csv` (**synthetic**) |

The 6 blocs are EU, USMCA, Mercosur, ASEAN, East Asia and Oceania. See `data/clean/countries.csv`.

The gravity model in part 2 measures associations, not causal effects. Countries choose their trade agreements, so the trade agreement coefficient also picks up other ties between the two countries.

## Who

| Role | Name | Works on |
|---|---|---|
| Team lead | Amina Haddad | README, data, merges |
| R analyst | Tomas Ferreira | Gravity model |
| Stata analyst | Grace Owusu | Subsidy pass-through |
| Python analyst | Mei Lin Tan | Bloc charts |

The Git history records who changed what, when and why. Ask your AI assistant to summarise it.

## How to run

Open this folder in Positron or VS Code. Run each part from the project root, the folder that holds this README.

| Part | Command |
|---|---|
| Python | `python code/00_master.py` |
| R | `Rscript code/00_master.R` |
| Stata | In Stata, `cd` to the project root, then `do code/00_master.do` |

Each master script runs its numbered scripts in order and writes to `outputs/`.
The parts are independent: run one, two or all three.

**What you need installed:**

- Python with `pandas` and `matplotlib`
- R with `fixest` (`install.packages("fixest")`)
- Stata 17 or later (optional)

All outputs are committed. If you do not have Stata or R, you can still see their results in `outputs/`.

## Folder map

| Folder | Holds | Rule |
|---|---|---|
| `data/raw/` | Notes on the raw sources: links, dates, licences | Read-only. The raw files are too large to ship. |
| `data/clean/` | Clean data, ready for analysis, with a variable dictionary | Prepared upstream. Do not edit by hand. |
| `code/` | Numbered scripts and one master script per language | See `code/README.md` |
| `outputs/figures/` | Charts | Made by code only |
| `outputs/tables/` | Tables (text, CSV, Excel) | Made by code only |
| `outputs/data/` | Tidy data behind the results | Made by code only. Keep the columns stable. |
| `reports/` | Notes and write-ups about the results | Flexible |

The data moves in three stages, like an ETL pipeline: extract (`data/raw/`), transform (`data/clean/`), load (`outputs/`).

## Outputs

| Part | File | What it shows |
|---|---|---|
| Python | `outputs/figures/bloc_trend.png` | Farm trade between blocs over time |
| Python | `outputs/figures/bloc_heatmap_2019.png` | Who trades with whom in 2019, in USD billions |
| Python | `outputs/tables/bloc_trade.csv` | Trade by bloc pair in 2000 and 2019, with growth |
| Python | `outputs/data/bloc_trade.csv` | Tidy: `year, bloc_from, bloc_to, trade_usd` |
| R | `outputs/tables/gravity.txt`, `gravity.csv` | PPML gravity regression table |
| R | `outputs/figures/gravity_coefs.png` | Gravity coefficients with 95% confidence intervals |
| R | `outputs/data/gravity_coefs.csv` | Tidy: `term, estimate, std_error, p_value` |
| Stata | `outputs/tables/sem_elasticities.xlsx` | Direct, indirect and total elasticities |
| Stata | `outputs/figures/sem_scatter.png` | Log farm output against log subsidy |
| Stata | `outputs/data/sem_effects.csv` | Tidy: `effect, path, estimate, std_error` |

The tidy CSVs in `outputs/data/` are for later use, for example a dashboard. You can read them without running any code.

## Data sources

| File | Source | Version or date | Licence |
|---|---|---|---|
| `farm_trade.csv`: `trade_usd` | FAOSTAT Detailed Trade Matrix (TM), FAO | Bulk release of 2025-12-18 | CC BY 4.0 |
| `farm_trade.csv`: distance, border, language, trade agreement, GDP | CEPII Gravity database | V202211 | Etalab Open Licence 2.0 |
| `farm_support.csv` | None: **synthetic** | Simulated, seed 20260311 | None |

**`farm_support.csv` is synthetic.** The numbers are made up by a computer program. They are not real subsidies, fertiliser use or farm output for any country. The data were built with known true elasticities of farm output with respect to subsidy: direct 0.10, indirect 0.24 (through fertiliser) and total 0.34. Use them to check the Stata estimates. Do not draw conclusions about real countries.

Citations, links and the full recipe: `data/raw/README.md` and `data/clean/README.md`.
