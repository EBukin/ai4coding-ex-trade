* 03_sem.do: path model of how subsidy reaches farm output.
* Needs the data from 01_prepare.do. Run through code/stata/00_master.do.
*
* Two equations, estimated together:
*   ln_fert   <- ln_subsidy           subsidy changes fertiliser use
*   ln_output <- ln_subsidy ln_fert   subsidy and fertiliser change output
* All variables are in logs, so coefficients are elasticities.

* Stop with a clear message if the prepared data are not in memory
capture confirm variable ln_output ln_subsidy ln_fert
if _rc {
    display as error "Run code/stata/01_prepare.do first (or code/stata/00_master.do)."
    exit 111
}

sem (ln_output <- ln_subsidy ln_fert) (ln_fert <- ln_subsidy), nolog

* Direct, indirect (through fertiliser) and total effects
estat teffects

* Copy the results now: the next r-class command overwrites r()
foreach e in direct indirect total {
    matrix b_`e' = r(`e')
    matrix V_`e' = r(V_`e')
}

* add_row writes one effect to the CSV and to the Excel sheet.
*   effect: direct, indirect or total
*   coef:   column name in the matrices, as equation:variable
*   path:   readable label;  row: Excel row number
capture program drop add_row
program add_row
    args effect coef path row
    local j   = colnumb(b_`effect', "`coef'")
    local est = b_`effect'[1, `j']
    local se  = sqrt(V_`effect'[`j', `j'])
    file write csv "`effect',`path'," ///
        (strtrim(strofreal(`est', "%12.6f"))) "," ///
        (strtrim(strofreal(`se', "%12.6f"))) _n
    putexcel A`row' = "`effect'" B`row' = "`path'"
    putexcel C`row' = `est' D`row' = `se', nformat("0.000")
end

* Excel table, written with putexcel
putexcel set "outputs/tables/sem_elasticities.xlsx", replace open ///
    sheet("sem_effects")
putexcel A1 = "Effects of farm subsidy on farm output (elasticities)"
putexcel A2 = "SYNTHETIC data. Model: sem, effects from estat teffects."
putexcel A3 = "effect" B3 = "path" C3 = "estimate" D3 = "std_error"

* Tidy CSV, same rows, exact header
capture file close csv    // close a handle left open by a failed run
file open csv using "outputs/data/sem_effects.csv", write replace text
file write csv "effect,path,estimate,std_error" _n

add_row direct   ln_output:ln_subsidy "subsidy -> output"     4
add_row indirect ln_output:ln_subsidy "subsidy -> output"     5
add_row total    ln_output:ln_subsidy "subsidy -> output"     6
add_row direct   ln_fert:ln_subsidy   "subsidy -> fertiliser" 7
add_row total    ln_fert:ln_subsidy   "subsidy -> fertiliser" 8
add_row direct   ln_output:ln_fert    "fertiliser -> output"  9

file close csv
putexcel A11 = "True values used to make the data: direct 0.10, indirect 0.24, total 0.34."
putexcel save
