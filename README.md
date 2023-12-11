# Code used for DUNE computing resource models 

Copyright © 2023 FERMI NATIONAL ACCELERATOR LABORATORY

This repository, and all software contained within, is licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
Copyright is granted to FERMI NATIONAL ACCELERATOR LABORATORY on behalf of the Deep Underground Neutrino Experiment (DUNE). Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

Primary authors: Heidi Schellman, Mike Kirby

# CCB 2023/24 simulations/usage

The code for the CCB in Dec 2023 is on branch CCB-Dec23 in subdirectory Numbers-2024/

New usage information is in subdirectory usage/

usage requires downloading a csv file by hand from the link at the top that dumps a fifemon summary and then running either monthly.py or monthly.ipynb

# 2024 simulations

The code for 2024 is in subdirectory Numbers-2024

* Uses a jupyter notebook (versioned by date for history) 
  
  -  Example: 2023-06-24.ipynb
  -  LATEST: 2023-11-07.ipynb, mainly added a wall-time plot
 
  -  This implements NDLAr as a separate detector and add retention times and ratios between analysia and reco+sim times for detectors. 

* Which reads a json file (versioned by date for history)
  
  -  Example: DOE23-NDLAr_2023-06-24-2040.json
  -  LATEST: DOE23-NDLAr_2023-11-03-2040.json - has ability to turn of MWC

* The json file has parameters for particular DUNE detectors and running periods. 

* Needs are parametrized by year starting in 2018.  Most year by years are set by

  - 2018-2027
  - 2028-2037
  - 2038-2040

just so  you can figure out which year is which.  

* Units are specified in the json file but are generally PB, MHr, Walltime.  

The notebook uses NumberUtils.py which does things like make plots, calculate cumulative use over multiple years, etc. 

# To run the code:

1. Install jupyter and matplotlib and the DUNE/dune_plot_style code (requires running the setup script to install the dune_plot_style)

2. clone DUNE/CCB-data  - maybe make your own branch while playing around

3. `cd Numbers-2024 directory`
   
4. open DOE23-NDLAr_2023-11-03-2040.json in an editor - save your own version 

6. `jupyter-lab 2023-11-07.ipynb &` will create a webpage with the notebook 
   
7. edit the notebook to point to your version of the json file.  DOE23-NDLAr_2023-11-03-2040.json is an example

8. you can then edit the json file and iterate.  Plots will appear in the notebook and in a subdirectory named after your json file. 


