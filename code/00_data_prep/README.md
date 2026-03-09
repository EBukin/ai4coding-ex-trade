# Data preparation

This stage turns the raw downloads into the clean data in `data/clean/`. One script does it all: `prepare_data.py`.

## What it does and why it is separate

- It downloads two public datasets, cuts them down to our 46 countries and 2000-2019, and joins them into clean tables.
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
6. `write_readmes`: writes `data/clean/README.md` and `data/raw/README.md`, with counts that match the files.

## Sources

- FAOSTAT Detailed Trade Matrix, from FAO, bulk release of 2025-12-18. Licence: CC BY 4.0. Gives the trade values.
- CEPII Gravity database, version V202211. Licence: Etalab Open Licence 2.0. Gives distance, border, language, trade agreements and GDP.
- Full links, versions and citations: [`data/raw/README.md`](../../data/raw/README.md).

## Units

- CEPII reports GDP in thousand US dollars. `build_trade` multiplies GDP by 1,000.

## How to run

- You need Python with `pandas`. `numpy` comes with `pandas`.
- From the project root: `python code/00_data_prep/prepare_data.py`.
- With the filtered extracts already in `data/raw/`, it takes about 15 seconds.
- Without them, it first downloads about 630 MB and filters FAOSTAT, which takes a few minutes more.
- `--refresh` rebuilds the filtered extracts from the downloads, even when they exist.
- The same input always gives the same files, byte for byte.
