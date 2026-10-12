* 02_figure.do: scatter of log farm output against log subsidy.
* Needs the data from 01_prepare.do. Run through code/stata/00_master.do.
*
* The slope of the fitted line is the total elasticity of output with
* respect to subsidy. 03_sem.do splits it into direct and indirect parts.

* Stop with a clear message if the prepared data are not in memory
capture confirm variable ln_output ln_subsidy
if _rc {
    display as error "Run code/stata/01_prepare.do first (or code/stata/00_master.do)."
    exit 111
}

twoway (scatter ln_output ln_subsidy, msize(small) mcolor(navy%40)) ///
       (lfit ln_output ln_subsidy, lcolor(cranberry) lwidth(medthick)), ///
    title("Farm output and farm subsidy, in logs") ///
    xtitle("Log farm subsidy (USD million)") ///
    ytitle("Log farm output (USD million)") ///
    note("Synthetic data: 46 countries, 2000-2019. Line: linear fit.") ///
    legend(off) scheme(s2color)

graph export "outputs/figures/sem_scatter.png", replace width(1600)
graph close
