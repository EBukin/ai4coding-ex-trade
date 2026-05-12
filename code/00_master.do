* 00_master.do: run the Stata part of the project, in order.
*
* Run it from the project root folder (the folder that holds README.md):
*   cd "path/to/farm-trade-support"
*   do code/00_master.do
* Every path below is relative to that root folder.

version 17
clear all
set more off

* Make sure the output folders exist (no error if they already do)
capture mkdir "outputs"
capture mkdir "outputs/data"
capture mkdir "outputs/figures"
capture mkdir "outputs/tables"

* The scripts share the data in memory, so run them in this order
do "code/01_prepare.do"    // load farm support data, take logs
do "code/02_figure.do"     // scatter of output against subsidy
do "code/03_sem.do"        // path model, effects table and CSV

display as text "Stata part finished. See outputs/."
