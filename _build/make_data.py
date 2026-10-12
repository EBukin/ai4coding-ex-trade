"""Build the clean data for the farm-trade-support learner project.

Plan: .docs/plans/0018-agentic-exercise-1-build.md, step B1.
Recipe: _build/research/data-sources.md and tooling.md.

Reads raw downloads in _build/raw/ (downloads them if missing) and writes:

    _build/project/data/clean/countries.csv
    _build/project/data/clean/farm_trade.csv
    _build/project/data/clean/farm_support.csv   (SYNTHETIC, fixed seed)
    _build/project/data/clean/README.md
    _build/project/data/raw/README.md

Run from the repository root:

    python _build/make_data.py
    python _build/make_data.py --refresh   # rebuild the filtered caches from the zips

Deterministic: fixed seed, sorted rows, integer or fixed-decimal output.
Rerunning gives byte-identical files. Uses pandas, numpy and stdlib only.
Downloaded files are treated as data only: nothing in them is executed.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
PROJECT = HERE / "project"
CLEAN = PROJECT / "data" / "clean"
RAW_DOC = PROJECT / "data" / "raw"

YEARS = range(2000, 2020)  # 2000-2019 inclusive
FAO_RELEASE = "2025-12-18"  # FAOSTAT bulk file release (date of its zip members)

FAO_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Trade_DetailedTradeMatrix_E_All_Data_(Normalized).zip"
)
FAO_ZIP = RAW / "fao_tm.zip"
FAO_MEMBER = "Trade_DetailedTradeMatrix_E_All_Data_(Normalized).csv"
FAO_CACHE = RAW / "fao_tm_filtered.csv"

GRAV_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
GRAV_ZIP = RAW / "gravity.zip"
GRAV_MEMBER = "Gravity_V202211.csv"
GRAV_CACHE = RAW / "gravity_filtered.csv"

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

# Synthetic data-generating process (logs, no fixed effects).
SEED = 20260311
B_FERT_ON_SUB = 0.60  # lnf <- lns
B_OUT_ON_SUB = 0.10  # lny <- lns (direct)
B_OUT_ON_FERT = 0.40  # lny <- lnf
C_FERT = 9.5  # intercept of lnf
C_OUT = 3.7  # intercept of lny, sets output on a realistic USD million scale
C_SUB = 7.0  # intercept of lns
B_SUB_ON_SIZE = 1.2  # lns <- standardised log mean GDP of the country
B_SUB_TREND = 0.02  # lns trend per year
SD_SUB, SD_FERT, SD_OUT = 0.30, 0.30, 0.08


# ---------------------------------------------------------------- downloads
def download(url: str, dest: Path) -> None:
    """Download url to dest with urllib (curl fails on cepii.fr on Windows)."""
    if dest.exists():
        return
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Downloading {url} -> {dest.name}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.replace(dest)


# ---------------------------------------------------------------- FAOSTAT
def build_fao_cache() -> None:
    """Stream the 8.5 GB FAOSTAT CSV and keep the 46 countries, 2000-2019.

    Sums Value (1000 USD) over all items for import value (5622) and
    export value (5922). TM has no aggregate item; all items are farm goods.
    """
    download(FAO_URL, FAO_ZIP)
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
    df.to_csv(FAO_CACHE, index=False, lineterminator="\n", float_format="%.3f")


# ---------------------------------------------------------------- CEPII
def build_gravity_cache() -> None:
    """Stream Gravity_V202211.csv and keep the 46 countries, 2000-2019."""
    download(GRAV_URL, GRAV_ZIP)
    cols = ["year", "iso3_o", "iso3_d", "country_exists_o", "country_exists_d",
            "dist", "contig", "comlang_off", "fta_wto", "gdp_o", "gdp_d"]
    parts = []
    with zipfile.ZipFile(GRAV_ZIP) as z, z.open(GRAV_MEMBER) as f:
        for chunk in pd.read_csv(f, usecols=cols, chunksize=2_000_000,
                                 low_memory=False):
            chunk = chunk[chunk["year"].between(min(YEARS), max(YEARS))
                          & chunk["iso3_o"].isin(ISO3) & chunk["iso3_d"].isin(ISO3)
                          & (chunk["iso3_o"] != chunk["iso3_d"])
                          & (chunk["country_exists_o"] == 1)
                          & (chunk["country_exists_d"] == 1)]
            parts.append(chunk[cols])
    df = pd.concat(parts, ignore_index=True).sort_values(["iso3_o", "iso3_d", "year"])
    df.to_csv(GRAV_CACHE, index=False, lineterminator="\n", float_format="%.3f")


# ---------------------------------------------------------------- clean files
def make_countries() -> pd.DataFrame:
    df = pd.DataFrame(COUNTRIES, columns=["iso3", "country", "bloc", "m49"])
    return df[["iso3", "country", "bloc"]].sort_values("iso3").reset_index(drop=True)


def make_trade() -> tuple[pd.DataFrame, dict]:
    fao = pd.read_csv(FAO_CACHE)
    imp = fao[fao["element"] == 5622].rename(
        columns={"reporter": "importer", "partner": "exporter", "value": "imp"})
    exp = fao[fao["element"] == 5922].rename(
        columns={"reporter": "exporter", "partner": "importer", "value": "exp"})
    key = ["exporter", "importer", "year"]

    grav = pd.read_csv(GRAV_CACHE).rename(columns={
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
    df["trade_usd"] = np.round(value * 1000).astype("int64")  # 1000 USD -> USD
    stats = pd.Series(src).value_counts().to_dict()
    stats["zero"] = int((df["trade_usd"] == 0).sum())
    stats["reported_zero"] = int(((df["trade_usd"] == 0) & (src != "none")).sum())

    df = df[key + ["trade_usd"]].merge(grav, on=key, how="left", validate="1:1")
    out_cols = ["exporter", "importer", "year", "trade_usd", "dist_km", "contig",
                "comlang", "rta", "gdp_exporter", "gdp_importer"]
    if df[out_cols].isna().any().any():
        missing = df[df[out_cols].isna().any(axis=1)]
        sys.exit(f"Missing gravity values for {len(missing)} rows:\n{missing.head()}")
    for c in ["dist_km", "contig", "comlang", "rta"]:
        df[c] = np.round(df[c]).astype("int64")
    for c in ["gdp_exporter", "gdp_importer"]:  # thousand USD -> USD
        df[c] = np.round(df[c] * 1000).astype("int64")
    df = df[out_cols].sort_values(key).reset_index(drop=True)
    return df, stats


def make_support(trade: pd.DataFrame) -> pd.DataFrame:
    """SYNTHETIC farm support panel. Fixed seed, no fixed effects.

    lns = C_SUB + B_SUB_ON_SIZE*size + B_SUB_TREND*(year-2010) + N(0, SD_SUB)
    lnf = 9.5 + 0.6*lns + N(0, 0.30)
    lny = 3.7 + 0.10*lns + 0.40*lnf + N(0, 0.08)
    size = standardised log of the country's mean GDP in current US dollars (from CEPII), so
    big economies get big subsidies.
    """
    gdp = (trade.groupby("exporter")["gdp_exporter"].mean()
                .reindex(ISO3))
    lg = np.log(gdp.to_numpy(dtype="float64"))
    size = (lg - lg.mean()) / lg.std()

    rng = np.random.default_rng(SEED)
    rows = [(iso, i, y) for i, iso in enumerate(ISO3) for y in YEARS]
    n = len(rows)
    idx = np.array([r[1] for r in rows])
    yr = np.array([r[2] for r in rows], dtype="float64")
    e_s = rng.normal(0, SD_SUB, n)
    e_f = rng.normal(0, SD_FERT, n)
    e_y = rng.normal(0, SD_OUT, n)
    lns = C_SUB + B_SUB_ON_SIZE * size[idx] + B_SUB_TREND * (yr - 2010) + e_s
    lnf = C_FERT + B_FERT_ON_SUB * lns + e_f
    lny = C_OUT + B_OUT_ON_SUB * lns + B_OUT_ON_FERT * lnf + e_y

    return pd.DataFrame({
        "iso3": [r[0] for r in rows],
        "year": [r[2] for r in rows],
        "subsidy": [f"{v:.1f}" for v in np.exp(lns)],  # USD million
        "fertiliser": np.round(np.exp(lnf)).astype("int64"),  # tonnes
        "farm_output": [f"{v:.1f}" for v in np.exp(lny)],  # USD million
    })


# ---------------------------------------------------------------- READMEs
CLEAN_README = """# Clean data

Prepared upstream from the raw sources listed in `../raw/README.md`.
Do not edit these files by hand.

## `countries.csv`

One row per country: 46 countries in 6 trade blocs.

| variable | description |
|---|---|
| `iso3` | ISO 3166-1 alpha-3 country code. Key used in the other files. |
| `country` | Short English name. |
| `bloc` | Trade bloc used for grouping: EU, USMCA, Mercosur, ASEAN, East Asia, Oceania. |

The bloc is a fixed label for grouping. It does not change over time, even
where membership did (for example, Poland joined the EU in 2004). Chile and
Bolivia are grouped with Mercosur for simplicity: Chile is an associate
state, and Bolivia became a full member only in 2024. Taiwan and Hong Kong
are separate economies in FAOSTAT and CEPII, so they are kept separate.

## `farm_trade.csv`

Bilateral trade in agricultural products. One row per exporter, importer and
year: every ordered pair of the 46 countries, 2000-2019 ({n_trade} rows).
Pairs with no recorded trade are kept with `trade_usd = 0`.

| variable | unit | description |
|---|---|---|
| `exporter` | iso3 | Exporting country. |
| `importer` | iso3 | Importing country. |
| `year` | year | Calendar year, 2000-2019. |
| `trade_usd` | current US dollars | Value of agricultural goods shipped from exporter to importer, summed over all FAOSTAT items. |
| `dist_km` | kilometres | Distance between the most populated cities of the two countries (CEPII `dist`). |
| `contig` | 0/1 | 1 if the countries share a land border. |
| `comlang` | 0/1 | 1 if the countries share an official language (CEPII `comlang_off`). |
| `rta` | 0/1 | 1 if a regional trade agreement notified to the WTO is in force in that year (CEPII `fta_wto`). Two EU members have `rta = 1`, because the EU counts as an agreement. |
| `gdp_exporter` | current US dollars | GDP of the exporter (CEPII `gdp_o`). |
| `gdp_importer` | current US dollars | GDP of the importer (CEPII `gdp_d`). |

How `trade_usd` is built: FAOSTAT reports each flow twice. We use the
importer's reported import value. Where the importer reports nothing, we use
the exporter's reported export value instead (a "mirror" flow). Where neither
reports, the flow is set to 0. In this file: {n_import} import-reported,
{n_mirror} mirror, {n_none} with no report. {n_zero} rows have
`trade_usd = 0`: the {n_none} with no report plus {n_rzero} where the
reported value itself is 0. FAOSTAT values are in thousand US dollars; they
are multiplied by 1,000 here.

## `farm_support.csv` (SYNTHETIC)

**These numbers are made up.** They are simulated by a computer program. They
are not real subsidies, fertiliser use or farm output for any country. The
country codes and years are real so the file joins to the others, but the
values carry no information about those countries. Use them to practise
methods, not to draw conclusions.

One row per country and year: 46 countries, 2000-2019 ({n_support} rows).

| variable | unit | description |
|---|---|---|
| `iso3` | iso3 | Country. |
| `year` | year | Calendar year, 2000-2019. |
| `subsidy` | million US dollars | Farm support paid to producers (synthetic). |
| `fertiliser` | tonnes | Fertiliser applied (synthetic). |
| `farm_output` | million US dollars | Value of farm output (synthetic). |

Values are levels, not logs. Take logs before estimating elasticities.

### How the synthetic data were made

Model in natural logs, with no country or year fixed effects
(`lns` = ln subsidy, `lnf` = ln fertiliser, `lny` = ln farm output):

```
lns = {c_sub} + {b_size} * size + {b_trend} * (year - 2010) + e1
lnf = {c_fert} + {b_fs} * lns + e2
lny = {c_out} + {b_ys} * lns + {b_yf} * lnf + e3
```

Errors are independent normal draws with mean 0 and standard deviations
e1: {sd_sub}, e2: {sd_fert}, e3: {sd_out}.

`size` is the standardised log of each country's mean GDP (current US
dollars, CEPII) over 2000-2019, so larger economies get larger subsidies.
Random seed: {seed}.

True elasticities of farm output with respect to subsidy:

| effect | path | true value |
|---|---|---|
| direct | subsidy -> output | {b_ys:.2f} |
| indirect | subsidy -> fertiliser -> output | {b_fs:.2f} x {b_yf:.2f} = {ind:.2f} |
| total | direct + indirect | {tot:.2f} |

A path model such as Stata `sem (lny <- lns lnf) (lnf <- lns)` should recover
these values up to sampling noise (about +/- 0.03). Rounding of the levels
adds negligible error.

## Sources and licences

- FAOSTAT Detailed Trade Matrix (TM), used for `trade_usd`. Licence: CC BY
  4.0. Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food
  and Agriculture Organization of the United Nations. Bulk download,
  release of {fao_release}.
- CEPII Gravity database V202211, used for distance, border, language, trade
  agreement and GDP variables. Licence: Etalab Open Licence 2.0. Citation:
  Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database",
  CEPII Working Paper No. 2022-05.
- `farm_support.csv` is synthetic. It has no source.

Full source detail, download links and versions: `data/raw/README.md`
([`../raw/README.md`](../raw/README.md) from this folder).
"""

RAW_README = """# Raw data sources

The clean files in `../clean/` were prepared upstream from the sources
below. The raw files are large (over 600 MB zipped) and are not shipped with
this project. To rebuild, download them from the links below.

Versions: FAOSTAT bulk release of {fao_release}; CEPII Gravity V202211.

## FAOSTAT Detailed Trade Matrix (TM)

- Used for: `trade_usd` in `farm_trade.csv`.
- Page: https://www.fao.org/faostat/en/#data/TM
- Bulk file: {fao_url}
  (normalized CSV, release of {fao_release}, about 420 MB zipped).
- Elements used: 5622 Import value and 5922 Export value, in thousand US
  dollars, summed over all items, 2000-2019.
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), under
  the FAO Statistical Database Terms of Use.
- Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food and
  Agriculture Organization of the United Nations. Bulk download, release of
  {fao_release}.
  https://www.fao.org/faostat/en/#data/TM. Licence: CC BY 4.0.

## CEPII Gravity database, version V202211

- Used for: `dist_km`, `contig`, `comlang`, `rta`, `gdp_exporter`,
  `gdp_importer` in `farm_trade.csv`, and the country size used to simulate
  `farm_support.csv`.
- Page: https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8
- Bulk file: {grav_url}
  (`Gravity_V202211.csv`, about 207 MB zipped).
- Variables used: `dist`, `contig`, `comlang_off`, `fta_wto`, `gdp_o`,
  `gdp_d` (GDP in thousand current US dollars).
- Licence: Etalab Open Licence 2.0 (Licence Ouverte 2.0).
- Citation: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity
  database", CEPII Working Paper No. 2022-05, July 2022.

## Synthetic data

`farm_support.csv` is simulated, not downloaded. See `../clean/README.md`.
"""


def write_readmes(n_trade: int, n_support: int, stats: dict) -> None:
    ind = B_FERT_ON_SUB * B_OUT_ON_FERT
    text = CLEAN_README.format(
        n_trade=f"{n_trade:,}", n_support=n_support,
        n_import=f"{stats.get('import', 0):,}", n_mirror=stats.get("mirror", 0),
        n_none=stats.get("none", 0), n_zero=stats.get("zero", 0),
        n_rzero=stats.get("reported_zero", 0), fao_release=FAO_RELEASE,
        c_sub=C_SUB, b_size=B_SUB_ON_SIZE, b_trend=B_SUB_TREND, sd_sub=SD_SUB,
        c_fert=C_FERT, b_fs=B_FERT_ON_SUB, sd_fert=SD_FERT,
        c_out=C_OUT, b_ys=B_OUT_ON_SUB, b_yf=B_OUT_ON_FERT, sd_out=SD_OUT,
        seed=SEED, ind=ind, tot=B_OUT_ON_SUB + ind)
    (CLEAN / "README.md").write_text(text, encoding="utf-8", newline="\n")
    (RAW_DOC / "README.md").write_text(
        RAW_README.format(fao_release=FAO_RELEASE, fao_url=FAO_URL, grav_url=GRAV_URL),
        encoding="utf-8", newline="\n")


def write_csv(df: pd.DataFrame, name: str) -> None:
    path = CLEAN / name
    df.to_csv(path, index=False, lineterminator="\n")
    print(f"  {name}: {len(df):,} rows, {path.stat().st_size / 1e6:.2f} MB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true",
                    help="rebuild the filtered caches from the raw zips")
    args = ap.parse_args()

    if args.refresh or not FAO_CACHE.exists():
        print("Filtering FAOSTAT (about 3 minutes)...")
        build_fao_cache()
    if args.refresh or not GRAV_CACHE.exists():
        print("Filtering CEPII Gravity...")
        build_gravity_cache()

    CLEAN.mkdir(parents=True, exist_ok=True)
    RAW_DOC.mkdir(parents=True, exist_ok=True)
    countries = make_countries()
    trade, stats = make_trade()
    support = make_support(trade)
    print("Writing clean data:")
    write_csv(countries, "countries.csv")
    write_csv(trade, "farm_trade.csv")
    write_csv(support, "farm_support.csv")
    write_readmes(len(trade), len(support), stats)
    print(f"  trade sources: {stats}")


if __name__ == "__main__":
    main()
