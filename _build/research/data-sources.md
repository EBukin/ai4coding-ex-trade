# Data sources for farm-trade-support (plan 0018, step A1)

Date: 2026-10-11. Status: tested end to end on this machine.

## Decision

Use **real farm trade**: FAOSTAT Detailed Trade Matrix (TM), summed over all items, joined to CEPII Gravity V202211. No fallback needed.

Trial result (27 countries, 2000-2019): 14,040 rows, 1.06 MB CSV, full balanced panel, 0.2% zeros.
PPML (`fepois`, exporter-year + importer-year FE, SE clustered by pair):
log(dist) -0.57***, contig +0.75***, comlang -0.11 (n.s.), rta +0.62***.
With GDP and year FE only: log(dist) -0.35***, rta +0.50***, log(gdp_o) 0.46, log(gdp_d) 0.66.
Farm trade among the 27 grows from USD 227 bn (2000) to 730 bn (2019).

## Recipe for `_build/make_data.py`

1. Download once with Python `urllib` (works). `curl` on Windows fails on cepii.fr with `CRYPT_E_NO_REVOCATION_CHECK`; use `curl --ssl-no-revoke` if needed.
   - FAOSTAT: `https://bulks-faostat.fao.org/production/Trade_DetailedTradeMatrix_E_All_Data_(Normalized).zip` (420.7 MB zip, 8.5 GB CSV, 52.4 M rows, last modified 2025-12-23).
   - CEPII: `https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip` (206.7 MB zip; `Gravity_V202211.csv` 1.25 GB).
2. FAOSTAT: stream `Trade_DetailedTradeMatrix_E_All_Data_(Normalized).csv` from the zip with `pandas.read_csv(chunksize=2_000_000, encoding="latin-1")`. Read the M49 columns as `str` (values look like `'276`, with a leading apostrophe). Keep columns `Reporter Country Code (M49)`, `Partner Country Code (M49)`, `Element Code`, `Year`, `Value`. Filter `Element Code` in {5622 Import value, 5922 Export value}, `Year` 2000-2019, both countries in the list. Sum `Value` over all items (TM has no aggregate item; 572 items, all agricultural). Unit is 1000 USD. Takes about 2.5 min.
3. Flow: use the **importer-reported import value** (5622; reporter = importer, partner = exporter). If missing, use the exporter's export value (5922) as mirror. Trial: 13,597 import, 413 mirror, 30 none (set to 0). Median export/import ratio 0.93.
4. Gravity: stream `Gravity_V202211.csv`; keep `year, iso3_o, iso3_d, dist, contig, comlang_off, fta_wto, gdp_o, gdp_d`, filter years, both iso3 in list, `country_exists_o == 1`, `country_exists_d == 1`, `iso3_o != iso3_d`. No missing values for this set.
5. Join: FAO M49 to iso3 via a fixed dict in the script (or `iso3num_o` in Gravity). China is FAO code 41 "China; mainland", M49 156. Belgium is M49 056 from 2000 (Belgium-Luxembourg ends 1999).
6. Output `farm_trade.csv`: `exporter, importer, year, trade_usd` (= value x 1000, integer), `dist_km` (= `dist`), `contig`, `comlang` (= `comlang_off`), `rta` (= `fta_wto`), `gdp_o`, `gdp_d` (Gravity GDP is in thousand current USD; multiply by 1000). Write integers, not floats. Expect 14,040 rows (27 x 26 x 20), about 1 MB.

## Countries (27, 6 blocs)

| bloc | iso3 |
|---|---|
| EU | DEU, FRA, ITA, ESP, NLD, POL, BEL, DNK, IRL |
| USMCA | USA, CAN, MEX |
| Mercosur | BRA, ARG, URY, PRY |
| ASEAN | IDN, MYS, THA, VNM, PHL, SGP |
| East Asia | CHN, JPN, KOR |
| Oceania | AUS, NZL |

Names: Germany, France, Italy, Spain, Netherlands, Poland, Belgium, Denmark, Ireland, United States, Canada, Mexico, Brazil, Argentina, Uruguay, Paraguay, Indonesia, Malaysia, Thailand, Viet Nam, Philippines, Singapore, China, Japan, Korea, Australia, New Zealand. M49 codes, same order: 276 250 380 724 528 616 056 208 372 840 124 484 076 032 858 600 360 458 764 704 608 702 156 392 410 036 554.

## Licences and citations

- FAOSTAT: CC BY 4.0 (FAO Statistical Database Terms of Use, Annex 1). Cite: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Accessed 2026-10-11. https://www.fao.org/faostat/en/#data/TM. Licence: CC-BY-4.0.
- CEPII Gravity V202211: Etalab Open Licence 2.0. Cite: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database", CEPII Working Paper No. 2022-05. Data: https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8

## Risks

- Downloads total 627 MB and land in `_build/raw/` (601 MB now). Git-ignore `_build/raw/` before any commit: `_build/` is untracked and not ignored yet.
- With pair FE added, rta falls to +0.04 (n.s.). Teach the exporter-year + importer-year spec only.
- `comlang` is small and insignificant; harmless, but the README should not claim a language effect.
- `fta_wto` treats EU members as one agreement; intra-EU pairs carry rta = 1 throughout. POL pairs with the EU have rta = 1 from 2000 (Europe Agreement), not only from EU entry in 2004.
- FAOSTAT bulk is revised yearly; values may shift slightly. Pin "accessed" date in `data/raw/README.md`.
- CEPII Gravity ends in 2020; GDP there is the source for `gdp_o`/`gdp_d`.
