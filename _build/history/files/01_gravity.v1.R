# 01_gravity.R: how do distance, borders, language and trade agreements
# relate to farm trade between countries?
#
# Gravity model of bilateral farm trade, estimated by PPML
# (Poisson pseudo-maximum likelihood). PPML keeps the zero flows
# and does not need log(trade).
#
# Input:  data/clean/farm_trade.csv

library(fixest)

# ---- Load data -------------------------------------------------------------
# One row per exporter, importer and year. trade_usd is 0 where no trade.
trade <- read.csv("data/clean/farm_trade.csv")

# ---- Estimate --------------------------------------------------------------
# Regressors: distance (in logs), shared border, common language and
# regional trade agreement.
# Fixed effects exporter^year and importer^year absorb everything about
# one country in one year (GDP, prices, "multilateral resistance").
# That is why GDP does not enter the formula.
model <- fepois(
  trade_usd ~ log(dist_km) + contig + comlang + rta |
    exporter^year + importer^year,
  data = trade
)

print(summary(model))
