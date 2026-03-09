# Raw data

- Raw data are the files as they come from the source. They are read-only: never edit them.
- The two downloads are large (over 600 MB zipped), so they are not shipped with this project. Git ignores everything in this folder except this README.
- `code/00_data_prep/prepare_data.py` downloads them here, then cuts them down to our 46 countries and 2000-2019. See [`../../code/00_data_prep/README.md`](../../code/00_data_prep/README.md).
- You do not need to run it: the clean data in `../clean/` are already made.
- Versions: FAOSTAT bulk release of 2025-12-18; CEPII Gravity V202211.

## Files the script writes here

- `fao_tm.zip`: the FAOSTAT download, about 420 MB.
- `gravity.zip`: the CEPII download, about 207 MB.
- `fao_tm_filtered.csv`: FAOSTAT cut down to our countries and years, about 2 MB.
- `gravity_filtered.csv`: CEPII cut down to our countries and years, about 3 MB.

## FAOSTAT Detailed Trade Matrix (TM)

- Publisher: FAO, the Food and Agriculture Organization of the United Nations.
- Used for: `trade_usd` in `farm_trade.csv`.
- Page: https://www.fao.org/faostat/en/#data/TM
- Bulk file: https://bulks-faostat.fao.org/production/Trade_DetailedTradeMatrix_E_All_Data_(Normalized).zip (normalized CSV, release of 2025-12-18, about 420 MB zipped).
- Elements used: 5622 Import value and 5922 Export value, in thousand US dollars, summed over all items, 2000-2019.
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), under the FAO Statistical Database Terms of Use.
- Citation: FAO. 2025. FAOSTAT: Detailed trade matrix (TM). Rome, Food and Agriculture Organization of the United Nations. Bulk download, release of 2025-12-18. https://www.fao.org/faostat/en/#data/TM. Licence: CC BY 4.0.

## CEPII Gravity database, version V202211

- Publisher: CEPII, a French research centre on the world economy.
- Used for: `dist_km`, `contig`, `comlang`, `rta`, `gdp_exporter` and `gdp_importer` in `farm_trade.csv`.
- Page: https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8
- Bulk file: https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip (`Gravity_V202211.csv`, about 207 MB zipped).
- Variables used: `dist`, `contig`, `comlang_off`, `fta_wto`, `gdp_o`, `gdp_d` (GDP in thousand current US dollars).
- Licence: Etalab Open Licence 2.0 (Licence Ouverte 2.0).
- Citation: Conte, M., P. Cotterlaz and T. Mayer (2022), "The CEPII Gravity database", CEPII Working Paper No. 2022-05, July 2022.
