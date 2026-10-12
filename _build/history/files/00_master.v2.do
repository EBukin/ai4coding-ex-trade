* 00_master.do: run the Stata part of the project, in order.
*
* Run it from the project root folder (the folder that holds README.md):
*   cd "path/to/farm-trade-support"
*   do code/00_master.do

version 17
clear all
set more off

* The scripts share the data in memory, so run them in this order
do "code/01_prepare.do"    // load farm support data, take logs
do "code/02_sem.do"        // path model and effects
