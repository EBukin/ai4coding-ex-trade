# Step 1: add up farm trade between country blocs.
# Input:  data/clean/farm_trade.csv  (one row per exporter, importer, year)
#         data/clean/countries.csv   (which bloc each country belongs to)
# Output: outputs/data/bloc_trade.csv    tidy data: year, bloc_from, bloc_to, trade_usd
#         outputs/tables/bloc_trade.csv  summary table: 2000 vs 2019 by bloc pair

import pandas as pd

# Read the clean data.
trade = pd.read_csv("data/clean/farm_trade.csv")
countries = pd.read_csv("data/clean/countries.csv")

# Look up the bloc of the exporter and of the importer.
bloc_of = countries.set_index("iso3")["bloc"]
trade["bloc_from"] = trade["exporter"].map(bloc_of)
trade["bloc_to"] = trade["importer"].map(bloc_of)

# Add up trade for each year and pair of blocs.
bloc_trade = (
    trade.groupby(["year", "bloc_from", "bloc_to"], as_index=False)["trade_usd"]
    .sum()
    .sort_values(["year", "bloc_from", "bloc_to"])
)

# Save the tidy data. Other scripts and other languages read this file.
bloc_trade.to_csv("outputs/data/bloc_trade.csv", index=False, lineterminator="\n")

# Summary table: trade in 2000 and 2019 for each bloc pair, in USD billions.
first, last = 2000, 2019
summary = bloc_trade[bloc_trade["year"].isin([first, last])].pivot_table(
    index=["bloc_from", "bloc_to"], columns="year", values="trade_usd"
)
summary = (summary / 1e9).round(2)
summary.columns = [f"usd_bn_{first}", f"usd_bn_{last}"]

# Growth from 2000 to 2019, in percent.
summary["growth_pct"] = (
    100 * (summary[f"usd_bn_{last}"] / summary[f"usd_bn_{first}"] - 1)
).round(1)

# Biggest trade flows first.
summary = summary.sort_values(f"usd_bn_{last}", ascending=False).reset_index()
summary.to_csv("outputs/tables/bloc_trade.csv", index=False, lineterminator="\n")

print(summary.head(10).to_string(index=False))
