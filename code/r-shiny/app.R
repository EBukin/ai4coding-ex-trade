# dashboard/app.R: Shiny dashboard of farm trade and farm support.
#
# One page. Pick countries and years in the left sidebar, then click Run.
# The page shows, for the selected countries and years:
#   1. bloc trend chart and bloc heatmap
#   2. gravity model (PPML): coefficient plot and table
#   3. subsidy pass-through (path model) table
#   4. farm trade against distance, with the gravity line
#
# Built from dashboard/prototype.R (same functions, copied below) and
# dashboard/LAYOUT.md. Models rerun only when you click Run. On first load
# the page shows results for all countries, 2000-2019.
#
# Start it (see README.md, "Run the dashboard"):
#   open this file and click "Run Shiny App", or in the R console run
#   shiny::runApp("dashboard") from the project root.
#
# Packages: shiny, bslib, fixest and base R (base graphics for the charts).
# NOTE: farm_support.csv is SYNTHETIC (made up). See data/clean/README.md.

library(shiny)
library(bslib)
library(fixest)

# ---- Load data ---------------------------------------------------------------
# shiny::runApp("dashboard") runs the app from inside dashboard/, while the
# Shiny extension may run it from the project root. Look for the data in
# both places, so the app works either way.
root <- if (file.exists("../data/clean/farm_trade.csv")) ".." else "."
if (!file.exists(file.path(root, "data/clean/farm_trade.csv"))) {
  stop("Cannot find data/clean/. Start the app from the project root or from dashboard/.")
}
trade     <- read.csv(file.path(root, "data/clean/farm_trade.csv"))
support   <- read.csv(file.path(root, "data/clean/farm_support.csv"))
countries <- read.csv(file.path(root, "data/clean/countries.csv"))

# Bloc of each country, for example bloc_of["FRA"] is "EU"
bloc_of <- setNames(countries$bloc, countries$iso3)

# One fixed colour per bloc, so a bloc has the same colour in every chart.
# Okabe-Ito colours stay distinct for most colour-blind readers.
all_blocs   <- sort(unique(countries$bloc))
bloc_colour <- setNames(palette.colors(9, "Okabe-Ito")[c(2, 3, 4, 6, 7, 8)], all_blocs)

# ---- Filter ------------------------------------------------------------------
# Keep trade only between selected countries (exporter AND importer selected),
# and support rows only for selected countries. years = c(first, last).
filter_trade <- function(trade, iso3, years) {
  trade[trade$exporter %in% iso3 & trade$importer %in% iso3 &
          trade$year >= years[1] & trade$year <= years[2], ]
}
filter_support <- function(support, iso3, years) {
  support[support$iso3 %in% iso3 &
            support$year >= years[1] & support$year <= years[2], ]
}

# Short text for chart titles, for example "EU, Mercosur (13 countries), 2010-2019"
filter_label <- function(iso3, years) {
  yrs <- if (years[1] == years[2]) years[1] else paste0(years[1], "-", years[2])
  if (length(iso3) == nrow(countries)) {
    who <- sprintf("all %d countries", nrow(countries))
  } else {
    # Name the blocs if the selection is made of whole blocs
    blocs <- sort(unique(bloc_of[iso3]))
    whole <- setequal(iso3, countries$iso3[countries$bloc %in% blocs])
    who <- if (whole) sprintf("%s (%d countries)", paste(blocs, collapse = ", "), length(iso3))
           else if (length(iso3) == 1) "1 selected country"
           else sprintf("%d selected countries", length(iso3))
  }
  paste0(who, ", ", yrs)
}

# ---- 1. Bloc charts ----------------------------------------------------------
# Add up trade by year, exporting bloc and importing bloc.
# Under a country filter, these are totals of the selected countries only.
bloc_trade <- function(trade) {
  trade$bloc_from <- bloc_of[trade$exporter]
  trade$bloc_to   <- bloc_of[trade$importer]
  aggregate(trade_usd ~ year + bloc_from + bloc_to, data = trade, FUN = sum)
}

# Trend: one panel per exporting bloc, one line per importing bloc, USD billions.
# The legend sits below the panels, so it never covers a line.
plot_trend <- function(bt, label) {
  from <- sort(unique(bt$bloc_from))
  to   <- sort(unique(bt$bloc_to))
  yr   <- range(bt$year)
  op <- par(mfrow = c(ceiling(length(from) / 3), min(length(from), 3)),
            mar = c(3, 4, 2.5, 1), oma = c(3, 0, 2.5, 0))
  on.exit(par(op))
  for (b in from) {
    s <- bt[bt$bloc_from == b, ]
    plot(NA, xlim = yr, ylim = c(0, max(s$trade_usd) / 1e9),
         xlab = "", ylab = "USD billions", main = paste("Exports from", b))
    for (dest in to) {
      r <- s[s$bloc_to == dest, ]
      r <- r[order(r$year), ]
      lines(r$year, r$trade_usd / 1e9, col = bloc_colour[dest], lwd = 2,
            type = if (nrow(r) == 1) "p" else "l", pch = 19)
    }
  }
  mtext(paste("Farm trade between blocs:", label), outer = TRUE, cex = 1.1, font = 2)
  # Legend in the bottom margin of the whole figure
  par(fig = c(0, 1, 0, 1), oma = c(0, 0, 0, 0), mar = c(0, 0, 0, 0), new = TRUE)
  plot.new()
  legend("bottom", legend = to, col = bloc_colour[to], lwd = 2, horiz = TRUE,
         bty = "n", cex = 0.9, title = "Importing bloc", xpd = NA)
}

# Heatmap: exporting bloc in rows, importing bloc in columns, last year of the filter
plot_heatmap <- function(bt, label) {
  year <- max(bt$year)
  s <- bt[bt$year == year, ]
  m <- xtabs(trade_usd ~ bloc_from + bloc_to, data = s) / 1e9
  m <- m[nrow(m):1, , drop = FALSE]   # first bloc on top
  op <- par(mar = c(7, 8, 4, 1)); on.exit(par(op))
  # Colour on a log scale, so one large cell does not wash out the others.
  # Cells with no trade stay white. The numbers in the cells are USD billions.
  z <- log10(unclass(m))
  z[!is.finite(z)] <- NA
  image(seq_len(ncol(m)), seq_len(nrow(m)), t(z),
        col = hcl.colors(50, "Blues 3", rev = TRUE),
        axes = FALSE, xlab = "", ylab = "")
  # Title centred on the whole figure, not the plot area, so it is not cut off
  mtext(sprintf("Farm trade in %d, USD billions (colour: log scale)\n%s", year, label),
        side = 3, line = 1, at = grconvertX(0.5, "ndc", "user"), font = 2, cex = 0.9)
  axis(1, at = seq_len(ncol(m)), labels = colnames(m), las = 2, cex.axis = 0.9)
  axis(2, at = seq_len(nrow(m)), labels = rownames(m), las = 1, cex.axis = 0.9)
  mtext("Exporting bloc", side = 2, line = 6.5)
  mtext("Importing bloc", side = 1, line = 5.5)
  text(rep(seq_len(ncol(m)), each = nrow(m)), rep(seq_len(nrow(m)), ncol(m)),
       sprintf("%.1f", m), cex = 0.9,
       col = ifelse(!is.na(z) & z > mean(range(z, na.rm = TRUE)), "white", "black"))
}

# ---- 2. Gravity model --------------------------------------------------------
gravity_terms <- c("log(dist_km)" = "Log distance", "contig" = "Shared border",
                   "comlang" = "Common language", "rta" = "Trade agreement")

# Guard: return NULL if the model can run, else a plain message.
# The model needs enough countries, and each 0/1 regressor must take both values.
# n_cty is the number of selected countries.
gravity_guard <- function(trade_f, n_cty, min_countries = 6) {
  if (n_cty < min_countries)
    return(sprintf("Gravity model needs at least %d countries; the filter keeps %d. Add countries.",
                   min_countries, n_cty))
  flat <- Filter(function(v) length(unique(trade_f[[v]])) < 2, c("contig", "comlang", "rta"))
  if (length(flat))
    return(sprintf("Gravity model cannot run: %s does not vary across country pairs in this filter. Add countries from another bloc.",
                   paste(flat, collapse = ", ")))
  NULL
}

# PPML with exporter-year and importer-year fixed effects, errors clustered by
# country pair: the same model as code/01_gravity.R.
# Returns a list: coefs (table), n_obs, n_pairs; or a list with only a message.
# The coefficients are associations, not causal effects.
fit_gravity <- function(trade_f, n_cty) {
  msg <- gravity_guard(trade_f, n_cty)
  if (!is.null(msg)) return(list(message = msg))
  trade_f$pair <- paste(trade_f$exporter, trade_f$importer, sep = "_")
  model <- tryCatch(
    fepois(trade_usd ~ log(dist_km) + contig + comlang + rta |
             exporter^year + importer^year,
           data = trade_f, cluster = ~ pair, notes = FALSE),
    error = function(e) NULL)
  # After the fit: fixest drops a regressor it cannot estimate; treat that as a failure
  if (is.null(model) || length(coef(model)) != 4)
    return(list(message = "Gravity model cannot estimate all four coefficients in this filter. Add countries from another bloc."))
  ct <- coeftable(model)
  coefs <- data.frame(
    term      = rownames(ct),
    label     = gravity_terms[rownames(ct)],
    estimate  = ct[, "Estimate"],
    std_error = ct[, "Std. Error"],
    p_value   = ct[, "Pr(>|z|)"],
    row.names = NULL
  )
  list(coefs = coefs, n_obs = nobs(model), n_pairs = length(unique(trade_f$pair)))
}

# Coefficient plot with 95% confidence intervals (estimate +/- 1.96 SE)
plot_gravity <- function(coefs, label) {
  lower <- coefs$estimate - 1.96 * coefs$std_error
  upper <- coefs$estimate + 1.96 * coefs$std_error
  y <- rev(seq_len(nrow(coefs)))   # first term on top
  op <- par(mar = c(4.5, 9, 4, 1)); on.exit(par(op))
  plot(coefs$estimate, y, xlim = range(c(lower, upper, 0)),
       ylim = c(0.5, nrow(coefs) + 0.5), pch = 19, yaxt = "n", ylab = "",
       xlab = "PPML coefficient (95% CI, clustered by country pair)",
       main = paste0("Gravity model of farm trade\n", label))
  segments(lower, y, upper, y, lwd = 2)
  abline(v = 0, lty = 2, col = "grey40")
  axis(2, at = y, labels = coefs$label, las = 1)
}

# Trade against distance, one point per country pair, with the gravity line.
# Points: average yearly trade of each pair in the filter, log scales.
# Line: its slope is the gravity coefficient on log distance. It goes through
# the average point. It is not a fit to these points: the model also holds
# border, language, trade agreement and the fixed effects constant.
plot_distance <- function(trade_f, coefs, label) {
  pairs <- aggregate(cbind(trade_usd, dist_km, rta) ~ exporter + importer,
                     data = trade_f, FUN = mean)
  n_zero <- sum(pairs$trade_usd == 0)
  pairs <- pairs[pairs$trade_usd > 0, ]   # log scale: leave out pairs with no trade
  if (nrow(pairs) == 0) {
    plot.new(); text(0.5, 0.5, "No trade between the selected countries."); return(invisible())
  }
  x <- pairs$dist_km
  y <- pairs$trade_usd / 1e6
  agreement <- pairs$rta > 0               # trade agreement in at least one year
  op <- par(mar = c(6, 5.5, 4, 1)); on.exit(par(op))
  plot(x, y, log = "xy", pch = 19, cex = 0.7, yaxt = "n",
       col = ifelse(agreement, "#0072B2AA", "#E69F00AA"),
       xlab = "Distance between the two countries (km, log scale)", ylab = "",
       main = paste0("Farm trade and distance\n", label))
  # Y-axis labels as plain numbers (1, 10, 100), not 1e+02
  at <- axTicks(2)
  axis(2, at = at, las = 1, cex.axis = 0.85,
       labels = format(at, big.mark = ",", scientific = FALSE, drop0trailing = TRUE, trim = TRUE))
  mtext("Average yearly farm exports (USD million, log scale)", side = 2, line = 4)
  note <- sprintf("One point per country pair; %d pairs with no trade left out.", n_zero)
  if (!is.null(coefs)) {
    slope <- coefs$estimate[coefs$term == "log(dist_km)"]
    xs <- exp(seq(log(min(x)), log(max(x)), length.out = 50))
    ys <- exp(mean(log(y)) + slope * (log(xs) - mean(log(x))))
    lines(xs, ys, lwd = 2.5)
    line_text <- sprintf("Gravity model, slope %.2f", slope)
    note <- paste0(note, "\nLine: gravity model distance coefficient, drawn through the average point.")
  } else {
    line_text <- NULL
    note <- paste0(note, "\nNo gravity line: the gravity model does not run on this filter.")
  }
  legend("bottomleft", c("Trade agreement", "No trade agreement", line_text),
         col = c("#0072B2", "#E69F00", "black"), pch = c(19, 19, NA),
         lwd = c(NA, NA, 2.5)[seq_len(2 + length(line_text))], bty = "n", cex = 0.85)
  mtext(note, side = 1, line = 4.8, cex = 0.75)
}

# ---- 3. Subsidy model (path model) -------------------------------------------
# Guard: the two regressions need enough country-years.
sem_guard <- function(support_f, min_rows = 20) {
  if (nrow(support_f) < min_rows)
    return(sprintf("Path model needs at least %d country-years; the filter keeps %d. Add countries or years.",
                   min_rows, nrow(support_f)))
  NULL
}

# The Stata model is recursive, so two OLS regressions give the same estimates:
#   ln_fert   ~ ln_subsidy             path a: subsidy -> fertiliser
#   ln_output ~ ln_subsidy + ln_fert   path c: subsidy -> output, path b: fertiliser -> output
# indirect = a * b, total = c + a * b. All in logs, so these are elasticities.
# Standard errors only for the direct paths: the indirect SE needs a delta
# method or a bootstrap. OLS SEs are about 0.3% larger than Stata's, which
# divides by n instead of n - k.
fit_sem <- function(support_f) {
  msg <- sem_guard(support_f)
  if (!is.null(msg)) return(list(message = msg))
  d <- data.frame(ln_subsidy = log(support_f$subsidy),
                  ln_fert    = log(support_f$fertiliser),
                  ln_output  = log(support_f$farm_output))
  m1 <- lm(ln_fert ~ ln_subsidy, data = d)
  m2 <- lm(ln_output ~ ln_subsidy + ln_fert, data = d)
  path_a <- coef(m1)[["ln_subsidy"]]   # subsidy -> fertiliser
  path_b <- coef(m2)[["ln_fert"]]      # fertiliser -> output
  path_c <- coef(m2)[["ln_subsidy"]]   # subsidy -> output, direct
  se <- function(m, v) sqrt(vcov(m)[v, v])
  effects <- data.frame(
    effect    = c("direct", "indirect", "total", "direct", "total", "direct"),
    path      = c(rep("subsidy -> output", 3), rep("subsidy -> fertiliser", 2),
                  "fertiliser -> output"),
    estimate  = c(path_c, path_a * path_b, path_c + path_a * path_b,
                  path_a, path_a, path_b),
    std_error = c(se(m2, "ln_subsidy"), NA, NA, se(m1, "ln_subsidy"),
                  se(m1, "ln_subsidy"), se(m2, "ln_fert"))
  )
  list(effects = effects, n_obs = nrow(d))
}


# ---- Page (UI) -----------------------------------------------------------------
# Countries grouped by bloc in the multi-select: a named list makes groups
country_choices <- lapply(split(countries, countries$bloc),
                          function(d) setNames(d$iso3, d$country))
year_range <- range(trade$year)

# One "add" button per bloc. Button ids cannot hold spaces, so number them.
bloc_buttons <- lapply(seq_along(all_blocs), function(i)
  actionButton(paste0("add_bloc_", i), all_blocs[i], class = "btn-sm btn-outline-primary"))

ui <- page_sidebar(
  title = "Farm trade and farm support",
  fillable = FALSE,   # fixed plot heights; the page scrolls on a small screen
  sidebar = sidebar(
    width = 290,
    tags$strong("Add a bloc"),
    div(style = "display: flex; flex-wrap: wrap; gap: 4px;", bloc_buttons),
    div(style = "display: flex; gap: 4px;",
        actionButton("select_all", "All", class = "btn-sm btn-outline-secondary"),
        actionButton("clear", "Clear", class = "btn-sm btn-outline-secondary")),
    selectizeInput("countries", "Countries", choices = country_choices,
                   selected = countries$iso3, multiple = TRUE),
    sliderInput("years", "Years", min = year_range[1], max = year_range[2],
                value = year_range, step = 1, sep = ""),
    actionButton("run", "Run", class = "btn-primary"),
    helpText("Results change only when you click Run.")
  ),
  textOutput("filter_used"),
  layout_columns(
    col_widths = c(7, 5),
    card(card_header("Farm trade between blocs over time"),
         plotOutput("trend", height = "460px")),
    card(card_header("Who trades with whom, last year of the filter"),
         plotOutput("heatmap", height = "460px"))
  ),
  layout_columns(
    col_widths = c(7, 5),
    card(card_header("Gravity model: coefficients with 95% CIs"),
         plotOutput("gravity_plot", height = "340px")),
    card(card_header("Gravity model: table"),
         tableOutput("gravity_table"),
         textOutput("gravity_note"))
  ),
  layout_columns(
    col_widths = c(6, 6),
    card(card_header("Farm trade and distance, with the gravity line"),
         plotOutput("distance", height = "420px")),
    card(card_header("Subsidy pass-through to farm output (path model, SYNTHETIC data)"),
         tableOutput("sem_table"),
         textOutput("sem_note"))
  )
)

# ---- Server --------------------------------------------------------------------
server <- function(input, output, session) {

  # Bloc buttons add the bloc's countries to the current selection
  lapply(seq_along(all_blocs), function(i) {
    observeEvent(input[[paste0("add_bloc_", i)]], {
      add <- countries$iso3[countries$bloc == all_blocs[i]]
      updateSelectizeInput(session, "countries", selected = union(input$countries, add))
    })
  })
  observeEvent(input$select_all,
               updateSelectizeInput(session, "countries", selected = countries$iso3))
  observeEvent(input$clear,
               updateSelectizeInput(session, "countries", selected = character(0)))

  # All computing happens here, once per click on Run.
  # ignoreNULL = FALSE: also run once on load, for the default filter.
  results <- eventReactive(input$run, {
    iso3  <- input$countries
    years <- input$years
    trade_f   <- filter_trade(trade, iso3, years)
    support_f <- filter_support(support, iso3, years)
    list(
      label = if (length(iso3) == 0) "no countries selected" else filter_label(iso3, years),
      trade_f = trade_f,
      bt    = if (nrow(trade_f) > 0) bloc_trade(trade_f) else NULL,
      grav  = fit_gravity(trade_f, length(iso3)),
      sem   = fit_sem(support_f)
    )
  }, ignoreNULL = FALSE)

  output$filter_used <- renderText(paste("Results for:", results()$label))

  # 1. Bloc charts
  output$trend <- renderPlot({
    r <- results()
    validate(need(!is.null(r$bt), "Bloc charts need at least 2 countries. Add countries."))
    plot_trend(r$bt, r$label)
  }, res = 96)
  output$heatmap <- renderPlot({
    r <- results()
    validate(need(!is.null(r$bt), "Bloc charts need at least 2 countries. Add countries."))
    plot_heatmap(r$bt, r$label)
  }, res = 96)

  # 2. Gravity model
  output$gravity_plot <- renderPlot({
    g <- results()$grav
    validate(need(is.null(g$message), g$message))
    plot_gravity(g$coefs, results()$label)
  }, res = 96)
  output$gravity_table <- renderTable({
    g <- results()$grav
    validate(need(is.null(g$message), g$message))
    data.frame(Term = g$coefs$label, Estimate = g$coefs$estimate,
               `Std. error` = g$coefs$std_error,
               `p-value` = ifelse(g$coefs$p_value < 0.001, "<0.001",
                                  sprintf("%.3f", g$coefs$p_value)),
               check.names = FALSE)
  }, digits = 3)
  output$gravity_note <- renderText({
    g <- results()$grav
    if (!is.null(g$message)) return("")
    sprintf("%d observations, %d country pairs. PPML with exporter-year and importer-year fixed effects; errors clustered by pair. Associations, not causal effects.",
            g$n_obs, g$n_pairs)
  })

  # Trade against distance: follows the filter; no line if the gravity model did not run
  output$distance <- renderPlot({
    r <- results()
    validate(need(!is.null(r$bt), "This chart needs at least 2 countries. Add countries."))
    plot_distance(r$trade_f, r$grav$coefs, r$label)
  }, res = 96)

  # 3. Path model
  output$sem_table <- renderTable({
    s <- results()$sem
    validate(need(is.null(s$message), s$message))
    data.frame(Effect = s$effects$effect, Path = s$effects$path,
               Elasticity = s$effects$estimate, `Std. error` = s$effects$std_error,
               check.names = FALSE)
  }, digits = 3, na = "")
  output$sem_note <- renderText({
    s <- results()$sem
    if (!is.null(s$message)) return("")
    sprintf("%d country-years. SYNTHETIC data: true values direct 0.10, indirect 0.24, total 0.34. Two OLS regressions give the Stata sem estimates; standard errors for direct paths only.",
            s$n_obs)
  })
}

shinyApp(ui, server)
