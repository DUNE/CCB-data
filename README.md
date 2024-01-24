# Code used for DUNE computing resource models 

Copyright © 2023 FERMI NATIONAL ACCELERATOR LABORATORY

This repository, and all software contained within, is licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
Copyright is granted to FERMI NATIONAL ACCELERATOR LABORATORY on behalf of the Deep Underground Neutrino Experiment (DUNE). Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

Primary authors: Heidi Schellman, Mike Kirby

# CCB 2023/24 simulations/usage

The code for the CCB in Dec 2023 is on branch CCB-Feb24 in subdirectory Numbers-2024/Dec23

New usage information is in subdirectory usage/

usage requires downloading a csv file by hand from the link at the top that dumps a fifemon summary and then running either monthly.py or monthly.ipynb

# 2024 simulations

The code for 2024 is in subdirectory Numbers-2024

* Uses a jupyter notebook (versioned by date for history) 
  
  - 2024-01-21-HMS.ipynb is the latest version.  It has fixed extension algorithms and can now read in the timeline from a csv file instead of those long lists of years. 
  
  -  This implements NDLAr as a separate detector and add retention times and ratios between analysia and reco+sim times for detectors. 

* Which reads a json file (versioned by date for history)
  
  -  Example: DOE23-NDLAr_2023-06-24-2040.json
  -     DOE23-NDLAr_2023-11-03-2040.json - has ability to turn of MWC
  - LongTerm_2024-01-23-2040.json  is a new model Kirby started that includes TP, Calib, and various physics types
  - NearTerm_2024-01-23-2040.json is the old model used in Dec 23 
  
LongTerm is still under development while NearTerm is similar to the 2023 models. 

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
   
4. open NearTerm_2024-01-23-2040.json in an editor - save your own version 

5. It will point to a Timeline file: NearTerm_2024-01-23-2040_timeline.json - that has year by year event and Test stream volumes in cvs format.  Much better for getting things in the right year.  If you comment out the "Timeline" line in the  top level json file, the code will use the old method with the lists in the top level json file. 

If you want your own version, make your own top level json file and then have it point to a new csv file. 

6. `jupyter-lab 2024-01-21-HMS.ipynb &` will create a webpage with the notebook 
   
7. edit the notebook to point to your version of the json file.  NearTerm_2024-01-23-2040.json is an example

8. you can then edit the json file and iterate.  Plots will appear in the notebook and in a subdirectory named after your json file. 


