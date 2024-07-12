#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
print(sys.executable)


# In[ ]:


# code to generate yearly summaries of DUNE data volumes from input parameters
# rewritten from the version in the CDR - mainly by using maps of years instead of arrays to make it clearer what is in each year.
# HMS 2022-10-23

# if you have json problems, run the program ../strip.py on your file to take off comments
# and then test using https://jsonlint.com
#import numberutils

import os,commentjson

from csv import reader
#import matplotlib.pyplot as plt
#import matplotlib.colors as mcolors

DEBUG = True
DRAW = False
import numpy as np
#import scipy
import dunestyle.matplotlib as dunestyle

from NumberUtils import dump
from NumberUtils import DrawTex
from NumberUtils import cumulateMap
from NumberUtils import DrawDet
from NumberUtils import DrawType
from NumberUtils import makeArray
from NumberUtils import ToCSV1
from NumberUtils import ToCSV2
from NumberUtils import SumOver1
from NumberUtils import SumOver2
from NumberUtils import TableTex
from NumberUtils import BothTex
from NumberUtils import extendMap
from NumberUtils import makeParameter

from DataHolder import DataHolder


# In[ ]:


# how many histograms to draw in multi-hist plots
N_HISTS = 8   # exhibits all the colors in the Okabe-Ito cycler


# # specify the json file here.  Will create a subdirectory for plots with a similar name

# ## 

# "Tex"# read in a configfile
# #configfilename = "Parameters_2022-11-21-2040.json"
# 
# #configfilename = "DOE23-NDLAr_2023-11-03-2040b.json"
# #configfilename = "DOE23-NDLAr_2023-12-11-2040.json"  # increase sim for ND

# In[ ]:


configfilename = "NearTerm_2024-07-10-2040.json"
#if len(sys.argv) > 1:
#  configfile = sys.argv[1]



shortname = configfilename.replace(".json","")
if os.path.exists(configfilename):
    with open(configfilename,'r') as f:
        #x = f.read()
        #print (x[6000:6960])
        config = commentjson.load(f)
else:
    print ("no config file",configfilename)
    sys.exit(0)

if not "Version" in config or config["Version"] < 20:
    print (" this code expects Version >= 20")
    sys.exit(1)






MWCWeight = config["MWCWeight"] # do we weight cores by available memory? 
MaxYear = config["MaxYear"]
MWCstring = "_noMWC"
if MWCWeight: MWCstring=""
#config["filename"] = configfilename.replace("_","\_")
config["filename"] = configfilename
MinYear = config["MinYear"]
Detectors = config["Detectors"]
if DEBUG:
    Detectors = ["SP","PDHD","DP"]
#HMS Years = np.array(config["Years"])
Years = config["Years"]
#if DEBUG:
#  Years = Years[0:7]

shortname = shortname.replace("2040","%d"%MaxYear)+MWCstring
dirname = shortname
if not os.path.exists(dirname):
    os.mkdir(dirname)
shortname = dirname+"/"+dirname
# make a tex output file
texfilename = dirname+".tex"
texfile = open(texfilename,'w')
tablefile = open(os.path.join(dirname,"tables.tex"),'w')
#texfile.write("\\input{Header.tex}\n")



size = len(Years)

Units = config["Units"]

RequestYear=2024
if "RequestYear" in config:
    RequestYear= config["RequestYear"]

if not MWCWeight: 
    print ("remove MWC")
    for type in Units.keys():
        Units[type] = Units[type].replace("MWC-","")
        Units[type] = Units[type].replace("Memory weighted ","")
        Units[type] = Units[type].replace("Memory Weighted ","")
    print ("Units", Units)
        
Formats = config["Formats"]

Detectors = config["Detectors"]

DataTypes = config["DataTypes"]
NativeTypes = config["NativeTypes"]
Resources = config["Resources"]
Locations = config["Locations"]

Cap = config["Cap"]

BaseMemory = config["Base-Memory"]

if DEBUG:
    Detectors = ["SP","PDHD","DP"]

print (Detectors)

CombinedDetectors = config["CombinedDetectors"]

DetectorParameters = list(config["SP"].keys())

print ("Parameters",DetectorParameters)


if "Comment" in DetectorParameters:
    DetectorParameters.remove("Comment")

TapeLifetimes = config["TapeLifetimes"]

DiskLifetimes = config["DiskLifetimes"]

TapeCopies = config["TapeCopies"]

DiskCopies = config["DiskCopies"]

# this is how far you go back each time you reprocess reco.
Reprocess = config["Reprocess"]

AnalysisExtend = config["AnalysisExtend"]

PerYear = config["PerYear"]

StorageTypes = list(TapeCopies.keys())

print (StorageTypes)
# plot config
DetColors=config["DetColors"]
DetLines = config["DetLines"]
TypeColors=config["TypeColors"]
TypeLines = config["TypeLines"]

PatternFraction = config["PatternFraction"]

SplitsYear = config["SplitsYear"]
SplitsEarly = config["SplitsEarly"]
SplitsLater = config["SplitsLater"]

Explain = config["Explain"]
Explain["filename"] = "Input configuration file"

holder = DataHolder(config)
csvname = configfilename.replace(".json",".csv")
csvData = holder.csvDump(csvname)
holder.jsonDump(configfilename.replace(".json","safe.json"))
#print (csvData)
#sys.exit(1)
 

holder.sumAcross("Detectors",Detectors,"Total")
holder.sumAcross("DataTypes",DataTypes,"Total")
holder.sumAcross("Locations",Locations,"Total")

# diskactual = config["Actual"]["diskactual"]
# tapeactual = config["Actual"]["tapeactual"]
# wallactual = config["Actual"]["wallactual"]
# efficiency = config["Cores"]["Efficiency"]


# In[ ]:


# Output some text that explains your parameters


# In[ ]:


for f in Explain.keys():

    field = "{\\tt %s:} %s = {\\tt %s} \\\\\n"%(f,Explain[f], config[f])
    field = field.replace("_","\_")
    tablefile.write(field)
    print (Explain[f])


# # Change from config - which goes 0-N to real year indices = 2018...

# In[ ]:



print ("Detector Parameters",DetectorParameters)
# read in the raw information

# Inputs = {}
# timeline = open("timeline.csv",'w')
# timeline.write("detector, datatype ")
# for year in Years:
#     timeline.write(", %d"%year)
# timeline.write("\n")

# for det in Detectors:
#     Inputs[det]={}
#     for type in dofirst:
#         Inputs[det][type]={}
#         if DEBUG: print (det,type,config[det][type])
#         timeline.write( "%s, %s"%(det,type))
#         for year in Years:
#             Inputs[det][type][year] = float(config[det][type][year-Years[0]])
#             timeline.write(", %f"%Inputs[det][type][year])
#         timeline.write("\n")
#         if DEBUG: print ("old", det,type,Inputs[det][type])
        

# timeline.close()


# # # Read in from file instead

# # In[ ]:


# if "Timeline" in config:
#     print ("Timeline from ", config["Timeline"])
#     if not os.path.exists(config["Timeline"]):
#         print ("timeline file ", config["Timeline"]," does not exist:")
        
    
#     Inputs = {}
#     counter = 0 
#     with open(config["Timeline"], newline='') as csvfile:
#         data = reader(csvfile)
#         for row in data:
#             if counter == 0: 
#                 counter = 1
#                 continue
#             if DEBUG: print (row)
#             det = row[0].strip()
#             if det not in Inputs: 
#                 Inputs[det]={}
#             type = row[1].strip()
#             if type not in  Inputs[det]:
#                 Inputs[det][type]={}
#             for year in Years:
                
#                 #print ("test",row[year - Years[0]+2])
#                 Inputs[det][type][year] = float(row[year - Years[0]+2])
#             if DEBUG: print ("new",det,type,Inputs[det][type])
#             # print (list(Inputs[det].keys()))
#     csvfile.close()
            
# # for det in Inputs:
# #     print (list(Inputs[det].keys()))  


# # Take the raw # of events/year and use cumulate to emulate reprocessing for data.  Then build CPU estimates.



# for det in Detectors:
#     if DEBUG: print ("Events",det,Inputs[det]["Events"])
#     #print ("see it", det,Inputs[det].keys())
    
#     if not MWCWeight:
#         if DEBUG: print ("memory check",MWCWeight,config[det]["Reco-Memory"],config[det]["Sim-Memory"])
#         if DEBUG: print ("disable MWCWeight")
    
#         config[det]["Reco-Memory"]=BaseMemory
#         config[det]["Sim-Memory"]=BaseMemory
#     if DEBUG: print ("memory check",MWCWeight,config[det]["Reco-Memory"],config[det]["Sim-Memory"])


# In[ ]:


# fill in other useful arrays


for detector in Detectors:
    print ("--------------- raw-storage ------------------")

    # first events, which have to be stored. 
    # Make "dummy" locations in to "Store" scled by config[detector][type]
    for datatype in config["NativeTypes"]:
        for resource in ["Store"]:
            for location in ["ALL"]:
                if holder.hasTag(detector,datatype,"dummy",location):
                    holder.printByTag(holder.tag(detector,datatype,"dummy",location))
                    factor = 1
                    if datatype == "Events":
                        factor = config[detector]["Raw-Store"]
                    if datatype == "Sim-Events":
                        factor = config[detector]["Sim-Store"]
                    # TP and Test are already in units of GB
                    if DEBUG: print ("storage",detector,datatype,resource,location,factor)
                    newtag = holder.scale(detector,datatype,"dummy",location,{"Resources":resource},factor)
                    holder.printByTag(newtag)
                else:
                    print ("could not find", detector,datatype,resource,location)

    # here you need to code reconstruction effects on all resources. 

    

    print ("---------------  makereco ------------------") 
    for datatype in ["Reco-Data","Sim"]:
        input = "Events"
        # Reco gets reprocessed so has a special cumulation
        for resource in ["CPU","GPU","Store"]:
            for location in ["ALL"]:
                if holder.hasTag(detector,input,"dummy",location):
                    holder.printByTag(holder.tag(detector,input,resource,location))                 
                    factor = config[detector][datatype+"-"+resource]
                    if datatype == "Reco-Data":
                        factor = config[detector]["Reco-Data-"+resource]*Reprocess[detector]*PerYear["Reco-Data-"+resource]
                        input = "Events"
                    if datatype == "Sim":
                        factor = config[detector]["Sim-"+resource]*PerYear["Sim-"+resource]
                        input = "Sim-Events"
                        # do two transforms to change both datatype and label. 
                    newtag = holder.cumulateMe(detector,input,"dummy",location,{"Resources":resource,"DataTypes":datatype},factor)          
                    # extend Recodata. 
                    if DEBUG:
                        print ("Try to extend", detector,datatype,resource,location)
                    if datatype in ["Reco-Data","Sim"]:
                        newtag = holder.extendMe(detector,datatype,resource,location,{"DataTypes":datatype},AnalysisExtend)
                    holder.printByTag(newtag)

holder.csvDump("after-reco.csv")
    
#     for key in DetectorParameters:
        
#         #print(key,det)
#         # skip the ones already done
#         if key in dofirst:
#             continue
        
#         # sim has its own configuration
#         # print ("this is the key",det,key)
        
#         if key in ["Reco-Data-CPU","Reco-Data-GPU","Reco-Data-Store"]:  # if doing reco, do over previous events using memory
#             Inputs[det][key] = cumulateMap(Years,Inputs[det]["Events"],Reprocess[det])
#             for year in Years:
#                 Inputs[det][key][year] *= config[det][key]
                
# #             if key == "Reco-Data-Store":
# #                 print ("extend reco data",det,key,AnalysisExtend)
# #                 Inputs[det][key] = extendMap(Years,Inputs[det][key],AnalysisExtend,key)
            
#             if key == "Reco-Data-CPU" and MWCWeight:
#                 if DEBUG: print ("fix the memory",config[det]["Reco-Memory"]/BaseMemory)
#                 for year in Years:
#                     Inputs[det][key][year] *= (config[det]["Reco-Memory"]/BaseMemory)
#                 if DEBUG: print ("reco-data-cpu",det, Inputs[det][key])
#             continue
        
            
#         if key == "Raw-Store":
#             Inputs[det][key] ={}
#             if DEBUG:print (det,key)
#             for year in Years:
                
#                 if DEBUG:print (year,float(Inputs[det]["Events"][year]),(config[det][key]))
                
#                 Inputs[det][key][year] = float(Inputs[det]["Events"][year])*config[det][key]
#             continue
            
#         if key in ["Sim-Store","Sim-CPU","Sim-GPU"]:
            
#             Inputs[det][key] ={}
#             for year in Years:
#                 Inputs[det][key][year]=Inputs[det]["Sim-Events"][year]*config[det][key]
#                 if key == "Sim-CPU" and MWCWeight:
#                     Inputs[det][key][year]*=(config[det]["Sim-Memory"]/BaseMemory)
                
            
            
            
# #             if key == "Sim-Store":
# #                 #print ("got here", key)
# #                 Inputs[det][key] = extendMap(Years,Inputs[det][key],AnalysisExtend,key)
# #             continue
            
        
            
            
         # right now this uses MWC - may be ok as reading in big stuff uses memory
    # make an analysis type
    #

print ("---------------  make analysis ------------------")
for detector in Detectors:
    for resource in ["CPU"]:   
        for location in ["ALL"]:
            recoAtag = holder.scale(detector,"Reco-Data",resource,location,{"DataTypes":"Analysis-Data"},config[detector]["Analysis-CPU"]*PerYear["Analysis-CPU"])
            simAtag = holder.scale(detector,"Sim",resource,location,{"DataTypes":"Analysis-Sim"},config[detector]["Analysis-CPU"]*PerYear["Analysis-CPU"])
            
            newtags = holder.sumAcross("DataTypes",["Analysis-Data","Analysis-Sim"],"Total-Analysis")
            
            
            

holder.csvDump("after-analyze.csv")

EventTags = []
RecoCPUTags = []
for detector  in Detectors:
    EventTags.append(holder.tag(detector,"Events","dummy","ALL"))
    RecoCPUTags.append(holder.tag(detector,"Reco-Data","CPU","ALL"))


holder.Draw("Test1","Events",EventTags)
holder.Draw("Test2","Reco-Data",RecoCPUTags)

    # for datatype in ["Analysis"]:  # keep analyzing for a few years. 
    #     for resource in Resources:
    #         for location in Locations:
    #             newtag = holder.cumulateMe(detector,datatype,resource,location,"Datatypes",resource,factor)
       
    #     mc = extendMap(Years,Inputs[det]["Sim-CPU"],AnalysisExtend)
    #     if DEBUG: print ("mc",mc)
    #     for year in Years:
    #         total = data[year]
    #         total += mc[year]
    #         Inputs[det][key][year] = total *config[det]["Analysis-CPU"]  # this scales by a factor relative to reco/sim-MWC
        
    #     if DEBUG: print ("other key",det,key)



# do a little cleanup

# for det in Inputs.keys():
    
#     if "Sim-Memory" in Inputs[det]:
#         Inputs[det].pop("Sim-Memory")
#     if "Reco-Memory" in Inputs[det]:
#         Inputs[det].pop("Reco-Memory")


# In[ ]:


# make a data file which uses # of events to figure out how big samples are

if PerYear["Reco-Data-Store"]!=PerYear["Reco-Data-CPU"]:
    print ("Data growth has to match reprocessing cycles/year")
    PerYear["Reco-Data-Store"] = PerYear["Reco-Data-CPU"]
if PerYear["Sim-Store"]!=PerYear["Sim-CPU"]:
    print ("Sim growth has to match reprocessing cycles/year")
    PerYear["Sim-Store"] = PerYear["Sim-CPU"]

#Data = {}
#dump = open("dump.txt",'w')

    
#print (Inputs.keys())
# fields = config["Scales"]
# print ("fields",fields)
# for dtype in fields:
#     Data[dtype] = {}
#     if "Memory" in dtype:
#         continue
#     for det in Detectors:
        
#         # this allows you to, say, do 2 passes of reco/year
        
#         # print("makeData",dtype, det, Inputs[det][dtype][year])
#         for year in Years:
#             Data[dtype][det][year] = float(Inputs[det][dtype][year]) * float(PerYear[dtype])
#         # compensate for nominal units being millions and TB or singles and MB
#         if Units[dtype] == "PB":
#             for year in Years:
#                 Data[dtype][det][year] *= 0.001
#         ds = "data %s %s %f\n"%(dtype,det,Data[dtype][det][2022])
#         dump.write(ds)


# - impose a cap at Cap (30 PB/year if set)

# In[ ]:


# impose a cap at Cap on things derived from raw data
sys.exit(1)
dtype = "Raw-Store"

Data["Raw-Store"]["Total"] = {}
for year in Years:
    Data[dtype]["Total"][year] = 0.0
for det in Inputs.keys():

    for year in Years:
        
        Data[dtype]["Total"][year] +=  Data["Raw-Store"][det][year]
        
dtypes = ["Raw-Store"] #,"Reco-Data-CPU"]
for dtype in dtypes:
    for det in Inputs.keys():
        #print (dtype,det,2035,1.0,Data[dtype][det][2035] )
        for year in Years:
            cap = Data["Raw-Store"]["Total"][year]/Cap
           # print (dtype,det,year,cap,Data[dtype][det][year] )
            if cap > 1:
                Data[dtype][det][year] /=cap
        #print (dtype,det,2035,cap,Data[dtype][det][2035] )


# # Make a total across detectors

# In[ ]:


dtypes = ["Raw-Store","Reco-Data-Store","Sim-Store","Reco-Data-CPU","Sim-CPU","Analysis-CPU"]



for dtype in dtypes:
    Data[dtype]["Total"] ={}
    
        
    for year in Years:
        Data[dtype]["Total"][year] = 0.0
    for det in Inputs.keys():
        #if dtype != "Analysis":  # not certain what this does... I think it is leftover. 
        for year in Years:
            Data[dtype]["Total"][year]+=  Data[dtype][det][year] 
    
             
    


# In[ ]:


PlotYears = []
for i in range(MinYear,MaxYear+1):
    PlotYears.append(i)


# In[ ]:


PlotYears = []
for i in range(MinYear,MaxYear+1):
    PlotYears.append(i)
#PlotYears = Years
print ("PlotYears",PlotYears)
# draw things
things = list(Inputs.keys())+["Total"]

if DRAW:
    for stuff in ["Events","Test","Sim-Events","Raw-Store","Reco-Data-Store","Sim-Store","Reco-Data-CPU","Sim-CPU","Analysis-CPU","Reco-Data-GPU","Sim-GPU"]:
        DrawDet(shortname,stuff,PlotYears,Data,things,Units,DetColors,DetLines)

ToCSV2(shortname+"-Reco-Data-GPU","Reco-Data-GPU",PlotYears,Data,Units,Formats)
ToCSV2(shortname+"-Sim-GPU","Sim-GPU",PlotYears,Data,Units,Formats)


# In[ ]:


PlotYears = []
for i in range(MinYear,MaxYear+1):
    PlotYears.append(i)
#PlotYears = Years
print ("PlotYears",PlotYears)
# draw things
things = list(Inputs.keys())+["Total"]

print (Inputs.keys())
other = list(Inputs["ND-SAND"].keys())+["Total"]

print (other)


if DRAW:
    for stuff in ["Events","Test","Sim-Events","Raw-Store","Reco-Data-Store","Sim-Store","Reco-Data-CPU","Sim-CPU","Analysis-CPU"]:
        DrawDet(shortname,stuff,PlotYears,Data,things,Units,DetColors,DetLines)



# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


# merge protodune info

if DEBUG: print ("Data keys",Data.keys())

for dtype in Data.keys():
    if DEBUG: print ("Merge protodunes",dtype)
    det = "PDs" 
    Data[dtype][det] = {}
    for year in Years:  
        Data[dtype][det][year] = Data[dtype]["SP"][year] + Data[dtype]["DP"][year] + Data[dtype]["PDHD"][year] + Data[dtype]["PDVD"][year]

    Data[dtype].pop("SP")
    Data[dtype].pop("PDHD")
    Data[dtype].pop("DP")
    Data[dtype].pop("PDVD")
    


# In[ ]:


# merge far detector into "FDs
if "HD" in Detectors and "VD" in Detectors:
    for dtype in Data.keys():
        det = "FDs"
        print ("merge FDS",dtype)
        Data[dtype][det] =  {}
        for year in Years:  
            Data[dtype][det][year] = Data[dtype]["HD"][year] + Data[dtype]["VD"][year]
        Data[dtype].pop("HD")
        Data[dtype].pop("VD")
        
# for dtype in Data.keys():
#         det = "FDs"
#         Data[dtype][det] =  {}
#         for year in Years:  
#             Data[dtype][det][year] = 0
        
# for subdet in ["Calib","HighE","LowE","LBL","Calib","TP"]:
#     for dtype in Data.keys():
#         det = "FDs"
#         print ("merge FDS",dtype)
        
#         for year in Years:  
#             Data[dtype][det][year] += Data[dtype][subdet][year] 
#         Data[dtype].pop("subdet")


# In[ ]:


# make a total CPU category

Data["Total-CPU"]={}

for det in CombinedDetectors:
    Data["Total-CPU"][det] =  {}
    for year in Years:
        Data["Total-CPU"][det][year] = Data["Reco-Data-CPU"][det][year] + Data["Sim-CPU"][det][year] + Data["Analysis-CPU"][det][year]
    #print(det,Data["Total-CPU"][det])


# In[ ]:


# make totals across categories. 

DataTypes = list(Data.keys())

for dt in DataTypes:
    Data[dt]["Total"] = {}
    for year in Years:
        Data[dt]["Total"][year]=0.0
    for k in Data[dt].keys():
        if k == "Total":
          continue  
        for year in Years:
            Data[dt]["Total"][year] += Data[dt][k][year]
    


# In[ ]:


# and make a special data type for cores

Data["Cores"] = {}
Data["HS23"] = {}
Data["Wall"] = {}
 
MHrsPerYear = 1000000/365./24.
print ("MHrsPerYear",MHrsPerYear)
print ("total-CPU keys",Data["Total-CPU"].keys())
for k in Data["Total-CPU"].keys():
#     if "MARS" not in k :
#         efficiency = config["Cores"]["Efficiency"]
#     else:
#         efficiency = 1

    scaleTo2020 = config["Cores"]["2020Units"]
    Data["Cores"][k]={}
    Data["Wall"][k]={}
    Data["HS23"][k]={}
#    Data["WALL"][k]={}
    for year in Years:
        Data["Wall"][k][year] = Data["Total-CPU"][k][year]/scaleTo2020/efficiency
        Data["Cores"][k][year] = Data["Total-CPU"][k][year]*MHrsPerYear/scaleTo2020/efficiency
        Data["HS23"][k][year] = Data["Total-CPU"][k][year]*MHrsPerYear/scaleTo2020/efficiency*config["kHEPSPEC06PerCPU"]
#        Data["WALL"][k][year] = Data["Total-CPU"][k][year]*MHrsPerYear/efficiency/scaleTo2020


# # Yearly info:

# In[ ]:


Types = CombinedDetectors+["Analysis","Total"] 
if DRAW:
    DrawDet(shortname+"_byyear","Total-CPU",PlotYears,Data,Types,Units,DetColors,DetLines)#,cpuactual)
    DrawDet(shortname+"_byyear","Cores",PlotYears,Data,Types,Units,DetColors,DetLines)#,coreactual)
    DrawDet(shortname+"_byyear","Wall",PlotYears,Data,Types,Units,DetColors,DetLines)#,wallactual)
    DrawDet(shortname+"_byyear","HS23",PlotYears,Data,Types,Units,DetColors,DetLines)#,wallactual)


# In[ ]:


#  for Storage work out split between different institutions

Splits = {}
for f in SplitsEarly:
    Splits[f] = {}
    for t in SplitsEarly[f]:
        Splits[f][t] = {}
        for loc in SplitsEarly[f][t]: 
            Splits[f][t][loc] = {}
            #print (f,t,Splits[f][t],Splits[f][t][0])
    
            for y in Years:
                if y < SplitsYear:
                    Splits[f][t][loc][y]=SplitsEarly[f][t][loc]
                else:
                    Splits[f][t][loc][y]=SplitsLater[f][t][loc]


# In[ ]:


if DEBUG: print (Splits["CPU"])

for key in ["Total-CPU","Cores","HS23","Wall"]: 
    
    for site in ["FNAL","CERN","Global"]:
        Data[key][site] = {}
        for year in Years:
            
            Data[key][site][year] = Data[key]["Total"][year]*Splits["CPU"]["CPU"][site][year]
            


# # here is where we start doing cumulation across years for disk and reconstruction

# In[ ]:


# now do some Cumulative-work.  Stuff stays on tape/disk for different amounts of time and we have multiple copies

Storage = {}
for k in StorageTypes:
    Storage[k] = {}
Storage["Total"] = {}
Storage["Global"] = {}
Storage["FNAL"] = {}
Storage["CERN"] = {}
Storage["Total"]["Cumulative-Tape"] = {}
Storage["Total"]["Cumulative-Disk"] = {}
Storage["FNAL"]["Cumulative-Tape"] = {}
Storage["FNAL"]["Cumulative-Disk"] = {}
Storage["CERN"]["Cumulative-Tape"] = {}
Storage["CERN"]["Cumulative-Disk"] = {}
Storage["Global"]["Cumulative-Tape"] = {}
Storage["Global"]["Cumulative-Disk"] = {}


for year in Years:
    Storage["Total"]["Cumulative-Tape"][year] = 0.0
    Storage["Total"]["Cumulative-Disk"][year] = 0.0

for k in StorageTypes:
    Storage[k]["Tape"] = {}
    Storage[k]["Disk"] = {}
    for year in Years:
        Storage[k]["Tape"][year] = Data[k]["Total"][year]*TapeCopies[k]
        Storage[k]["Disk"][year] = Data[k]["Total"][year]*DiskCopies[k]
    # extend disk for Analysis HMS 6-24-2023
    #Storage[k]["Disk"]  = extendMap(Years,Storage[k]["Disk"],AnalysisExtend) 
    
    Storage[k]["Cumulative-Tape"] = cumulateMap(Years,Storage[k]["Tape"],TapeLifetimes[k])
    Extend = cumulateMap(Years,Storage[k]["Disk"],DiskLifetimes[k])
    if k != "Test": 
        Storage[k]["Cumulative-Disk"] = extendMap(Years,Extend,AnalysisExtend,k)
    else:
        Storage[k]["Cumulative-Disk"] = Extend
    
    for year in Years:
        Storage["Total"]["Cumulative-Tape"][year] += Storage[k]["Cumulative-Tape"][year]
        Storage["Total"]["Cumulative-Disk"][year] += Storage[k]["Cumulative-Disk"][year]
    
    
        
for loc in Splits["Disk"]["Raw-Store"]:
    for year in Years:
        Storage[loc]["Cumulative-Disk"][year] = 0.0
        Storage[loc]["Cumulative-Tape"][year] = 0.0       
        for k in StorageTypes:
              Storage[loc]["Cumulative-Disk"][year] += Storage[k]["Cumulative-Disk"][year]*Splits["Disk"][k][loc][year]
              Storage[loc]["Cumulative-Tape"][year] += Storage[k]["Cumulative-Tape"][year]*Splits["Tape"][k][loc][year]


# cdisk = SumOver1("Cumulative-Disk",Data)
# print ("sum over",cdisk)

# for year in Years:
#         Data[loc]["Cumulative-Disk"][year] = 0.0
#         Data[loc]["Cumulative-Tape"][year] = 0.0       
#         for k in StorageTypes:
#               Data[loc]["Cumulative-Disk"][year] += Data[k]["Cumulative-Disk"][year] 
#               Data[loc]["Cumulative-Tape"][year] += Data[k]["Cumulative-Tape"][year] 


# In[ ]:


texfile.write("\\section{Projected Disk and Tape needs by source and site}\n")
#ToCSV1(shortname+"-Disk_by_location","Cumulative-Disk",PlotYears,Storage,Units,Formats)
#ToCSV1(shortname+"-Tape_by_location","Cumulative-Tape",PlotYears,Storage,Units,Formats)
# s = "\\begin{table}[h]\n \\centering\\csvautotabularright\
# {external/DUNERSEUSAGE-2022-11-14.csv}\n \\label{Cumulative-Tape}\n\
# \\caption{Rucio report on storage usage 2022-11-14 from the Scotgrid Dashboard \
# \\href{https://dune.monitoring.edi.scotgrid.ac.uk/app/dashboards}{https://dune.monitoring.edi.scotgrid.ac.uk/app/dashboards}.}\n \\end{table}\n"
# s.replace("_","\_")
# texfile.write(s)

# s = TableTex(shortname+"-Disk_by_location","Disk requests by location. The top 4 lines show the source, the bottom 4 show the locations requested and the total request.","Cumulative-Disk"+"\n")
# texfile.write(s)
# s = TableTex(shortname+"-Tape_by_location","Tape requests by location. The top 4 lines show the source, the bottom 4 show the locations requested and the total request.","Cumulative-Tape"+"\n")
# texfile.write(s)

# texfile.write("\\clearpage\n")


# In[ ]:


# now do some plots

Types = CombinedDetectors+["Analysis","Total"]

cpuactual = []
coreactual = []
wallactual = []

Sites = ["FNAL","CERN","Global","Total"]

if DRAW:
    DrawDet(shortname,"Total-CPU",PlotYears,Data,Types,Units,DetColors,DetLines,cpuactual)
    DrawDet(shortname,"Cores",PlotYears,Data,Types,Units,DetColors,DetLines,coreactual)
    DrawDet(shortname,"Wall",PlotYears,Data,Types,Units,DetColors,DetLines,wallactual)
    DrawDet(shortname,"HS23",PlotYears,Data,Types,Units,DetColors,DetLines,wallactual)



# DrawDet(shortname,"Total-CPU",PlotYears,Data,Sites,Units,DetColors,DetLines,cpuactual)
# DrawDet(shortname,"Cores",PlotYears,Data,Sites,Units,DetColors,DetLines,coreactual)
# #DrawDet(shortname,"WALL",PlotYears,Data,Types,Units,DetColors,DetLines,wallactual)
# DrawDet(shortname,"HS23",PlotYears,Data,Sites,Units,DetColors,DetLines,wallactual)



for x in ["Total-CPU","Cores","HS23","Wall"]:
    ToCSV2(shortname+"-"+x,x,PlotYears,Data,Units,Formats)


# In[ ]:


Captions2 = {"Events":"Projected million of detector events per year.  Reconstructed data resources are based on this number.",
"Test":"Projected PB of Test data per year.",
"Sim-Events":"Projected millions of simulated events per year. Simulated data resources are based on this number. ",
"Raw-Store":"Projected raw data written per year in PB, derived from the number of events.",
"Reco-Data-CPU":"Projected CPU needs in core-hrs for data reconstruction. \
             Slot weighted wall time takes into account memory use and an efficiency correction.  Assumes rereconstruction of several years of older data.",
"Sim-CPU":"Projected CPU needs in core-hrs for simulation and reconstruction. \
             Slot weighted wall time takes into account memory use and an efficiency correction. Based directly on the number of simulated Events.",
"Reco-Data-Store":"Projected PB of reconstructed data per year. Includes reprocessing.",
"Sim-Store":"Projected PB of simulated data/year",
"Total-CPU":"Slot weighted CPU needs in core-years. Slot weighted wall time takes into account memory and efficiency.",
"Cores":"Slot weighted CPU needs in number of cores. Slot weighted wall time takes into account memory and efficiency.",
"HS23":"Slot weighted CPU needs in kHS23 hrs. Slot weighted wall time takes into account memory and efficiency.",
"Analysis-CPU":"Slot weighted analysis CPU needs in core-hrs. Assumed to be a weighted fraction of reco+sim needs.",
            }
print (Data["Events"]["PDs"])
#print (Data["Events"]["FDs"])
print (Data["Events"]["ND-SAND"])

    


# In[ ]:





# In[ ]:


# for key in ["Cores","Total-CPU","HS23"]:
#     print ("Got to Here")
#     if not key in Units:
#         print ("no units for key",key)
#         continue
#     ToCSV2(shortname+"-"+key,key,PlotYears,Data,Units,Formats)
#     s = TableTex(shortname+"-"+key,Captions2[key],key+"\n")
#     #DrawDet(shortname,key,PlotYears,Data,list(Data[key].keys()),Units,DetColors,DetLines)
#     #s2 = DrawTex(shortname,key+".png",Captions2[key],key)
#     print  ("Got to here")
#     s2 = BothTex(shortname,key+".png",Captions2[key],key)
#     #texfile.write(s2)
#     tablefile.write(s2)


# In[ ]:


print (Storage.keys())
    
Captions1 = {"Cumulative-Tape":"Cumulative Tape needs in PB. Includes multiple copies and data lifetimes.\
 The top 4 lines show the source of the data while the last four propose responsibilities.", 
             "Cumulative-Disk":"Cumulative Disk needs in PB. Includes multiple copies and data lifetimes.\
 The top 4 lines show the source of the data while the last four propose responsibilities.",
            "HS23":"CPU needs in HS23 units"}
            

for key in ['Cumulative-Tape', 'Cumulative-Disk']:
    if not key in Units:
        print ("no units for key",key)
        continue
    # actual = None
    # if key == "Cumulative-Tape":
    #     actual = tapeactual
    # if key == "Cumulative-Disk":
    #     actual = diskactual
    # print (actual)
    ToCSV1(shortname+"-"+key,key,PlotYears,Storage,Units,Formats)
    ToCSV1(shortname+"-"+key+"-Source",key,PlotYears,Storage,Units,Formats,['Raw-Store', 'Test', 'Reco-Data-Store', 'Sim-Store', 'Total'])
    ToCSV1(shortname+"-"+key+"-Request",key,PlotYears,Storage,Units,Formats,['Global', 'FNAL', 'CERN', 'Total'])
    s = TableTex(shortname+"-"+key,Captions1[key],key+"\n")
    print (key,s)
    dunestyle.Preliminary()
    DrawType(shortname,key,PlotYears,Storage,StorageTypes+["Total"],Units,TypeColors,TypeLines)
 
    s2 = BothTex(shortname,key+".png",Captions1[key],key)

    #texfile.write(s2)
    texfile.write(s2)


# In[ ]:


print (Types)

for key in Types:
    if not key in Units:
        print ("no units for key",key)
        continue
    ToCSV2(shortname+"-"+key,key,PlotYears,Data,Units,Formats)
    s = TableTex(shortname+"-"+key,Captions2[key],key+"\n")
    DrawDet(shortname,key,PlotYears,Data,list(Data[key].keys()),Units,DetColors,DetLines)
    #s2 = DrawTex(shortname,key+".png",Captions2[key],key)
    s2 = BothTex(shortname,key+".png",Captions2[key],key)
    #texfile.write(s2)
    tablefile.write(s2)

for key in Sites:
    if not key in Units:
        print ("no units for key",key)
        continue
    ToCSV2(shortname+"-"+key,key,PlotYears,Data,Units,Formats)
    s = TableTex(shortname+"-"+key,Captions2[key],key+"\n")
    DrawDet(shortname,key,PlotYears,Data,list(Data[key].keys()),Units,DetColors,DetLines)
    #s2 = DrawTex(shortname,key+".png",Captions2[key],key)
    s2 = BothTex(shortname,key+".png",Captions2[key],key)
    #texfile.write(s2)
    tablefile.write(s2)
        


# In[ ]:


tapepoints = np.zeros(len(Years))
diskpoints = np.zeros(len(Years))

#DrawType(shortname,"Tape",Years,Data,StorageTypes+["Total"],Units,TypeColors,TypeLines,None,None)
#DrawType(shortname,"Cumulative-Tape",PlotYears,Storage,StorageTypes+["Total"],Units,TypeColors,TypeLines,None,None)
#DrawType(shortname,"Cumulative-Disk",PlotYears,Storage,StorageTypes+["Total"],Units,TypeColors,TypeLines,None,None)
#DrawType(shortname,"Cumulative-Disk",Years,Data,StorageTypes+["Total"],Units,TypeColors,TypeLines,None,None)



# In[ ]:


tablefile.close()
#texfile.write("\\input{bibmaker.tex}\n")
#texfile.write("\\clearpage\n")
#texfile.write("\\section{Appendix - Model inputs}\n")
#texfile.write("\\input{"+dirname+"/tables.tex}\n")
#texfile.write("\\end{document}\n")
texfile.close()


       


# In[ ]:


# make a set of request numbers to add to the tex file - they need to have tex compatible nicknames

macro = open(shortname+"_macros.tex",'w')

command = makeParameter("HS23Request","%10.0f"%(Data["HS23"]["Total"][RequestYear]))
print ("tex command", command,Data["HS23"]["Total"][RequestYear])

Requests = {}
Requests["CPU"]="HS23"
Requests["CORES"]="Cores"

Requests["DISK"]="Cumulative-Disk"
Requests["TAPE"]="Cumulative-Tape"

m = makeParameter("ThisYear","%d"%RequestYear)
macro.write(m+"\n")

for y in Requests:
    for x in Sites:
        name = ("%s%s"%(y,x)).replace("-","")
        if y == "CPU" or y == "CORES":
            if y == "CPU": 
                m = makeParameter(name,"%10.1f"%(Data[Requests[y]][x][RequestYear]))
            else: 
                m = makeParameter(name,"%10.0f"%(Data[Requests[y]][x][RequestYear]))
        else:
            m = makeParameter(name,"%10.1f"%(Storage[x][Requests[y]][RequestYear]))
        macro.write(m+"\n")
macro.close()



# In[ ]:


jname = configfilename.replace(".json","_internal.json")
jj = open(jname,'w')
commentjson.dump(Data,jj,indent=4)
jj.close()


# In[ ]:


#cmd='pdflatex MoreSim_2023-06-22-2040.tex'
#get_ipython().system('{cmd}')