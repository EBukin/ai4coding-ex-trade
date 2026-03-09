"""Prepare the clean data for the farm trade project.

Run from the project root, the folder that holds README.md:

    python code/00_data_prep/prepare_data.py
    python code/00_data_prep/prepare_data.py --refresh

--refresh rebuilds the two filtered extracts from the downloads.

The analyses never run this script. The clean data in data/clean/ are
already made and committed, so nobody has to download 600 MB to run the
project. Run it only to rebuild the clean data or to change them.

Stages, one function each, in run order:
    download          data/raw/fao_tm.zip, data/raw/gravity.zip
    filter_faostat    data/raw/fao_tm_filtered.csv
    filter_cepii      data/raw/gravity_filtered.csv
    build_countries   data/clean/countries.csv
    build_trade       data/clean/farm_trade.csv
    write_readmes     data/clean/README.md, data/raw/README.md

Needs pandas and numpy (numpy comes with pandas). The same input gives
byte-identical files: fixed seed, sorted rows, fixed number formats.
Downloaded files are read as data only: nothing in them is executed.
"""

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# All paths are relative to the project root.
RAW = Path("data/raw")
CLEAN = Path("data/clean")

YEARS = range(2000, 2020)  # 2000-2019 inclusive
FAO_RELEASE = "2025-12-18"  # FAOSTAT bulk release (date of its zip members)

FAO_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Trade_DetailedTradeMatrix_E_All_Data_(Normalized).zip"
)
FAO_ZIP = RAW / "fao_tm.zip"
FAO_MEMBER = "Trade_DetailedTradeMatrix_E_All_Data_(Normalized).csv"
FAO_EXTRACT = RAW / "fao_tm_filtered.csv"

CEPII_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
CEPII_ZIP = RAW / "gravity.zip"
CEPII_MEMBER = "Gravity_V202211.csv"
CEPII_EXTRACT = RAW / "gravity_filtered.csv"

# 46 countries in 6 blocs: iso3, name, bloc, M49 code (as used by FAOSTAT).
# China is FAO "China; mainland" (FAO code 41, M49 156).
# Belgium is M49 056 from 2000 (Belgium-Luxembourg, 058, ends in 1999).
COUNTRIES = [
    ("DEU", "Germany", "EU", "276"),
    ("FRA", "France", "EU", "250"),
    ("ITA", "Italy", "EU", "380"),
    ("ESP", "Spain", "EU", "724"),
    ("NLD", "Netherlands", "EU", "528"),
    ("POL", "Poland", "EU", "616"),
    ("BEL", "Belgium", "EU", "056"),
    ("DNK", "Denmark", "EU", "208"),
    ("IRL", "Ireland", "EU", "372"),
    ("AUT", "Austria", "EU", "040"),
    ("SWE", "Sweden", "EU", "752"),
    ("FIN", "Finland", "EU", "246"),
    ("PRT", "Portugal", "EU", "620"),
    ("GRC", "Greece", "EU", "300"),
    ("CZE", "Czechia", "EU", "203"),
    ("HUN", "Hungary", "EU", "348"),
    ("SVK", "Slovakia", "EU", "703"),
    ("USA", "United States", "USMCA", "840"),
    ("CAN", "Canada", "USMCA", "124"),
    ("MEX", "Mexico", "USMCA", "484"),
    ("BRA", "Brazil", "Mercosur", "076"),
    ("ARG", "Argentina", "Mercosur", "032"),
    ("URY", "Uruguay", "Mercosur", "858"),
    ("PRY", "Paraguay", "Mercosur", "600"),
    ("CHL", "Chile", "Mercosur", "152"),
    ("BOL", "Bolivia", "Mercosur", "068"),
    ("IDN", "Indonesia", "ASEAN", "360"),
    ("MYS", "Malaysia", "ASEAN", "458"),
    ("THA", "Thailand", "ASEAN", "764"),
    ("VNM", "Viet Nam", "ASEAN", "704"),
    ("PHL", "Philippines", "ASEAN", "608"),
    ("SGP", "Singapore", "ASEAN", "702"),
    ("KHM", "Cambodia", "ASEAN", "116"),
    ("MMR", "Myanmar", "ASEAN", "104"),
    ("LAO", "Lao PDR", "ASEAN", "418"),
    ("BRN", "Brunei", "ASEAN", "096"),
    ("CHN", "China", "East Asia", "156"),
    ("JPN", "Japan", "East Asia", "392"),
    ("KOR", "Korea", "East Asia", "410"),
    ("TWN", "Taiwan", "East Asia", "158"),
    ("HKG", "Hong Kong", "East Asia", "344"),
    ("MNG", "Mongolia", "East Asia", "496"),
    ("AUS", "Australia", "Oceania", "036"),
    ("NZL", "New Zealand", "Oceania", "554"),
    ("FJI", "Fiji", "Oceania", "242"),
    ("VUT", "Vanuatu", "Oceania", "548"),
]
ISO3 = sorted(c[0] for c in COUNTRIES)
M49_TO_ISO3 = {c[3]: c[0] for c in COUNTRIES}


# ---- Stage: download -----------------------------------------------------
# Reads:  the FAOSTAT and CEPII websites.
# Writes: data/raw/fao_tm.zip (about 420 MB), data/raw/gravity.zip (207 MB).
# Why:    the raw files as published, so every later step can be rerun.
def download(url, dest):
    """Download url to dest, unless dest is already there."""
    if dest.exists():
        return
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Downloading {url} -> {dest}")
    # urllib, not curl: curl fails on cepii.fr on Windows.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.replace(dest)


# ---- Stage: filter FAOSTAT -----------------------------------------------
# Reads:  data/raw/fao_tm.zip (an 8.5 GB CSV inside).
# Writes: data/raw/fao_tm_filtered.csv (about 2 MB).
# Why:    keep only our 46 countries and 2000-2019, so the next stages
#         run in seconds instead of minutes.
def filter_faostat():
    """Sum Value (thousand USD) over all items, for import value (element
    5622) and export value (5922). The Trade Matrix has no total item, and
    every item in it is a farm good."""
    cols = ["Reporter Country Code (M49)", "Partner Country Code (M49)",
            "Element Code", "Year", "Value"]
    parts = []
    with zipfile.ZipFile(FAO_ZIP) as z, z.open(FAO_MEMBER) as f:
        reader = pd.read_csv(
            f, usecols=cols, chunksize=2_000_000, encoding="latin-1",
            dtype={cols[0]: str, cols[1]: str, "Element Code": "int32",
                   "Year": "int32", "Value": "float64"},
        )
        for i, chunk in enumerate(reader):
            chunk = chunk[chunk["Element Code"].isin([5622, 5922])
                          & chunk["Year"].between(min(YEARS), max(YEARS))]
            rep = chunk[cols[0]].str.lstrip("'").map(M49_TO_ISO3)
            par = chunk[cols[1]].str.lstrip("'").map(M49_TO_ISO3)
            keep = rep.notna() & par.notna() & (rep != par)
            if keep.any():
                parts.append(pd.DataFrame({
                    "reporter": rep[keep], "partner": par[keep],
                    "element": chunk.loc[keep, "Element Code"],
                    "year": chunk.loc[keep, "Year"],
                    "value": chunk.loc[keep, "Value"],
                }))
            print(f"  FAOSTAT chunk {i + 1}", end="\r", flush=True)
    print()
    df = pd.concat(parts, ignore_index=True)
    df = (df.groupby(["reporter", "partner", "element", "year"], as_index=False)
            ["value"].sum().sort_values(["reporter", "partner", "element", "year"]))
    df.to_csv(FAO_EXTRACT, index=False, lineterminator="\n", float_format="%.3f")


# ---- Stage: filter CEPII -------------------------------------------------
# Reads:  data/raw/gravity.zip.
# Writes: data/raw/gravity_filtered.csv (about 3 MB).
# Why:    same as for FAOSTAT: only our countries and years.
def filter_cepii():
    """Keep the 46 countries, 2000-2019, and the variables we use."""
    cols = ["year", "iso3_o", "iso3_d", "country_exists_o", "country_exists_d",
            "dist", "contig", "comlang_off", "fta_wto", "gdp_o", "gdp_d"]
    parts = []
    with zipfile.ZipFile(CEPII_ZIP) as z, z.open(CEPII_MEMBER) as f:
        for chunk in pd.read_csv(f, usecols=cols, chunksize=2_000_000,
                                 low_memory=False):
            chunk = chunk[chunk["year"].between(min(YEARS), max(YEARS))
                          & chunk["iso3_o"].isin(ISO3) & chunk["iso3_d"].isin(ISO3)
                          & (chunk["iso3_o"] != chunk["iso3_d"])
                          & (chunk["country_exists_o"] == 1)
                          & (chunk["country_exists_d"] == 1)]
            parts.append(chunk[cols])
    df = pd.concat(parts, ignore_index=True).sort_values(["iso3_o", "iso3_d", "year"])
    df.to_csv(CEPII_EXTRACT, index=False, lineterminator="\n", float_format="%.3f")


# ---- Stage: build countries.csv ------------------------------------------
# Reads:  the COUNTRIES list above.
# Writes: data/clean/countries.csv.
# Why:    one small lookup table of country names and blocs for every part.
def build_countries():
    df = pd.DataFrame(COUNTRIES, columns=["iso3", "country", "bloc", "m49"])
    return df[["iso3", "country", "bloc"]].sort_values("iso3").reset_index(drop=True)


# ---- Stage: build farm_trade.csv -----------------------------------------
# Reads:  data/raw/fao_tm_filtered.csv, data/raw/gravity_filtered.csv.
# Writes: data/clean/farm_trade.csv.
# Why:    one panel with trade values and the gravity variables side by
#         side, every country pair and year, zeros kept.
def build_trade():
    fao = pd.read_csv(FAO_EXTRACT)
    imp = fao[fao["element"] == 5622].rename(
        columns={"reporter": "importer", "partner": "exporter", "value": "imp"})
    exp = fao[fao["element"] == 5922].rename(
        columns={"reporter": "exporter", "partner": "importer", "value": "exp"})
    key = ["exporter", "importer", "year"]

    grav = pd.read_csv(CEPII_EXTRACT).rename(columns={
        "iso3_o": "exporter", "iso3_d": "importer", "dist": "dist_km",
        "comlang_off": "comlang", "fta_wto": "rta",
        "gdp_o": "gdp_exporter", "gdp_d": "gdp_importer"})

    # Full grid of ordered pairs x years, so zeros are kept explicitly.
    grid = pd.MultiIndex.from_product(
        [ISO3, ISO3, list(YEARS)], names=key).to_frame(index=False)
    grid = grid[grid["exporter"] != grid["importer"]]
    df = (grid.merge(imp[key + ["imp"]], on=key, how="left")
              .merge(exp[key + ["exp"]], on=key, how="left"))

    # Importer-reported import value first; exporter's export value as mirror.
    src = np.where(df["imp"].notna(), "import",
                   np.where(df["exp"].notna(), "mirror", "none"))
    value = df["imp"].fillna(df["exp"]).fillna(0.0)
    df["trade_usd"] = np.round(value).astype("int64")
    stats = pd.Series(src).value_counts().to_dict()
    stats = {
        "n_import": stats.get("import", 0),
        "n_mirror": stats.get("mirror", 0),
        "n_none": stats.get("none", 0),
        "n_zero": int((df["trade_usd"] == 0).sum()),
        "n_rzero": int(((df["trade_usd"] == 0) & (src != "none")).sum()),
    }

    df = df[key + ["trade_usd"]].merge(grav, on=key, how="left", validate="1:1")
    out_cols = ["exporter", "importer", "year", "trade_usd", "dist_km", "contig",
                "comlang", "rta", "gdp_exporter", "gdp_importer"]
    if df[out_cols].isna().any().any():
        missing = df[df[out_cols].isna().any(axis=1)]
        sys.exit(f"Missing gravity values for {len(missing)} rows:\n{missing.head()}")
    for c in ["dist_km", "contig", "comlang", "rta"]:
        df[c] = np.round(df[c]).astype("int64")
    for c in ["gdp_exporter", "gdp_importer"]:  # CEPII GDP: thousand USD -> USD
        df[c] = np.round(df[c] * 1000).astype("int64")
    df = df[out_cols].sort_values(key).reset_index(drop=True)
    return df, stats


# ---- Stage: write the data READMEs ---------------------------------------
# Reads:  the counts from the stages above.
# Writes: data/clean/README.md, data/raw/README.md.
# Why:    the counts in the READMEs always match the files, because the
#         same run writes both.
CLEAN_README = """# Clean data

- These files are ready for analysis. Do not edit them by hand.
- `code/00_data_prep/prepare_data.py` makes them from the raw sources in [`../raw/README.md`](../raw/README.md).
- The same script writes this README. To change it, change the script and run it again.

## `countries.csv`

One row per country: 46 countries in 6 trade blocs.

- `iso3`: three-letter country code (ISO 3166-1 alpha-3). The key that links the files.
- `country`: short English name.
- `bloc`: trade bloc used for grouping: EU, USMCA, Mercosur, ASEAN, East Asia, Oceania.

About the blocs:

- The bloc is a fixed label. It does not change over time, even where membership did (for example, Poland joined the EU in 2004).
- Chile and Bolivia are grouped with Mercosur for simplicity. Chile is an associate state; Bolivia became a full member only in 2024.
- Taiwan and Hong Kong are separate economies in FAOSTAT and CEPII, so they are kept separate.

## `farm_trade.csv`

Trade in farm goods between countries. One row per exporter, importer and year: every ordered pair of the 46 countries, 2000-2019 ({n_trade} rows). Pairs with no recorded trade are kept, with `trade_usd = 0`.

- `exporter`: iso3 code of the country that sells.
- `importer`: iso3 code of the country that buys.
- `year`: calendar year, 2000-2019.
- `trade_usd`: current US dollars. Value of farm goods shipped from exporter to importer, summed over all FAOSTAT items.
- `dist_km`: kilometres. Distance between the most populated cities of the two countries (CEPII `dist`).
- `contig`: 0 or 1. 1 if the countries share a land border.
- `comlang`: 0 or 1. 1 if the countries share an official language (CEPII `comlang_off`).
- `rta`: 0 or 1. 1 if a regional trade agreement reported to the WTO is in force that year (CEPII `fta_wto`). Two EU members have `rta = 1`, because the EU counts as an agreement.
- `gdp_exporter`: current US dollars. GDP of the exporter (CEPII `gdp_o`). GDP is the value of everything a country produces in a year.
- `gdp_importer`: current US dollars. GDP of the importer (CEPII `gdp_d`).

How `trade_usd` is built:

- FAOSTAT reports each flow twice: once by the importer and once by the exporter.
- We use the value the importer reports.
- Where the importer reports nothing, we use the value the exporter reports (a "mirror" flow).
- Where neither reports, the flow is set to 0.
- In this file: {n_import} rows reported by the importer, {n_mirror} mirror rows, {n_none} rows with no report.
- {n_zero} rows have `trade_usd = 0`: the {n_none} with no report, plus {n_rzero} where the reported value itself is 0.

"""

SOURCES_README = """## Sources and licences

- FAOSTAT Detailed Trade Matrix (TM), used for `trade_usd`. Licence: CC BY 4.0. Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food and Agriculture Organization of the United Nations. Bulk download, release of {fao_release}.
- CEPII Gravity database V202211, used for distance, border, language, trade agreement and GDP. Licence: Etalab Open Licence 2.0. Citation: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database", CEPII Working Paper No. 2022-05.
- Full detail, download links and versions: [`../raw/README.md`](../raw/README.md).
"""

RAW_README = """# Raw data

- Raw data are the files as they come from the source. They are read-only: never edit them.
- The two downloads are large (over 600 MB zipped), so they are not shipped with this project. Git ignores everything in this folder except this README.
- `code/00_data_prep/prepare_data.py` downloads them here, then cuts them down to our 46 countries and 2000-2019. See [`../../code/00_data_prep/README.md`](../../code/00_data_prep/README.md).
- You do not need to run it: the clean data in `../clean/` are already made.
- Versions: FAOSTAT bulk release of {fao_release}; CEPII Gravity V202211.

## Files the script writes here

- `fao_tm.zip`: the FAOSTAT download, about 420 MB.
- `gravity.zip`: the CEPII download, about 207 MB.
- `fao_tm_filtered.csv`: FAOSTAT cut down to our countries and years, about 2 MB.
- `gravity_filtered.csv`: CEPII cut down to our countries and years, about 3 MB.

## FAOSTAT Detailed Trade Matrix (TM)

- Publisher: FAO, the Food and Agriculture Organization of the United Nations.
- Used for: `trade_usd` in `farm_trade.csv`.
- Page: https://www.fao.org/faostat/en/#data/TM
- Bulk file: {fao_url} (normalized CSV, release of {fao_release}, about 420 MB zipped).
- Elements used: 5622 Import value and 5922 Export value, in thousand US dollars, summed over all items, 2000-2019.
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), under the FAO Statistical Database Terms of Use.
- Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food and Agriculture Organization of the United Nations. Bulk download, release of {fao_release}. https://www.fao.org/faostat/en/#data/TM. Licence: CC BY 4.0.

## CEPII Gravity database, version V202211

- Publisher: CEPII, a French research centre on the world economy.
- Used for: `dist_km`, `contig`, `comlang`, `rta`, `gdp_exporter` and `gdp_importer` in `farm_trade.csv`.
- Page: https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8
- Bulk file: {cepii_url} (`Gravity_V202211.csv`, about 207 MB zipped).
- Variables used: `dist`, `contig`, `comlang_off`, `fta_wto`, `gdp_o`, `gdp_d` (GDP in thousand current US dollars).
- Licence: Etalab Open Licence 2.0 (Licence Ouverte 2.0).
- Citation: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database", CEPII Working Paper No. 2022-05, July 2022.
"""


def write_readmes(stats, n_trade):
    counts = {k: f"{v:,}" for k, v in stats.items()}
    clean = CLEAN_README.format(n_trade=f"{n_trade:,}", **counts)
    clean += SOURCES_README.format(fao_release=FAO_RELEASE)
    (CLEAN / "README.md").write_text(clean, encoding="utf-8", newline="\n")
    raw = RAW_README.format(fao_release=FAO_RELEASE, fao_url=FAO_URL,
                            cepii_url=CEPII_URL)
    (RAW / "README.md").write_text(raw, encoding="utf-8", newline="\n")


def write_csv(df, name):
    path = CLEAN / name
    df.to_csv(path, index=False, lineterminator="\n")
    print(f"  {path.as_posix()}: {len(df):,} rows, {path.stat().st_size / 1e6:.2f} MB")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true",
                    help="rebuild the filtered extracts from the downloads")
    args = ap.parse_args()
    if not Path("code/00_data_prep/prepare_data.py").exists():
        sys.exit("Run this script from the project root folder.")

    # The extracts are rebuilt only when asked, or when they are missing.
    if args.refresh or not FAO_EXTRACT.exists():
        download(FAO_URL, FAO_ZIP)
        print("Filtering FAOSTAT (about 3 minutes)...")
        filter_faostat()
    if args.refresh or not CEPII_EXTRACT.exists():
        download(CEPII_URL, CEPII_ZIP)
        print("Filtering CEPII Gravity...")
        filter_cepii()

    CLEAN.mkdir(parents=True, exist_ok=True)
    countries = build_countries()
    trade, stats = build_trade()
    print("Writing clean data:")
    write_csv(countries, "countries.csv")
    write_csv(trade, "farm_trade.csv")
    write_readmes(stats, len(trade))
    print(f"  trade rows by source: {stats}")


if __name__ == "__main__":
    main()
