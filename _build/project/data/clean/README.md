# Clean data

Prepared upstream from the raw sources listed in `../raw/README.md`.
Do not edit these files by hand.

## `countries.csv`

One row per country: 27 countries in 6 trade blocs.

| variable | description |
|---|---|
| `iso3` | ISO 3166-1 alpha-3 country code. Key used in the other files. |
| `country` | Short English name. |
| `bloc` | Trade bloc used for grouping: EU, USMCA, Mercosur, ASEAN, East Asia, Oceania. |

The bloc is a fixed label for grouping. It does not change over time, even
where membership did (for example, Poland joined the EU in 2004).

## `farm_trade.csv`

Bilateral trade in agricultural products. One row per exporter, importer and
year: every ordered pair of the 27 countries, 2000-2019 (14,040 rows).
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
reports, the flow is set to 0. In this file: 13,597 import-reported,
413 mirror, 30 with no report. 32 rows have
`trade_usd = 0`: the 30 with no report plus 2 where the
reported value itself is 0. FAOSTAT values are in thousand US dollars; they
are multiplied by 1,000 here.

## `farm_support.csv` (SYNTHETIC)

**These numbers are made up.** They are simulated by a computer program. They
are not real subsidies, fertiliser use or farm output for any country. The
country codes and years are real so the file joins to the others, but the
values carry no information about those countries. Use them to practise
methods, not to draw conclusions.

One row per country and year: 27 countries, 2000-2019 (540 rows).

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
lns = 7.0 + 1.2 * size + 0.02 * (year - 2010) + e1
lnf = 9.5 + 0.6 * lns + e2
lny = 3.7 + 0.1 * lns + 0.4 * lnf + e3
```

Errors are independent normal draws with mean 0 and standard deviations
e1: 0.3, e2: 0.3, e3: 0.08.

`size` is the standardised log of each country's mean GDP (current US
dollars, CEPII) over 2000-2019, so larger economies get larger subsidies.
Random seed: 20260311.

True elasticities of farm output with respect to subsidy:

| effect | path | true value |
|---|---|---|
| direct | subsidy -> output | 0.10 |
| indirect | subsidy -> fertiliser -> output | 0.60 x 0.40 = 0.24 |
| total | direct + indirect | 0.34 |

A path model such as Stata `sem (lny <- lns lnf) (lnf <- lns)` should recover
these values up to sampling noise (about +/- 0.03). Rounding of the levels
adds negligible error.

## Sources and licences

- FAOSTAT Detailed Trade Matrix (TM), used for `trade_usd`. Licence: CC BY
  4.0. Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food
  and Agriculture Organization of the United Nations. Bulk download,
  release of 2025-12-18.
- CEPII Gravity database V202211, used for distance, border, language, trade
  agreement and GDP variables. Licence: Etalab Open Licence 2.0. Citation:
  Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database",
  CEPII Working Paper No. 2022-05.
- `farm_support.csv` is synthetic. It has no source.

Full source detail, download links and versions: `data/raw/README.md`
([`../raw/README.md`](../raw/README.md) from this folder).
