#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import os
print(sys.executable)
DEBUG=False


# In[ ]:





# 
# Code to generate yearly summaries of DUNE data volumes from input parameters
# 
# Complete rewrite of data structures to allow selection of any subsample
# 
# HMS 2024-08-11
# 
# If you have json problems, run the program ../strip.py on your json file to take off comments and then test using https://jsonlint.com
# 
# 
# 

# In[ ]:


DRAW = ".py" not in sys.argv[0] # only draw if in notebook - otherwise write to file
import os,commentjson
from csv import reader
import json
import numpy as np
import dunestyle.matplotlib as dunestyle
from NumberUtils import dump
from NumberUtils import DrawTex
from NumberUtils import cumulateMap
from NumberUtils import DrawDet
from NumberUtils import DrawType
from NumberUtils import makeArray
from NumberUtils import ToCSV1
from NumberUtils import ToCSV2
#from NumberUtils import SumOver1
#from NumberUtils import SumOver2
from NumberUtils import TableTex
from NumberUtils import BothTex
from NumberUtils import extendMap
from NumberUtils import makeParameter
from DataHolder import DataHolder


# In[ ]:


# how many histograms to draw in multi-hist plots
N_HISTS = 8   # exhibits all the colors in the Okabe-Ito cycler

# specify the json file here.  Will create a subdirectory for plots with a similar name

configfilename = "NearTerm_2024-08-14-2040.json"
if len(sys.argv) > 1 and sys.argv[1] == "old":
    configfilename = "Feb24.json"
print (configfilename)


# In[ ]:


theshortname = configfilename.replace(".json","")
if os.path.exists(configfilename):
    with open(configfilename,'r') as f:
        config = commentjson.load(f)
        print ("config file",configfilename,"found")
else:
    print ("no config file",configfilename)
    sys.exit(0)

if not "Version" in config or config["Version"] < 20:
    print (" this code expects Version >= 20")
    sys.exit(1)


# In[ ]:


MWCWeight = config["MWCWeight"] # do we weight cores by available memory? 
MaxYear = config["MaxYear"]
MWCstring = "_noMWC"
if MWCWeight: 
    print ("MWC no longer enabled, ignore")
    MWCstring=""
config["filename"] = configfilename
TEST = config["Test"]
MinYear = config["MinYear"]
Detectors = config["Detectors"]
DataTypes = config["DataTypes"]
NativeTypes = config["NativeTypes"]
if TEST:
    Detectors = config["TestDetectors"]
    DataTypes = config["TestTypes"]
    if "TP" not in DataTypes and "TP" in NativeTypes:
        NativeTypes.remove("TP")
    
Years = config["Years"]

shortname = theshortname.replace("2040","%d"%MaxYear)+MWCstring
dirname = shortname
if not os.path.exists(dirname):
    os.mkdir(dirname)
shortname = os.path.join(dirname,dirname)
# make a tex output file
texfilename = os.path.join(dirname,dirname+".tex")
texfile = open(texfilename,'w')
tablefile = open(os.path.join(dirname,"tables.tex"),'w')
texfile.write("\\input{../Header.tex}\n")

size = len(Years)
Units = config["Units"]
BaseUnits = config["BaseUnits"]
RequestYear=2024
if "RequestYear" in config:
    RequestYear= config["RequestYear"]
        
Formats = config["Formats"]
Resources = config["Resources"]
Locations = config["Locations"]
PlotDetectors = Detectors+["Total"]
PlotDataTypes = DataTypes+["Total"]
PlotLocations = Locations+["Total"]
Scales = config["Scales"]
Cap = config["Cap"]
CapInTB = Cap*1000

BaseMemory = config["Base-Memory"]
Splits= config["Splits"]
PDlist = config["PDlist"]
FDlist = config["FDlist"]
NDlist = config["NDlist"]

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
Slots = config["Slots"]
DetColors=config["DetColors"]
DetLines = config["DetLines"]
#TypeColors=config["TypeColors"]
#TypeLines = config["TypeLines"]

#PatternFraction = config["PatternFraction"]
Explain = config["Explain"]
Explain["filename"] = "Input configuration file"

if DEBUG:
    for i in config.keys():
        if i not in Explain.keys():
            print ("Still need to explain",i)

for f in Explain.keys():
    field = "{\\tt %s:} %s = {\\tt %s} \\\\\n"%(f,Explain[f], config[f])
    field = field.replace("_","\_")
    tablefile.write(field)
    print (f, Explain[f], config[f])


# ## Make data container (holder)

# In[ ]:


holder = DataHolder(theconfig=config,debug=DEBUG)
holder.readTimeline()
holder.showPlot = DRAW
csvname = configfilename.replace(".json","_inputs.csv")
csvData = holder.csvDump(dirname,csvname)

holder.jsonDump(dirname,configfilename.replace(".json","_safe.json"))

holder.debug=DEBUG

if DEBUG: ("Detector Parameters",DetectorParameters)


# # Change input (NativeTypes) into storage numbers

# In[ ]:


# fill in other useful arrays

holder.debug=DEBUG
print ("--------------- raw-storage ------------------")
print ("NativeTypes",NativeTypes)
for detector in Detectors:
    # first raw data events which have to be stored. 
    # Make "input" locations in to "Store" scaled by config[detector][type]
    for olddatatype in config["NativeTypes"]:
        oldunits = Scales[olddatatype]
        oldresource = "input"
        newresource = "Store"
        location = "Total"
                 
        if holder.hasTag(detector,olddatatype,oldresource,location,oldunits):
            if DEBUG: holder.printByTag(holder.tag(detector,olddatatype,oldresource,location,oldunits))
            factor = 1
            if olddatatype == "Raw-Events":
                newdatatype = "Raw-Data"
                factor = config[detector]["Raw-Data-Store"]
                newunits = Scales["Raw-Data-Store"]
            else:
                newdatatype = olddatatype
                newunits = oldunits
            # TP and Test are already in units of GB
            if DEBUG: print ("storage",detector,olddatatype,newresource,location,newunits,factor)
            newtag = holder.scale(detector,olddatatype,oldresource,location,oldunits,{"DataTypes":newdatatype,"Resources":newresource,"Units":newunits},factor,explanation="Change native types into storage using factor %.2f"%factor)
            if DEBUG: holder.printByTag(newtag)
        else:
            if DEBUG: print ("could not find", detector,olddatatype,oldresource,location,oldunits)



# In[ ]:



               


# # calculate size of raw data coming from Far detector 

# In[ ]:


# complicated way of doing double sum  
print ("----------------------------- draw real data -----------------------")
RealDataTypes=["Raw-Data","TP","Test"]
FarDetectors = ["PDVD","PDHD","FDHD","FDVD"]
realsubset={"Detectors":FarDetectors,"DataTypes":RealDataTypes,"Resources":["Store"],"Locations":["Total"],"Units":["TB"]}
explanation = "Sum over raw data types from ProtoDUNEs and Far detector"
realDataTotalDetector=holder.sumAcrossFilters(
    filter=realsubset,sumCat="Detectors",sumName="Sub-Total",
    explanation=explanation)

realsubset2={"Detectors":FarDetectors+["Sub-Total"],
             "DataTypes":RealDataTypes,"Resources":["Store"],"Locations":["Total"],"Units":["TB"]}

realDataTotalDetectorStore=holder.sumAcrossFilters(
    filter=realsubset2,sumCat="DataTypes",sumName="Sub-Total",
    explanation="second sum over raw types")
    
newsubset={"Detectors":(["Sub-Total"]),
           "DataTypes":RealDataTypes+["Sub-Total"],
           "Resources":["Store"],
           "Locations":["Total"],
           "Units":["TB"]}

fig= holder.Draw(dirname,Title="RealData",YAxis="Storage",
            Resource="Store",Category="DataTypes",filter=newsubset)
texfile.write(holder.TexBoth(fig,"Real data create/year in TB",label="realdata"))
holder.csvDump(dirname,"realData.csv")

holder.debug = DEBUG

holder.csvDump(dirname,dirname+"after-raw.csv")


# ## special section to impose the cap

# In[ ]:


# scale everything year by year so it meets the cap
DEBUG=True
subtotaltag  = holder.tag("Sub-Total","Sub-Total","Store","Total","TB")
print (subtotaltag)

subtotal = holder.holder[subtotaltag]
factors = {}
for year in Years:
    if subtotal[year] > CapInTB:
        factors[year] = CapInTB/subtotal[year]
    else:
        factors[year] = 1.0

if DEBUG: print ("Cap scaling factor", factors)


toRescale = {"Detectors":FarDetectors+["Sub-Total"],
             "DataTypes":RealDataTypes+["Sub-Total"],
             "Resources":["Store","input"],
             "Locations":["Total"],
             "Units":["TB","Million"]
             }

tagsToRescale=holder.makeTagSet(toRescale)

for tag in tagsToRescale:
    modified = False
    # att = holder.tagToDict(tag)
    # if DEBUG: print ("Check", att)
    # if att["Detectors"] in FarDetectors and att["DataTypes"] in RealDataTypes+["Raw-Events"]:

    if DEBUG: holder.printByTag(tag)
    for year in Years:
        if factors[year] < 1.0:
            holder.holder[tag][year] *= factors[year]
            modified = True
    if modified:
        print ("Rescale to fit cap of %d PB "%Cap)
        holder.explanation[tag] += " rescaled to meet cap of %d"%Cap
    if DEBUG: holder.printByTag(tag)





#holder.sumAcrossAll(filter=to,sumName="Sub-Total",explanation="Rescaled after cap")

drawfilter= {"Detectors":["Sub-Total"],
             "DataTypes":RealDataTypes+["Sub-Total"],
             "Resources":["Store"],
             "Locations":["Total"],
             "Units":["TB"]
             }

DEBUG=False

holder.csvDump(dirname,"aftercap.csv")


# In[ ]:


fig= holder.Draw(dirname,Title="Real Data after scaling to cap of %d PB."%Cap,YAxis="Storage",
            Resource="Store",Category="DataTypes",filter=drawfilter)
texfile.write(holder.TexBoth(fig,"Real data created/year in TB, after scaling to cap of %d PB.  All data types are scaled by the same factor. "%Cap,label="realdataCapped"))
holder.csvDump(dirname,"realDataCapped.csv")


# In[ ]:







# # extend events for Reco and calculate storage/CPU/GPU per year

# In[ ]:


print ("---------------  transform Events into CPU estimates  ------------------") 
for detector in Detectors:
    for newdatatype in ["Reco-Data","Reco-Sim"]:
        oldresource = "input"

        if newdatatype == "Reco-Data": 
            olddatatype = "Raw-Events"

        if newdatatype == "Reco-Sim":
            olddatatype = "Sim-Events"

        oldunits = Scales[olddatatype]
        location = "Total"

        # Reco gets reprocessed so has a special cumulation

        for resource in ["CPU","GPU","Store"]:
            newunits = Scales[newdatatype+"-"+resource]    
            if holder.hasTag(detector,olddatatype,oldresource,location,oldunits):
                if DEBUG: holder.printByTag(
                    holder.tag(detector,olddatatype,oldresource,location,oldunits))                 
                if DEBUG: print ("--before Events->Things",olddatatype,resource)
                newunits = Scales[newdatatype+"-"+resource]
                factor = config[detector][newdatatype + "-" +resource]*PerYear[newdatatype+"-"+resource]
                if DEBUG: print ("factor",detector,newdatatype,resource,factor)
                thedatatype = newdatatype
                newtag = holder.scale(detector,olddatatype,oldresource,location,oldunits,{"DataTypes":thedatatype,"Resources":resource,"Units":newunits},factor,explanation="Scale inputs by %.2f"%factor)
                if DEBUG: holder.printByTag(newtag)
                if DEBUG: print ("--after Events->Things",newdatatype,resource)

                # special to say you redo previous Reprocess years of reco every year.
                if thedatatype == "Reco-Data":  
                    newtag = holder.cumulateMe(detector,newdatatype,resource,
                                               location,newunits,{"DataTypes":"Reco-Data"},
                                               Reprocess[detector],
                                               explanation="Go back %.2f years for Reco-Data"%(Reprocess[detector])) 
                    
                if DEBUG: holder.printByTag(newtag)


# In[ ]:





# # calculate analysis based on scaling of data/sim

# In[ ]:


print ("---------------  make analysis ------------------")
for detector in Detectors:
    for resource in ["CPU"]:   
        location = "Total"
        factor = config[detector]["Analysis-CPU"]*PerYear["Analysis-CPU"]
        recoAtag = holder.scale(detector,"Reco-Data",
                                resource,location,Scales["Reco-Data-CPU"],{"DataTypes":"Analysis-Data"},factor,
                                explanation="Make Analysis using factor %.2f"%factor)
        simAtag = holder.scale(detector,"Reco-Sim",
                               resource,location,Scales["Reco-Sim-CPU"],{"DataTypes":"Analysis-Sim"},factor,
                               explanation="Make Analysis using factor %.2f"%factor)
        if DEBUG: print (recoAtag)
      
        recoAtag = holder.extendMe(detector,"Analysis-Data",
                                   resource,location,Scales["Reco-Data-CPU"],{},AnalysisExtend,
                                   explanation="Extend Analysis processing by %.2f years"%AnalysisExtend)
        simAtag = holder.extendMe(detector,"Analysis-Sim",
                                  resource,location,Scales["Reco-Sim-CPU"],{},AnalysisExtend,
                                  explanation="Extend Analysis processing by %.2f years"%AnalysisExtend)
        if DEBUG: print ("make analysis:",recoAtag,simAtag)

holder.csvDump(dirname,"after-analysis.csv")


# In[ ]:


print ("---------------  make different CPU units ------------------")

MHrsPerYear = 1000000./365/24.
for detector in Detectors:
    for datatype in DataTypes:
        for oldresource in ["CPU","GPU"]:
            oldunits = "MHr"
            location = "Total"
        
            for newunit in ["Wall","kHS23-Yr","Cores"]:
                
                newresource = oldresource + " " + newunit
                factor = 1./Slots["Efficiency"]/Slots["2020Units"]
                
                newunits = "MHr"
                if newunit == "kHS23-Yr":
                    factor *= config["kHEPSPEC06PerCPU"]*MHrsPerYear
                    newunits = "kHS23-Yr"
                if newunit == "Cores":
                    newunits = "Cores"
                    factor *= MHrsPerYear
                if DEBUG:
                    print (newunit,newunits,factor)
                newtag = holder.scale(detector,datatype,oldresource,location,oldunits,{"DataTypes":datatype,"Resources":newresource,"Units":newunits},factor,explanation="Add %.2f efficiency Change units from %s to %s using factor of %.2f"%(Slots["Efficiency"],oldunits,newunits,factor))
                if newtag != None and DEBUG:
                    print (newtag,holder.holder[newtag])
              
holder.csvDump(dirname,"after-CPUscale.csv")


# 

# In[ ]:





# In[ ]:


holder.debug = DEBUG

print("---------------------- sum across CPU ---------------------------------")

# filter on derived event types

CPUTypes = ["GPU","CPU","Total","CPU Wall","CPU kHS23-Yr", "CPU Cores"] 
filter = {"Detectors":Detectors,"DataTypes":["Reco-Sim","Reco-Data","Analysis-Data","Analysis-Sim"],"Resources":CPUTypes,"Locations":["Total"],"Units":Units}
if DEBUG:
    show = json.dumps(filter,indent=4)
    print (show)

CPUTotals=holder.sumAcrossFilters(filter=filter,sumCat="DataTypes",
                                  sumName="Total",explanation="Sum processing across DataTypes")

filter2 = {"Detectors":Detectors,
           "DataTypes":["Reco-Sim","Reco-Data","Analysis-Data","Analysis-Sim"]+["Total"],"Resources":CPUTypes,"Locations":["Total"],"Units":Units}

#print (filter2)
CPUTotalsAllDetectors=holder.sumAcrossFilters(
    filter=filter2, sumCat="Detectors",sumName= "Total",
    explanation="Sum processing across Detectors")
#print ("DataTypes",DataTypes)



# In[ ]:


# make filters and then draw
print ("draw CPU info")

CPUResources = ["CPU","CPU Wall","CPU kHS23-Yr", "CPU Cores"]
CPUResourcesByDetector = {"Detectors":Detectors+["Total"],
                          "DataTypes":["Total"],"Resources":CPUResources,"Locations":["Total"],"Units":Units}
CPUResourcesByType = {"Detectors":["Total"],
                      "DataTypes":DataTypes+["Total"],"Resources":CPUResources,"Locations":["Total"],"Units":Units}

holder.storeFilter(filter=CPUResourcesByDetector,name="CPUResourcedByDetector")
holder.storeFilter(filter=CPUResourcesByType,name="CPUResourcesByType")

for resource in CPUResources:
    fig = holder.Draw(Dir=dirname,Title="Processing by Type",
                YAxis=resource,Resource=resource,Category="DataTypes",filter=CPUResourcesByType)
    texfile.write(holder.TexBoth(fig,"%s resources by data types by year."%resource,label=resource+"_Types"))
    fig = holder.Draw(Dir=dirname,Title="Processing by Detector",
                YAxis=resource,Resource=resource,Category="Detectors",filter=CPUResourcesByDetector)
    texfile.write(holder.TexBoth(fig,"%s resources by detector by year."%resource,label=resource+"_Detectors"))
    
holder.debug = DEBUG
holder.csvDump(dirname,"after-total2.csv")


# # make tape and disk and them cumulate

# In[ ]:


print("---------------------- change Store into Disk and Tape ---------------------------------")

oldresource = "Store"
for detector in Detectors:
    for datatype in DataTypes:
        if datatype in holder.nosum:
            continue
        if datatype in ["Raw-Events","Sim-Events"]: continue
        for newresource in ["Disk","Tape"]:
            for locations in ["Total"]:
                if newresource == "Disk": 
                    factor = DiskCopies[datatype]
                    if detector in ["PDHD","PDVD"]:
                        factor *=2
                if newresource == "Tape": 
                    factor = TapeCopies[datatype]
                newtag = holder.scale(detector= detector,datatype=datatype,resource=oldresource,location=locations,units="TB",categories={"Resources":newresource},factor=factor,explanation="Scale by number of copies, %.2f"%factor)

holder.csvDump(dirname,"disk-tape.csv")


# In[ ]:


print("---------------------- split disk and tape across sites ---------------------------------")
print (Detectors)
holder.debug=DEBUG
oldlocation = "Total"
for detector in Detectors:
    split = None
    if detector in PDlist:
        split = Splits["PD"]
    elif detector in FDlist:
        split = Splits["FD"]
    elif detector in NDlist:
        split = Splits["ND"]
    if split is None:
        print ("can't figure out split", detector)
        break
    if DEBUG: print (split.keys())
    for datatype in DataTypes:
        #if datatype in holder.nosum: continue            
        for resource in Resources:
            thedatatype = datatype
            if resource in holder.nosum: continue
            #if resource in ["CPU","GPU"]:  # right now this is generic 
            #    thedatatype = resource
            for location in Locations:
                if location in holder.nosum: continue
                oldtag = holder.tag(detector,datatype,resource,oldlocation,BaseUnits[resource])
                if oldtag not in holder.holder:
                    if DEBUG: print ("skip split tag",oldtag)
                    continue
                if DEBUG: print ("check", resource,thedatatype,location)
                if "CPU" in resource:
                    factor = split["CPU"]["CPU"][location]
                elif "GPU" in resource:
                    factor = split["GPU"]["GPU"][location]
                else:
                    factor = split[resource][thedatatype][location]
                if DEBUG: print ("split",factor)
                newtag = holder.scale(detector= detector,datatype=datatype,resource=resource,location=oldlocation,units=BaseUnits[resource],
                                      categories={"Locations":location},factor=factor,explanation="Split  by %.2f"%factor)

holder.csvDump(dirname,"split.csv")


# In[ ]:


# get rid of generic storage
for detector in Detectors:
    for datatype in config["NativeTypes"]:
        location = "Total"
        resource = "Store"
        newtag = holder.tag(detector,datatype,location,resource,"TB")
        if newtag in holder.holder:
            holder.remove(newtag)


# In[ ]:





# # do the cumulation

# In[ ]:


print("----------- cumulate storage by retention -------------")
#DEBUG=True

print (Detectors)
for detector in Detectors:
    if detector in holder.nosum: continue
    for datatype in DataTypes:
        if datatype in ["Raw-Events","Sim-Events"]: continue
        for newresource in ["Disk","Tape"]:
            for location in Locations+["Total"]:

                if newresource == "Disk": 
                    retain = DiskLifetimes[datatype]
                    retresource = "Cumulative-Disk"
                    if "Reco" in datatype:
                        if DEBUG: print ("extend later",detector,datatype,newresource,location)
                        retresource = "Unextended-Cumulative-Disk"
                    #print (detector,datatype,newresource,location)

                if newresource == "Tape": 
                    retain = TapeLifetimes[datatype]
                    retresource = "Cumulative-Tape"

                newertag = holder.cumulateMe(detector=detector,datatype=datatype,resource=newresource,location=location,units="TB",categories={"Resources":retresource},period=retain,explanation="Look back %.2f years and keep that Storage "%factor)
                # if DEBUG: print (newertag,holder.holder,newertag)
                # # and extend time for reconstructed disk so one can analyze
                # if ("Reco" in datatype and retresource == "Cumulative-Disk"):
                #     if DEBUG: print ("extend by ",AnalysisExtend,newertag)
                #     newertag = holder.extendMe(detector,datatype,retresource,location,"TB",{},AnalysisExtend)
                if DEBUG: print (newertag)
                
holder.csvDump(dirname,"cumulate.csv")


# In[ ]:


print("----------- extend reco samples on disk -------------")
#DEBUG=True
print (Detectors)
for detector in Detectors:
    #if detector in holder.nosum: continue
    for datatype in ["Reco-Data","Reco-Sim"]:   
        for newresource in ["Unextended-Cumulative-Disk"]:
            for location in Locations+["Total"]:
                if "Reco" in datatype:
                    #print (detector,datatype,newresource,location)
                    pretag = holder.tag(detector,datatype,newresource,location,"TB")
                    if pretag not in holder.holder:
                        print ("pretag not there",pretag)
                        continue
                    if DEBUG: print ("extend by ",AnalysisExtend,pretag)
                    
                    if DEBUG and pretag in holder.holder:
                        print (holder.holder[pretag])
                    #newtype = datatype.replace("Reco","Analysis")
                    newertag = holder.extendMe(detector,datatype,newresource,location,"TB",{"Resources":"Cumulative-Disk"},AnalysisExtend,explanation="Extend disk by %.2f years as still analyzing"%(AnalysisExtend))
                    if DEBUG: print ("removing",pretag)
                    holder.removeTag(pretag)
                if DEBUG: print (newertag)
                
holder.csvDump(dirname,"extend.csv")


# In[ ]:


print (Detectors)
print (Locations)
while "Total" in Detectors:
    Detectors.remove("Total")
print (Detectors)
print ("------------------ sum across storage types -------------------")
StorageTypes=["Tape","Disk","Cumulative-Tape","Cumulative-Disk"]

Storage = {"Detectors":Detectors,"DataTypes":DataTypes,"Resources":StorageTypes,"Locations":Locations,"Units":["TB"]}

#holder.debug=True
holder.sumAcrossAll(filter=Storage,sumName="Total",explanation="Sum across storage types")
holder.debug=DEBUG

holder.csvDump(dirname,"sumacross.csv")
print (Detectors)


# In[ ]:


storeFilter={"Detectors":Detectors,"DataTypes":["Raw-Data","Reco-Sim","TP","Test"],"Resources":["Store"],"Locations":["Total"],"Units":["TB"]}
holder.sumAcrossAll(filter=storeFilter,sumName="Store-Total",explanation="show raw added storage/year")
storeFilter={"Detectors":Detectors+["Store-Total"],"DataTypes":["Raw-Data","Reco-Sim","TP","Test","Store-Total"],"Resources":["Store"],"Locations":["Total"],"Units":["TB"]}
# holder.csvDump(dirname,"InputStore.csv",filter=storeFilter,dropColumns=["Resources","Locations","Units","Explanation"],format="%d")
# texfile.write(holder.TexTable(name="InputStore.csv",caption="Initial raw storage generated by detector and type per year. Units are TB. This estimate does not include multiple copies.",label="inputStore"))


# ## Define subsamples to plot

# In[ ]:


Storage = {"Detectors":(Detectors+["Total"]),"DataTypes":DataTypes+["Total"],"Resources":StorageTypes,"Locations":["Total"],"Units":["TB"]}

TapeStorage = {"Detectors":["Total"],"DataTypes":DataTypes+["Total"],"Resources":["Tape"],"Locations":["Total"],"Units":["TB"]}

CumulativeTapeStorage = {"Detectors":["Total"],"DataTypes":DataTypes+["Total"],"Resources":["Cumulative-Tape"],"Locations":["Total"],"Units":["TB"]}

DiskStorage = {"Detectors":["Total"],"DataTypes":DataTypes+["Total"],"Resources":["Disk"],"Locations":["Total"],"Units":["TB"]}

DiskStorageFDVD = {"Detectors":["FDVD"],"DataTypes":DataTypes+["Total"],"Resources":["Disk"],"Locations":["Total"],"Units":["TB"]}

CumulativeDiskStorage = {"Detectors":["Total"],"DataTypes":DataTypes+["Total"],"Resources":["Cumulative-Disk"],"Locations":["Total"],"Units":["TB"]}

DiskStorageBySite = {"Detectors":["Total"],"DataTypes":["Total"],"Resources":["Disk"],"Locations":Locations+["Total"],"Units":["TB"]}
DiskStorageByDetector = {"Detectors":Detectors,"DataTypes":["Total"],"Resources":["Disk"],"Locations":["Total"],"Units":["TB"]}
TapeStorageBySite = {"Detectors":["Total"],"DataTypes":["Total"],"Resources":["Tape"],"Locations":Locations+["Total"],"Units":["TB"]}
TapeStorageByDetector = {"Detectors":Detectors,"DataTypes":["Total"],"Resources":["Tape"],"Locations":["Total"],"Units":["TB"]}

CumulativeDiskStorageByType = {"Detectors":["Total"],"DataTypes":DataTypes,"Resources":["Cumulative-Disk"],"Locations":["Total"],"Units":["TB"]}
CumulativeDiskStorageByDetector = {"Detectors":Detectors,"DataTypes":["Total"],"Resources":["Cumulative-Disk"],"Locations":["Total"],"Units":["TB"]}
CumulativeDiskStorageBySite = {"Detectors":["Total"],"DataTypes":["Total"],"Resources":["Cumulative-Disk"],"Locations":Locations+["Total"],"Units":["TB"]}

CumulativeTapeStorageByDetector = {"Detectors":Detectors,"DataTypes":["Total"],"Resources":["Cumulative-Tape"],"Locations":["Total"],"Units":["TB"]}
CumulativeTapeStorageBySite = {"Detectors":["Total"],"DataTypes":DataTypes,"Resources":["Cumulative-Tape"],"Locations":["Total"],"Units":["TB"]}
CumulativeTapeStorageBySite = {"Detectors":["Total"],"DataTypes":["Total"],"Resources":["Cumulative-Tape"],"Locations":Locations+["Total"],"Units":["TB"]}


# In[ ]:


fig = holder.Draw(dirname,"New Tape by Type",YAxis="Storage",Resource="Tape",Category="DataTypes",filter=TapeStorage)
texfile.write(holder.TexBoth(fig,"New Tape by data type.",label="TapeByYearByType"))
              
fig = holder.Draw(dirname,"New Tape by Detector",YAxis="Storage",Resource="Tape",Category="Detectors",filter=TapeStorageByDetector)
texfile.write(holder.TexBoth(fig,"New Tape by detector.",label="TapeByYearByDetector"))

fig = holder.Draw(dirname,"New Tape by Site",YAxis="Storage",Resource="Tape",Category="Locations",filter=TapeStorageBySite)
texfile.write(holder.TexBoth(fig,"New Tape by site.",label="TapeByYearBySite"))

fig = holder.Draw(dirname,"Cumulative Tape by Type",YAxis="Storage",Resource="Cumulative-Tape",Category="DataTypes",filter=CumulativeTapeStorage)

texfile.write(holder.TexBoth(fig,"Cumulative Tape by data type.",label="TapeByYearByType"))

# holder.csvDump(dirname,"CumulativeTapeBySite.csv",filter=CumulativeTapeStorageBySite,dropColumns=["Detectors","DataTypes","Resources","Explanation"],format="%d")

# table = holder.TexTable("CumulativeTapeBySite.csv",caption="Cumulative Tape by Site. Units are TB",label="CumulativeTapeBySiteTable")
# texfile.write(table)

fig = holder.Draw(dirname,"Cumulative Tape by Detector",YAxis="Storage",Resource="Cumulative-Tape",Category="Detectors",filter=CumulativeTapeStorageByDetector)
texfile.write(holder.TexBoth(fig,"Cumulative Tape by detector.",label="TapeByYearByType"))

fig = holder.Draw(dirname,"Cumulative Tape by Site",YAxis="Storage",Resource="Cumulative-Tape",Category="Locations",filter=CumulativeTapeStorageBySite)
texfile.write(holder.TexBoth(fig,"Cumulative Tape by site.",label="TapeByYearByType"))




# In[ ]:


fig = holder.Draw(dirname,"New Disk by Type",YAxis="Storage",Resource="Disk",Category="DataTypes",filter=DiskStorage)
texfile.write(holder.TexBoth(fig,"New Disk by data type.",label="DiskByYearByType"))
              
fig = holder.Draw(dirname,"New Disk by Detector",YAxis="Storage",Resource="Disk",Category="Detectors",filter=DiskStorageByDetector)
texfile.write(holder.TexBoth(fig,"New Disk by detector.",label="DiskByYearByDetector"))

fig = holder.Draw(dirname,"New Disk by Site",YAxis="Storage",Resource="Disk",Category="Locations",filter=DiskStorageBySite)
texfile.write(holder.TexBoth(fig,"New Disk by site.",label="DiskByYearBySite"))

fig = holder.Draw(dirname,"Cumulative Disk by Type",YAxis="Storage",Resource="Cumulative-Disk",Category="DataTypes",filter=CumulativeDiskStorage)
texfile.write(holder.TexBoth(fig,"Cumulative Disk by data type.",label="DiskByYearByType"))

fig = holder.Draw(dirname,"Cumulative Disk by Detector",YAxis="Storage",Resource="Cumulative-Disk",Category="Detectors",filter=CumulativeDiskStorageByDetector)
texfile.write(holder.TexBoth(fig,"Cumulative Disk by detector.",label="DiskByYearByType"))

fig = holder.Draw(dirname,"Cumulative Disk by Site",YAxis="Storage",Resource="Cumulative-Disk",Category="Locations",filter=CumulativeDiskStorageBySite)
texfile.write(holder.TexBoth(fig,"Cumulative Disk by site.",label="DiskByYearByType"))




# In[ ]:





# In[ ]:


# holder.Draw(dirname,"New Disk by Type",YAxis="Storage",Resource="Disk",Category="DataTypes",filter=DiskStorage)
# holder.Draw(dirname,"New Disk by Type for FDVD",YAxis="Storage",Resource="Disk",Category="DataTypes",filter=DiskStorageFDVD)
# holder.Draw(dirname,"New Disk by Detector",YAxis="Storage",Resource="Disk",Category="Detectors",filter=DiskStorageByDetector)
# holder.Draw(dirname,"New Disk by Site",YAxis="Storage",Resource="Disk",Category="Locations",filter=DiskStorageBySite)
# holder.Draw(dirname,"Cumulative Disk by Type",YAxis="Storage",Resource="Cumulative-Disk",Category="DataTypes",filter=CumulativeDiskStorage)
# holder.Draw(dirname,"Cumulative Disk by Detector",YAxis="Storage",Resource="Cumulative-Disk",Category="Detectors",filter=CumulativeDiskStorageByDetector)
# holder.Draw(dirname,"Cumulative Disk by Site",YAxis="Storage",Resource="Cumulative-Disk",Category="Locations",filter=CumulativeDiskStorageBySite)


# In[ ]:


# texfile.write("\\end{document}")
# texfile.close()


# # by detector plots
# 
# for detector in Detectors:
#     if detector == "Total": continue
#     TapeStorage = {"Detectors":[detector],"DataTypes":DataTypes+["Total"],"Resources":["Tape"],"Locations":["Total"],"Units":["TB"]}
# 
#     CumulativeTapeStorage = {"Detectors":[detector],"DataTypes":DataTypes+["Total"],"Resources":["Cumulative-Tape"],"Locations":["Total"],"Units":["TB"]}
# 
#     DiskStorage = {"Detectors":[detector],"DataTypes":DataTypes+["Total"],"Resources":["Disk"],"Locations":["Total"],"Units":["TB"]}
# 
#     CumulativeDiskStorage = {"Detectors":[detector],"DataTypes":DataTypes+["Total"],"Resources":["Cumulative-Disk"],"Locations":["Total"],"Units":["TB"]}
# 
#     DiskStorageBySite = {"Detectors":[detector],"DataTypes":["Total"],"Resources":["Disk"],"Locations":Locations+["Total"],"Units":["TB"]}
#     
#     TapeStorageBySite = {"Detectors":[detector],"DataTypes":["Total"],"Resources":["Tape"],"Locations":Locations+["Total"],"Units":["TB"]}
# 
#     CumulativeDiskStorageBySite = {"Detectors":[detector],"DataTypes":["Total"],"Resources":["Cumulative-Disk"],"Locations":Locations+["Total"],"Units":["TB"]}
#     
#     CumulativeTapeStorageBySite = {"Detectors":[detector],"DataTypes":["Total"],"Resources":["Cumulative-Tape"],"Locations":Locations+["Total"],"Units":["TB"]}
# 
#     holder.Draw(dirname,"New Disk by Type "+detector,YAxis="Storage",Resource="Disk",Category="DataTypes",filter=DiskStorage)
#     
#     holder.Draw(dirname,"New Disk by Site "+detector,YAxis="Storage",Resource="Disk",Category="Locations",filter=DiskStorageBySite)
#     holder.Draw(dirname,"Cumulative Disk by Type "+detector,YAxis="Storage",Resource="Cumulative-Disk",Category="DataTypes",filter=CumulativeDiskStorage)
#     
#     holder.Draw(dirname,"Cumulative Disk by Site "+detector,YAxis="Storage",Resource="Cumulative-Disk",Category="Locations",filter=CumulativeDiskStorageBySite)
# 
#     holder.Draw(dirname,"New Tape by Type "+detector,YAxis="Storage",Resource="Tape",Category="DataTypes",filter=TapeStorage)
#     #holder.Draw(dirname,"New Tape by Detector",YAxis="Storage",Category="Detectors",filter=TapeStorageByDetector)
#     holder.Draw(dirname,"New Tape by Site "+detector,YAxis="Storage",Resource="Tape",Category="Locations",filter=TapeStorageBySite)
#     holder.Draw(dirname,"Cumulative Tape by Type "+detector,YAxis="Storage",Resource="Cumulative-Tape",Category="DataTypes",filter=CumulativeTapeStorage)
#     #holder.Draw(dirname,"Cumulative Tape by Detector",YAxis="Storage",Category="Detectors",filter=CumulativeTapeStorageByDetector)
#     holder.Draw(dirname,"Cumulative Tape by Site "+detector,YAxis="Storage",Resource="Cumulative-Tape",Category="Locations",filter=CumulativeTapeStorageBySite)

# In[ ]:


texfile.write("\\end{document}")
texfile.close()

