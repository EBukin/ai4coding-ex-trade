* 01_prepare.do: load the farm support data and take logs.
* Run through code/stata/00_master.do from the project root.
*
* NOTE: farm_support.csv is SYNTHETIC (made up). See data/clean/README.md.

* Country list, kept as a temporary file so we can check the country codes
import delimited "data/clean/countries.csv", clear varnames(1) ///
    stringcols(_all)
tempfile countries
save `countries'

* Farm support panel: one row per country and year
import delimited "data/clean/farm_support.csv", clear varnames(1)
isid iso3 year                          // one row per country-year
assert subsidy > 0 & fertiliser > 0 & farm_output > 0 ///
    & !missing(subsidy, fertiliser, farm_output)  // logs need positives

* Every country code must appear in the country list
merge m:1 iso3 using `countries', keep(master match)
tab _merge
assert _merge == 3
drop _merge

* Elasticities come from a model in natural logs
generate ln_subsidy = ln(subsidy)
generate ln_fert    = ln(fertiliser)
generate ln_output  = ln(farm_output)

label variable ln_subsidy "Log farm subsidy (USD million)"
label variable ln_fert    "Log fertiliser use (tonnes)"
label variable ln_output  "Log farm output (USD million)"

summarize ln_subsidy ln_fert ln_output
