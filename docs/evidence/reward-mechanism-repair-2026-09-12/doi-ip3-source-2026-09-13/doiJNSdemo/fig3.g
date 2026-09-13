//genesis
// This simulation generates the time courses of 
// Ca2+, IP3, open IP3Rs, Ca2+ stores, and inactivated IP3Rs
// with PF and/or CF inputs.

include DoiCaModel.g


// Define clocks.
float normdt = 1e-06
float plotdt = 0.001
MAXTIME = 2.0001

setclock 0 {normdt}
setclock 1 {normdt}
setclock 3 {plotdt}

// PF alone

setfield /kinetics/Influx/CF input 100          /* CF input starts at -100 sec */
echo "Running simulation of fig.3, PF alone"
step {MAXTIME} -time

do_save_named_plot /graphs/conc2/Ca.Co             {"./simresult/fig3/PFalone_Ca.plot"}
do_save_named_plot /graphs/conc1/IP3_spine.Co      {"./simresult/fig3/PFalone_IP3.plot"}
do_save_named_plot /moregraphs/conc3/IP3R-open.Co  {"./simresult/fig3/PFalone_openIP3R.plot"}
do_save_named_plot /moregraphs/conc4/CaStore.Co    {"./simresult/fig3/PFalone_CaStore.plot"}
do_save_named_plot /moregraphs/conc3/IP3R_inact.Co {"./simresult/fig3/PFalone_inactIP3R.plot"}

setfield /kinetics/Influx/CF input -0.6
reset


// CF alone

setfield /kinetics/mGluR/100Hz5Glu input 100
setfield /kinetics/Influx/100Hz5PFCa input 100
echo "Running simulation of fig.3, CF alone"
step {MAXTIME} -time

do_save_named_plot /graphs/conc2/Ca.Co             {"./simresult/fig3/CFalone_Ca.plot"}
do_save_named_plot /graphs/conc1/IP3_spine.Co      {"./simresult/fig3/CFalone_IP3.plot"}
do_save_named_plot /moregraphs/conc3/IP3R-open.Co  {"./simresult/fig3/CFalone_openIP3R.plot"}
do_save_named_plot /moregraphs/conc4/CaStore.Co    {"./simresult/fig3/CFalone_CaStore.plot"}
do_save_named_plot /moregraphs/conc3/IP3R_inact.Co {"./simresult/fig3/CFalone_inactIP3R.plot"}

setfield /kinetics/mGluR/100Hz5Glu input 0
setfield /kinetics/Influx/100Hz5PFCa input 0
reset

// Conjunctive PF and CF

echo "Running simulation of fig.3, conjunctive PF and CF"
step {MAXTIME} -time

do_save_named_plot /graphs/conc2/Ca.Co             {"./simresult/fig3/PFCF_Ca.plot"}
do_save_named_plot /graphs/conc1/IP3_spine.Co      {"./simresult/fig3/PFCF_IP3.plot"}
do_save_named_plot /moregraphs/conc3/IP3R-open.Co  {"./simresult/fig3/PFCF_openIP3R.plot"}
do_save_named_plot /moregraphs/conc4/CaStore.Co    {"./simresult/fig3/PFCF_CaStore.plot"}
do_save_named_plot /moregraphs/conc3/IP3R_inact.Co {"./simresult/fig3/PFCF_inactIP3R.plot"}

echo "Simulation has done!"
echo "Type 'quit' to exit GENESIS/kinetikit"





