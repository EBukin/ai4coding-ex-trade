# R dashboard

A Shiny app that shows the three parts of the project for any choice of countries and years: the bloc charts, the PPML gravity model, the subsidy path model, and trade against distance.

- Live version: <https://datanalytics.worldbank.org/ai4coding-ex2-3-r-shiny/>. It was deployed on 2026-10-12 from an earlier copy of the data with 27 countries, so its numbers differ from the files here.
- The app reads `data/clean/` and writes nothing.

## Files

- `app.R`: the whole app: analysis functions, page and server.

## What you need

- R with `shiny`, `bslib` and `fixest`:

```r
install.packages(c("shiny", "bslib", "fixest"))
```

- Tested with R 4.5.3, shiny 1.13.0, bslib 0.11.0, fixest 0.13.2.

## Run it

- In Positron or VS Code with the Shiny extension: open `code/r-shiny/app.R` and click **Run Shiny App**.
- Or in the R console, from the project root: `shiny::runApp("code/r-shiny")`. The app opens in your browser.
- Pick countries and years in the left sidebar, then click **Run**. Nothing changes until you click **Run**.
- Stop it with **Stop Shiny App**, or `Esc` in the R console (`Ctrl+C` in a terminal).
- After you change `app.R`, stop the app and start it again.

## Layout

- One page, for economists, on a laptop screen. Main use: compare blocs.
- Left sidebar:
  - One button per bloc. It adds the bloc to the selection; it does not replace it, because no single bloc can run the gravity model on its own.
  - **All** and **Clear**.
  - Countries: a multi-select grouped by bloc. All countries at the start.
  - Years: a slider over the years in the data.
  - **Run**.
- Main area:
  - A line that names the filter the results use.
  - Row 1: bloc trend chart, one panel per exporting bloc; bloc heatmap for the last year of the filter.
  - Row 2: gravity coefficient plot with 95% confidence intervals; gravity table with observations and country pairs.
  - Row 3: trade against distance, one point per country pair, with the gravity line; subsidy path model table.

## Rules on the page

- Bloc totals cover the selected countries only.
- The gravity model needs at least 6 countries, and border, language and trade agreement must each vary across pairs. If not, the page shows a plain message.
- The path model needs at least 20 country-years.
- The path model is the Stata model estimated as two OLS regressions: the same estimates, standard errors about 0.3% larger, and none for the indirect and total effects.
- The gravity coefficients are associations, not causal effects.
- The subsidy data are synthetic.
