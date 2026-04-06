# Clean data

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

Trade in farm goods between countries. One row per exporter, importer and year: every ordered pair of the 46 countries, 2000-2019 (41,400 rows). Pairs with no recorded trade are kept, with `trade_usd = 0`.

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
- In this file: 34,082 rows reported by the importer, 2,822 mirror rows, 4,496 rows with no report.
- 5,008 rows have `trade_usd = 0`: the 4,496 with no report, plus 512 where the reported value itself is 0.
- FAOSTAT values are in thousand US dollars. The script multiplies them by 1,000, so `trade_usd` is in US dollars.

## `farm_support.csv` (SYNTHETIC)

**These numbers are made up.** A computer program made them. They are not real subsidies, fertiliser use or farm output for any country. The country codes and years are real, so the file joins to the others, but the values say nothing about those countries. Use them to practise methods, not to draw conclusions.

One row per country and year: 46 countries, 2000-2019 (920 rows).

- `iso3`: the country.
- `year`: calendar year, 2000-2019.
- `subsidy`: million US dollars. Farm support paid to producers (synthetic).
- `fertiliser`: tonnes. Fertiliser used on farms (synthetic).
- `farm_output`: million US dollars. Value of farm output (synthetic).

Values are levels, not logs. Take logs before you estimate elasticities. An elasticity is the percent change in one variable when another changes by 1 percent.

### How the synthetic data were made

- The script is `code/00_data_prep/prepare_data.py`, stage `simulate_support`.
- The model is in natural logs: `lns` is ln subsidy, `lnf` is ln fertiliser, `lny` is ln farm output.
- It has no fixed effects (a fixed effect is a separate constant for each country or each year).

```
lns = 7.0 + 1.2 * size + 0.02 * (year - 2010) + e1
lnf = 9.5 + 0.6 * lns + e2
lny = 3.7 + 0.1 * lns + 0.4 * lnf + e3
```

- `e1`, `e2`, `e3` are random draws from a normal distribution with mean 0 and standard deviations 0.3, 0.3 and 0.08.
- `size` is the standardised log of each country's mean GDP over 2000-2019 (CEPII), so larger economies get larger subsidies.
- Random seed: 20260311. The same seed gives the same numbers on every run.

True elasticities of farm output with respect to subsidy:

- Direct, subsidy -> output: 0.10.
- Indirect, subsidy -> fertiliser -> output: 0.60 x 0.40 = 0.24.
- Total, direct + indirect: 0.34.

A path model estimates linked equations together. Stata `sem (lny <- lns lnf) (lnf <- lns)` should get these values back, up to sampling noise (about +/- 0.03). Rounding the levels adds almost no error.

## Sources and licences

- FAOSTAT Detailed Trade Matrix (TM), used for `trade_usd`. Licence: CC BY 4.0. Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food and Agriculture Organization of the United Nations. Bulk download, release of 2025-12-18.
- CEPII Gravity database V202211, used for distance, border, language, trade agreement and GDP. Licence: Etalab Open Licence 2.0. Citation: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database", CEPII Working Paper No. 2022-05.
- `farm_support.csv` is synthetic. It has no source.
- Full detail, download links and versions: [`../raw/README.md`](../raw/README.md).
