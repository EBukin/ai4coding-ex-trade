* 02_sem.do: path model of how subsidy reaches farm output.
* Needs the data from 01_prepare.do. Run through code/00_master.do.
*
* Two equations, estimated together:
*   ln_fert   <- ln_subsidy           subsidy changes fertiliser use
*   ln_output <- ln_subsidy ln_fert   subsidy and fertiliser change output
* All variables are in logs, so coefficients are elasticities.

sem (ln_output <- ln_subsidy ln_fert) (ln_fert <- ln_subsidy), nolog

* Direct, indirect (through fertiliser) and total effects
estat teffects
