# 00_master.R: run every R script in this project, in order.
#
# Run from the project root (the folder that holds code/, data/, outputs/):
#   Rscript code/00_master.R
# Or open the project in your editor and source this file.
#
# Package needed: fixest. Install once with install.packages("fixest").

scripts <- c(
  "code/01_gravity.R"     # PPML gravity model
)

for (s in scripts) {
  message("Running ", s)
  # local = new.env() keeps each script's objects separate
  source(s, local = new.env())
}

message("Done.")
