# How to install #

  * Install Python Numpy. For Ubuntu users just type in the command line:
> > sudo apt-get install python-numpy
  * Untar the file _lte-sim-helper-X-tar.gz_ (where X indicate the version).

  * Choose a place for the files _lte-sim-helper-X.py_ and _setup-X.cfg_. It can be the root folder of LTE-Sim.

  * Make the file _lte-sim-helper-X.py_ executable.

  * Copy the files _single-cell-with-interference-from-file-X.h_ and _multi-cell-from-file-X.h_ to folder /src/scenarios/. These scenarios have the ability for reading the parameters from setup-X.cfg.

  * Open the file _LTE-Sim.cpp_ and add the following #include statements:

```
#include "scenarios/single-cell-with-interference-from-file-X.h"
#include "scenarios/multi-cell-from-file-X.h"
```

  * In _LTE-Sim.cpp_ add the following if statement to the if else chain of this file:

```
if (strcmp(argv[1], "SCWIFF")==0)
  {
    int nbUE = atoi(argv[2]);
    string sched_type = argv[3];
    int seed = atoi(argv[4]);
    string path = argv[5];
    SingleCellWithInterFromFile (nbUE, sched_type, seed, path);
}
if (strcmp(argv[1], "MCFF")==0)
  {
    int nbUE = atoi(argv[2]);
    string sched_type = argv[3];
    int seed = atoi(argv[4]);
    string path = argv[5];
    MultiCellFromFile (nbUE, sched_type, seed, path);
}
```

  * Compile the code. Everything should be ok.

# How to run #

To run LTE-Sim Helper you have to set the parameters of the simulation.

  * Open file setup-X.cfg and set the parameters of your simulation. Pay special attention in fields LTE\_SIM\_DIR and SAVE\_DIR. If these fields are set with wrong paths the simulation will not succeed. Save the file.
  * Run lte-sim-helper-X.py in the terminal:


> ./lte-sim-helper-X.py