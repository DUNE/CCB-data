
'''Container for DUNE data volume information'''
import os,commentjson,sys

from csv import reader

import itertools

from NumberUtils import cumulateMap

#import matplotlib.pyplot as plt
#import matplotlib.colors as mcolors

DEBUG = True
DRAW = False

#import numpy as np
#import scipy

class DataHolder:
    ''' Container for data for DUNE data volume estimates'''

    ''' needs to be indexed by 
    
    experiment: protodune-VD, FDHD, FDVD ... 
    type: events, sim, reco, raw?
    resource: CPU, disk, tape
    location: of the resource (does this need to be separate)
    cumulative or not: 
    years:  handled by using numpy arrays.
    '''

    def __init__(self,theconfig=None):
        self.holder={}
        config = theconfig.copy()
        self.Indices = config["Indices"]

        self.DataTypes = config["DataTypes"]+["Total"]
        self.Resources = config["Resources"]+["Total"]
        self.Locations = config["Locations"]+["Total"]
        self.config=config
        self.MaxYear = config["MaxYear"]
        self.MinYear = config["MinYear"]
        self.Detectors = config["Detectors"]+["Total"]
        print ("detectors",self.Detectors)
        self.Years = config["Years"]
        self.size = len(self.Years)
        self.dataObj = {}

        # # make an empty data object
        # print ("Iter",list(itertools.chain(self.Detectors,["Total"])))
        # for d in itertools.chain(self.Detectors,["Total"]):
        #     self.dataObj[d] = {}
        #     for t in itertools.chain(self.DataTypes,["Total"]):
        #         self.dataObj[d][t] = {}
        #         for r in itertools.chain(self.Resources,["Total"]):
        #             self.dataObj[d][t][r] = {}
        #             for l in itertools.chain(self.Locations,["Total"]):
        #                 self.dataObj[d][t][r][l]={}
        #                 for y in self.Years:
        #                      self.dataObj[d][t][r][l][y] = 0.0

        #                 if DEBUG:
        #                     print("Make",d,t,r,l, self.dataObj[d][t][r][l])
                        

        if "Timeline" in config:
            print ("Timeline from ", config["Timeline"])
        if not os.path.exists(config["Timeline"]):
            print ("timeline file ", config["Timeline"]," does not exist:")
        
        counter = 0
        with open(config["Timeline"], newline='') as csvfile:
            timedata = reader(csvfile)
            for row in timedata:
                if counter == 0: 
                    counter = 1
                    continue
                if DEBUG: print (row)
                det = row[0].strip()
                print (det)
                if det not in self.Detectors:
                    print ("unrecognized detector",det)
                    continue
                    
                thetype = row[1].strip()
                if thetype not in  self.DataTypes:
                    print ("unrecognized datatype", thetype)
            
                local = {}
                for year in self.Years:       
                    local[year] = float(row[year - self.Years[0]+2])
                if not self.hasKey(det,thetype,"dummy","ALL"):
                    self.placeData(detector=det,datatype=thetype,resource="dummy",location="ALL",series=local)
                
        print ( self.holder)

        csvfile.close()
        #sys.exit(1)        
       
        self.RequestYear=2024
        if "RequestYear" in config:
            self.RequestYear= config["RequestYear"]

        self.MWCWeight=config["MWCWeight"]    

        self.Cap = config["Cap"]

        self.BaseMemory = config["Base-Memory"]

        self.CombinedDetectors = config["CombinedDetectors"]

        self.DetectorParameters = list(config["SP"].keys())


        if "Comment" in self.DetectorParameters:
            self.DetectorParameters.remove("Comment")

        
        self.PerYear = config["PerYear"]

        # plot config
        self.DetColors=config["DetColors"]
        self.DetLines = config["DetLines"]
        self.TypeColors=config["TypeColors"]
        self.TypeLines = config["TypeLines"]

        self.PatternFraction = config["PatternFraction"]

        self.SplitsYear = config["SplitsYear"]
        self.SplitsEarly = config["SplitsEarly"]
        self.SplitsLater = config["SplitsLater"]
       

    def tag(self,detector,datatype,resource,location):
        return "%s!%s!%s!%s"%(detector,datatype,resource,location)
    
    def parseTag(self,tag):
        items = tag.split("!")
        return items
    
    def checkTag(self,tag,type,value):
        index = self.Indices(type)
        return self.parseTag(tag)[index] == value
    
    def getData(self,detector,datatype,resource,location):
        return  self.holder[self.tag(detector,datatype,resource,location)]
    
    def placeData(self,detector,datatype,resource,location,series):
        tag = self.tag(detector,datatype,resource,location)
        self.holder[tag] = series

    def zeroes(self):
        new = {}
        for y in self.Years:
            new[y] = 0.0
        return new

    # def cumulateme(self,det,newkey,oldkey,resource,location,period):
    #     ' cumulate over period years '
    #     self.dataObj[det][newkey][resource][location] = cumulateMap(self.Years,self.dataObj[det][oldkey][resource][location],period)

            
    # def scaleme(self,det,newkey,resource,location,scale):
    #     ' scale by a factor'
    #     for year in self.Years:
    #         self.dataObj[det][newkey][resource][location][year] *= scale

    # def getValues(self,detector=None,key=None,resource="dummy",location="ALL"):
    #     return self.dataObj[detector][key][resource][location]
    
    def sumAcross(self,tier="Detectors",sumover=[]):
        totals = {}
        index = self.Indices[tier]
        if DEBUG: print ("index",index)
        for tag in self.holder.keys():
            types = self.parseTag(tag)
            if types[index] == "Total":continue
            if types[index] not in sumover: continue
            sumtag = tag.replace(types[index],"Total") 
            if sumtag not in totals:
                print ("make a new total",sumtag)
                totals[sumtag]=self.zeroes()
            for y in self.Years:
                totals[sumtag][y]+=self.holder[tag][y]
        for x in totals:
            if DEBUG:
                print ("Sums",x,totals[x])
        for x in totals:
            self.holder[x] = totals[x]

    def cumulateMe(self,det,datatype,resource,location,period):
        ' cumulate over period years '
        #self.dataObj[det][newkey][resource][location] = cumulateMap(self.Years,self.dataObj[det][oldkey][resource][location],period)
        tag = self.tag(det,datatype,resource,location)
        
        if tag not in self.holder:
            print ("cannot cumulate missing tag",tag)
        if DEBUG:
            print ("precumulate",tag,self.holder[tag])
        newtype= datatype+"-cumulative"
        newtag = self.tag(det,newtype,resource,location)
        new = cumulateMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        if DEBUG:
            print ("postcumlate",newtag,self.holder[newtag])
        
            
    def listTags(self):
        print (list(self.holder.keys()))
            



        
    def hasKey(self,detector,datatype,resource,location):
        return self.tag(detector,datatype,resource,location) in self.holder
    
    

if __name__ == '__main__':
    configfilename = "NearTerm_2024-06-12-2040.json"
    if os.path.exists(configfilename):
        with open(configfilename,'r') as f:
            config = commentjson.load(f)
    else:
        print ("no config file",configfilename)
    data = DataHolder(config)
    print ("Got Here")
    data.sumAcross("Detectors",config["Detectors"])
    data.listTags()
    data.cumulateMe("SP","Events","dummy","ALL",2)