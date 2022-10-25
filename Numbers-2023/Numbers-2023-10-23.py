import os,sys,string,time,commentjson,datetime, math
from csv import reader
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

DEBUG = True

import numpy as np

from NumberUtils import dump
from NumberUtils import DrawTex
from NumberUtils import cumulateMap
from NumberUtils import DrawDet
from NumberUtils import DrawType
from NumberUtils import makeArray

# read in a configfile
configfile = "Parameters_2022-10-23-2040.json"
if len(sys.argv) > 1:
  configfile = sys.argv[1]

shortname = configfile.replace(".json","")
if os.path.exists(configfile):
  with open(configfile,'r') as f:
    config = commentjson.load(f)
else:
  print ("no config file",configfile)
  sys.exit(0)

if not "Version" in config or config["Version"] < 5:
  print (" this code expects Version >= 2")
  sys.exit(1)

json_formatted_str = commentjson.dumps(config, indent=2)

MaxYear = config["MaxYear"]

MinYear = config["MinYear"]
Detectors = config["Detectors"]
if DEBUG:
  Detectors = ["SP","SP2","DP"]
Years = np.array(config["Years"])
if DEBUG:
  Years = Years[0:7]
shortname = shortname.replace("2040","%d"%MaxYear)
print (Years, len(Years))
size = len(Years)

Units = config["Units"]

Detectors = config["Detectors"]

print (Detectors)

CombinedDetectors = config["CombinedDetectors"]

DetectorParameters = list(config["SP"].keys())
if "Comment" in DetectorParameters:
    DetectorParameters.remove("Comment")

TapeLifetimes = config["TapeLifetimes"]

DiskLifetimes = config["DiskLifetimes"]

TapeCopies = config["TapeCopies"]

DiskCopies = config["DiskCopies"]

# this is how far you go back each time you reprocess reco.
Reprocess = config["Reprocess"]

PerYear = config["PerYear"]

StorageTypes = list(TapeCopies.keys())

# plot config
DetColors=config["DetColors"]
DetLines = config["DetLines"]
TypeColors=config["TypeColors"]
TypeLines = config["TypeLines"]

PatternFraction = config["PatternFraction"]

dofirst = ["Events","Test","Sim Events"]

# read in the raw information

Inputs = {}
for det in Detectors:
  Inputs[det]={}
  for type in dofirst:
      Inputs[det][type]={}
      for year in Years:
          Inputs[det][type][year] = float(config[det][type][year-Years[0]])

# fill in other useful arrays
for det in Detectors:
  if DEBUG: print ("Events",det,Inputs[det]["Events"])
  for key in DetectorParameters:
    # skip the ones already done
    if key in dofirst:
      continue
    # sim has its own configuration
    # print ("this is the key",det,key)
    if not "Sim" in key:
      if key in ["CPU","Reco"]:  # if doing reco, do over previous events using memory
            Inputs[det][key] = cumulateMap(Years,Inputs[det]["Events"],Reprocess[det])
            for year in Years:
                Inputs[det][key][year] *= config[det][key]
      else:
        if key == "Raw":
            Inputs[det][key] ={}
            for year in Years:
                Inputs[det][key][year] = Inputs[det]["Events"][year]*config[det][key]
        else:
            continue
    else:
        Inputs[det][key] ={}
        for year in Years:
            Inputs[det][key][year]=Inputs[det]["Sim Events"][year]*config[det][key]

    
if PerYear["Reco"]!=PerYear["CPU"]:
    print ("Data growth has to match reprocessing cycles/year")
    PerYear["Reco"] = PerYear["CPU"]
if PerYear["Sim"]!=PerYear["Sim-CPU"]:
    print ("Sim growth has to match reprocessing cycles/year")
    PerYear["Sim"] = PerYear["Sim-CPU"]

Data = {}
dump = open("dump.txt",'w')
#print (Inputs.keys())
fields = list(Inputs["ND"].keys())
for dtype in fields:
  Data[dtype] = {}
  for det in Inputs.keys():
    Data[dtype][det] = {}
    # this allows you to, say, do 2 passes of reco/year
    for year in Years:
        Data[dtype][det][year] = Inputs[det][dtype][year] * float(PerYear[dtype])
    # compensate for nominal units being millions and TB or singles and MB
    if Units[dtype] == "PB":
        for year in Years:
            Data[dtype][det][year] *= 0.001
    ds = "data %s %s %f\n"%(dtype,det,Data[dtype][det][2022])
    dump.write(ds)
PlotYears = []
for i in range(MinYear,MaxYear-1):
    PlotYears.append(i)
PlotYears = Years

DrawDet(shortname,"Events",PlotYears,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"CPU",Years,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"Raw",Years,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"Test",Years,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"Sim Events",Years,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"Sim",Years,Data,Inputs.keys(),Units,DetColors,DetLines)
DrawDet(shortname,"Reco",Years,Data,Inputs.keys(),Units,DetColors,DetLines)


