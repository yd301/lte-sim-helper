# LTE-Sim Helper #

## Description ##
lte-sim-helper is a python program designed to facilitate the simulation process for LTE-Sim simulator.


## Motivation ##
The simulation process in LTE-Sim is not straighforward. The users should pass a great number of parameters as arguments of the function that implements the scenario. Besides, some parameters are "hard coded" as a value of a given variable in the code. For each change in the value a new re-compilation is needed.

The results of the simulation can be processed by a bunch of shell scripts that follow the LTE-Sim oficial release. However, for each different simulation, the user must make a set of changes in several files to get correct results. Besides, these scripts use only one CPU of the machine and it does not take advantage of the multi-core processors present in the major part of the current machines.

## Key Features ##

  * Use of multiples CPUs to run simulations and to process results;
  * Simulation parameters are set through a configuration file. This approach centralizes the parameters in one place and facilitates the process of building a new scenario.
  * A new scenario template is proposed. In this new template the parameters are gotten from a config file and there is not necessity of re-compilation of the code when a value of a given parameter is changed.


## Drawbacks ##
  * To use LTE-Sim Helper you have to adapt you current scenarios to the new template. This is not difficult.


## Limitations ##
  * LTE-Sim Helper is under development. So, it does not have some functionalities of the original scripts, e.g., the automatic plot process.