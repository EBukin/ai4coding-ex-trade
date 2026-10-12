# 02_coef_plot.R: plot the gravity coefficients with 95% confidence intervals.
#
# Input:  outputs/data/gravity_coefs.csv  (written by 01_gravity.R)
# Output: outputs/figures/gravity_coefs.png
#
# Uses base R graphics only, so no extra packages are needed.

dir.create("outputs/figures", recursive = TRUE, showWarnings = FALSE)

coefs <- read.csv("outputs/data/gravity_coefs.csv")

# 95% confidence interval: estimate +/- 1.96 standard errors
coefs$lower <- coefs$estimate - 1.96 * coefs$std_error
coefs$upper <- coefs$estimate + 1.96 * coefs$std_error

# Readable labels for the regressors
labels <- c(
  "log(dist_km)" = "Log distance",
  "contig"       = "Shared border",
  "comlang"      = "Common language",
  "rta"          = "Trade agreement"
)
coefs$label <- labels[coefs$term]

# Plot top to bottom in the order of the table
y <- rev(seq_len(nrow(coefs)))

png("outputs/figures/gravity_coefs.png", width = 1600, height = 1000, res = 200)
par(mar = c(4.5, 9, 3, 1))
plot(coefs$estimate, y,
     xlim = range(c(coefs$lower, coefs$upper, 0)),
     ylim = c(0.5, nrow(coefs) + 0.5),
     pch = 19, yaxt = "n", ylab = "",
     xlab = "PPML coefficient (95% CI, clustered by country pair)",
     main = "Gravity model of farm trade, 2000-2019")
segments(coefs$lower, y, coefs$upper, y, lwd = 2)
abline(v = 0, lty = 2, col = "grey40")
axis(2, at = y, labels = coefs$label, las = 1)
dev.off()
