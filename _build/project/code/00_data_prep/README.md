# Data preparation

This stage turns the raw downloads into the clean data in `data/clean/`. One script does it all: `prepare_data.py`.

## What it does and why it is separate

- It downloads two public datasets, cuts them down to our 46 countries and 2000-2019, and joins them into clean tables.
- It also makes the synthetic subsidy data for the Stata part.
- It is separate from the analyses because it needs 600 MB of downloads. The analyses only read the small clean files.
- The clean data are already made and committed. **You do not need to run this script** to run the project.
- The master scripts of the analyses never call it.

## The pipeline

Each step is one function in `prepare_data.py`. The comment above each function says what it reads, what it writes and why.

1. `download`: gets the raw zips from FAOSTAT and CEPII and saves them as `data/raw/fao_tm.zip` and `data/raw/gravity.zip`.
2. `filter_faostat`: keeps our countries and years and writes `data/raw/fao_tm_filtered.csv`.
3. `filter_cepii`: does the same for CEPII and writes `data/raw/gravity_filtered.csv`.
4. `build_countries`: writes `data/clean/countries.csv`, the list of countries and blocs.
5. `build_trade`: joins trade values and gravity variables and writes `data/clean/farm_trade.csv`.
6. `simulate_support`: makes the synthetic `data/clean/farm_support.csv`.
7. `write_readmes`: writes `data/clean/README.md` and `data/raw/README.md`, with counts that match the files.

## Sources

- FAOSTAT Detailed Trade Matrix, from FAO, bulk release of 2025-12-18. Licence: CC BY 4.0. Gives the trade values.
- CEPII Gravity database, version V202211. Licence: Etalab Open Licence 2.0. Gives distance, border, language, trade agreements and GDP.
- Full links, versions and citations: [`data/raw/README.md`](../../data/raw/README.md).

## Units

- FAOSTAT reports trade values in thousand US dollars.
- `build_trade` multiplies them by 1,000, so `trade_usd` in `farm_trade.csv` is in US dollars.
- CEPII reports GDP in thousand US dollars too. `build_trade` also multiplies GDP by 1,000.

## The synthetic subsidy data

- There are no comparable subsidy data for all 46 countries, so `simulate_support` makes them up from a known model.
- Three equations in logs: subsidy depends on country size and a time trend; fertiliser depends on subsidy; farm output depends on subsidy and fertiliser.
- Country size comes from each country's mean GDP in CEPII, so larger economies get larger subsidies.
- The true elasticities of output with respect to subsidy are: direct 0.10, indirect through fertiliser 0.24, total 0.34. An elasticity is the percent change in output when subsidy rises by 1 percent.
- The random seed is fixed (20260311), so every run gives the same numbers.
- The full model, with all its values, is in [`data/clean/README.md`](../../data/clean/README.md).

## How to run

- You need Python with `pandas`. `numpy` comes with `pandas`.
- From the project root: `python code/00_data_prep/prepare_data.py`.
- With the filtered extracts already in `data/raw/`, it takes about 15 seconds.
- Without them, it first downloads about 630 MB and filters FAOSTAT, which takes a few minutes more.
- `--refresh` rebuilds the filtered extracts from the downloads, even when they exist.
- The same input always gives the same files, byte for byte.
