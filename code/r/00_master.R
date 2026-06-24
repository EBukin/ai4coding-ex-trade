# 00_master.R: run every R script in this project, in order.
#
# Run from the project root (the folder that holds code/, data/, outputs/):
#   Rscript code/r/00_master.R
# Or open the project in your editor and source this file.
#
# Package needed: fixest. Install once with install.packages("fixest").

scripts <- c(
  "code/r/01_gravity.R",    # PPML gravity model -> tables and tidy coefficients
  "code/r/02_coef_plot.R"   # coefficient plot with 95% confidence intervals
)

for (s in scripts) {
  message("Running ", s)
  # local = new.env() keeps each script's objects separate
  source(s, local = new.env())
}

message("Done. Results are in outputs/.")
