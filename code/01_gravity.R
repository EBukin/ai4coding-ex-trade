# 01_gravity.R: how do distance, borders, language and trade agreements
# relate to farm trade between countries?
#
# Gravity model of bilateral farm trade, estimated by PPML
# (Poisson pseudo-maximum likelihood). PPML keeps the zero flows
# and does not need log(trade).
#
# Input:  data/clean/farm_trade.csv
# Output: outputs/tables/gravity.txt   readable regression table
#         outputs/tables/gravity.csv   same table as CSV
#         outputs/data/gravity_coefs.csv  tidy: term, estimate, std_error, p_value

library(fixest)

# Create output folders if they are missing
dir.create("outputs/tables", recursive = TRUE, showWarnings = FALSE)
dir.create("outputs/data", recursive = TRUE, showWarnings = FALSE)

# ---- Load data -------------------------------------------------------------
# One row per exporter, importer and year. trade_usd is 0 where no trade.
trade <- read.csv("data/clean/farm_trade.csv")

# ---- Estimate --------------------------------------------------------------
# Regressors: distance (in logs), shared border, common language and
# regional trade agreement.
# Fixed effects exporter^year and importer^year absorb everything about
# one country in one year (GDP, prices, "multilateral resistance").
# That is why GDP does not enter the formula.
# The coefficients are associations, not causal effects: countries choose
# their trade agreements, so rta also picks up other ties between them.
model <- fepois(
  trade_usd ~ log(dist_km) + contig + comlang + rta |
    exporter^year + importer^year,
  data = trade
)

print(summary(model))

# Open a file for writing with LF line endings on every system. R on
# Windows writes CRLF otherwise, and Git then shows an unchanged result as
# changed after a rerun.
lf_file <- function(path) file(path, open = "wb")

# ---- Readable table --------------------------------------------------------
# Standard errors go in brackets below each coefficient.
tab <- etable(model, digits = 3, se.below = TRUE, headers = "PPML")

# etable returns a data frame; print it to a text file with a title
con <- lf_file("outputs/tables/gravity.txt")
writeLines(c("Gravity model of farm trade, 46 countries, 2000-2019", "",
             capture.output(print(tab))), con)
close(con)

# CSV version: give the first column a name and drop padding spaces
names(tab)[1] <- "row"
tab[] <- lapply(tab, trimws)
con <- lf_file("outputs/tables/gravity.csv")
write.csv(tab, con, row.names = FALSE)
close(con)

# ---- Tidy coefficients -----------------------------------------------------
# One row per regressor, for later reuse (plots, other languages).
ct <- coeftable(model)
coefs <- data.frame(
  term      = rownames(ct),
  estimate  = ct[, "Estimate"],
  std_error = ct[, "Std. Error"],
  p_value   = ct[, "Pr(>|z|)"]
)
con <- lf_file("outputs/data/gravity_coefs.csv")
write.csv(coefs, con, row.names = FALSE)
close(con)

print(coefs, row.names = FALSE)
