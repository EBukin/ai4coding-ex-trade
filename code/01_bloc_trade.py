# Step 1: add up farm trade between country blocs.
# Input:  data/clean/farm_trade.csv  (one row per exporter, importer, year)
#         data/clean/countries.csv   (which bloc each country belongs to)
# Output: outputs/data/bloc_trade.csv    tidy data: year, bloc_from, bloc_to, trade_usd

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

print(bloc_trade.tail(10).to_string(index=False))
