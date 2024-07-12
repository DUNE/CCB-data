
'''Container for DUNE data volume information'''
import os,commentjson,csv

# pylint: disable=C0303
# pylint: disable=W0621  # reuse external name in method
# pylint: disable=W1514  # don't worry about encoding for open
# pylint: disable=W0105  # let me put a string after ___main___ 
# pylint: disable=C0411  # complaints about import order
# pylint: disable=C0206  # item instead of keys
# pylint: disable=C0201  # item instead of keys



from csv import reader

from NumberUtils import cumulateMap
from NumberUtils import extendMap
from NumberUtils import makeArray
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
import numpy as np
import scipy
import dunestyle.matplotlib as dunestyle

DEBUG = False

class DataHolder:
    ''' Container for data for DUNE data volume estimates

    internally uses tags to split data by
    detector: protodune-VD, FDHD, FDVD ... 
    datatype: events, sim, reco, raw?
    resource: CPU, disk, tape
    location: of the resource (does this need to be separate)
    years:  
    '''

    def __init__(self,theconfig=None):
        ' initialization, needs a config dictionary'
        self.holder={}
        config = theconfig.copy()
        self.Indices = config["Indices"]
        self.Detectors = config["Detectors"] 
        self.DataTypes = config["DataTypes"] 
        self.NativeTypes = config["NativeTypes"]
        self.Resources = config["Resources"] 
        self.Locations = config["Locations"] 
        self.config=config
        self.MaxYear = config["MaxYear"]
        self.MinYear = config["MinYear"]
        self.Units = config["Units"]
        
        print ("detectors",self.Detectors)
        self.Years = config["Years"]
        self.size = len(self.Years)
        self.PlotYears = []
        for i in range(self.MinYear,self.MaxYear+1):
            self.PlotYears.append(i)
        
                    
# fill out the actual data array

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
                #print (det)
                if det not in self.Detectors:
                    print ("unrecognized detector",det)
                    continue
                    
                thetype = row[1].strip()
                if thetype not in  self.DataTypes:
                    print ("unrecognized datatype", thetype)

                local = {}
                for year in self.Years:       
                    local[year] = float(row[year - self.Years[0]+2])
                if not self.hasTag(det,thetype,"dummy","ALL"):
                    self.placeData(detector=det,datatype=thetype,resource="dummy",location="ALL",series=local)
        csvfile.close()
        if DEBUG:
            for x in self.holder:
                print ( x, self.holder)      
       
        # self.RequestYear=2024
        # if "RequestYear" in config:
        #     self.RequestYear= config["RequestYear"]

        # self.MWCWeight=config["MWCWeight"]    
        # self.Cap = config["Cap"]
        # self.BaseMemory = config["Base-Memory"]
        # self.CombinedDetectors = config["CombinedDetectors"]
        self.DetectorParameters = list(config["SP"].keys())


        if "Comment" in self.DetectorParameters:
            self.DetectorParameters.remove("Comment")

        
        # self.PerYear = config["PerYear"]
        # # plot config
        self.DetColors=config["DetColors"]
        self.DetLines = config["DetLines"]
        # self.TypeColors=config["TypeColors"]
        # self.TypeLines = config["TypeLines"]
        # self.PatternFraction = config["PatternFraction"]
        # self.SplitsYear = config["SplitsYear"]
        # self.SplitsEarly = config["SplitsEarly"]
        # self.SplitsLater = config["SplitsLater"]
       

    def tag(self,detector,datatype,resource,location):
        ' make a tag from the categories '
        return "%s!%s!%s!%s"%(detector,datatype,resource,location)
    
    def parseTag(self,tag):
        ' make a list of categories from a tag'
        items = tag.split("!")
        return items
    
    def newTag(self,tag,newcategories):
        'generate a new tag with newkey substituted in category'
        items = self.parseTag(tag)
        for category,value in newcategories.items():
            items[self.Indices[category]] = value
        newtag = self.tag(items[0],items[1],items[2],items[3])
        if DEBUG:
            print ("newtag",tag,newtag)
        return newtag
    
    
    def checkIfInTag(self,tag,category,value):
        ' true if value is in right category in tag '
        index = self.Indices(category)
        return self.parseTag(tag)[index] == value
    
    def getData(self,detector,datatype,resource,location):
        ' return data by categories '
        return  self.holder[self.tag(detector,datatype,resource,location)]
    
    def jsonDump(self,newfile):
        newfile = newfile.replace(".json","_holder.json")
        newlist = []
        for tag in self.holder:
            fields = tag.split("!")
            newlist.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3]}|self.holder[tag])
        f = open(newfile,'w')
        commentjson.dump(newlist,f,indent=4)
        f.close()
        return True
    
    def csvDump(self,newfile):
        ' return data by categories '
        
        result = []
        for tag in self.holder:
            print (tag)
            fields = tag.split("!")
            result.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3]}|self.holder[tag])
        fieldnames = list(result[0].keys())
        with open(newfile, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for line in result:
                writer.writerow(line)
        return  result
    
    def placeData(self,detector,datatype,resource,location,series):
        ' make a new data entry '
        tag = self.tag(detector,datatype,resource,location)
        if tag in self.holder:
            print ("Will overwrite existing", tag)
        self.holder[tag] = series
        return tag

    def makeEmpty(self,detector,datatype,resource,location):
        ' make a new data entry  full of zeros'
        return self.placeData(self,detector,datatype,resource,location,self.zeroes)


    def zeroes(self):
        ' make an array of zeroes'
        new = {}
        for y in self.Years:
            new[y] = 0.0
        return new
    
    def scaleByTag(self,tag,categories,factor):
        ' scale a time series by factor and rename with the keys listed in categories'
        newtag = self.newTag(tag,categories)
        if tag not in self.holder:
            print ("Atempt to scale a non-existent tag",tag)
        if newtag in self.holder:
            print ("will overwrite existing data",newtag)
        else:
            self.holder[newtag]={}
        for y in self.Years:
            self.holder[newtag][y] = round(self.holder[tag][y]*factor,3)
        return newtag

    def scale(self,detector,datatype,resource,location,categories,factor):
        ' scale a time series by factor and rename with the keys listed in categories'
        tag = self.tag(detector,datatype,resource,location)
        return self.scaleByTag(tag,categories,factor)
    
    def combineByTag(self,tags,newtag):
    
        self.holder[newtag]=self.zeroes()
        for tag in tags:
            if tag not in self.holder:
                print ("combineByTag skipping tag",tag)
                continue
            for y in self.Years:
                self.holder[newtag][y] += self.holder[tag][y]
        return newtag
        
    def sumAcross(self,category="Detectors",sumOver=None,sumName="Total"):
        ' sum across sumOver members of a category and call it sumName'
        totals = {}
        index = self.Indices[category]
        if DEBUG: print ("index",index)
        for tag in self.holder.keys():
            types = self.parseTag(tag)
            if types[index] == "Total": continue
            if types[index] not in sumOver: continue
            sumtag = tag.replace(types[index],sumName) 
            if sumtag not in totals:
                #print ("make a new total",sumtag)
                totals[sumtag]=self.zeroes()
            for y in self.Years:
                totals[sumtag][y]+=self.holder[tag][y]
        for x in totals:
            if DEBUG:
                print ("Sums",x,totals[x])
        for x in totals:
            self.holder[x] = totals[x]
        return list(totals.keys())
    
    def removeTag(self,tag):
        if tag in self.holder:
            self.holder.pop(tag)
            print ("tag",tag,"removed")

    def cumulateMe(self,det,datatype,resource,location,categories,period):
        ' cumulate over period years and give it name based on categories '
        tag = self.tag(det,datatype,resource,location)
        if DEBUG: print ("test cumulation")
        if tag not in self.holder:
            print ("cannot cumulate missing tag",tag)
            return None
        if DEBUG:
            print ("precumulate",tag,self.holder[tag])
        newtag = self.newTag(tag,categories)
        new = cumulateMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        if DEBUG:
            print ("postcumlate",newtag,self.holder[newtag])
        return newtag
        
    def extendMe(self,det,datatype,resource,location,categories,period): 
        ' extend a category and give it a new name based on categories'
        tag = self.tag(det,datatype,resource,location)
        if DEBUG:
            print ("\n preextend",tag,self.holder[tag])
        
        newtag = self.newTag(tag,categories)
        new = extendMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        if DEBUG:
            print ("postextend",newtag,self.holder[newtag])
        return newtag


    def listTags(self):
        ' list all the tags'
        return (list(self.holder.keys()))
    
    def printByTag(self,tag):
        ' print by tag'
        if tag is None or tag not in self.holder:
            print ("request to print nonexistent tag",tag)
        else:
            print ("\n",tag,self.holder[tag])
        
    def hasTag(self,detector,datatype,resource,location):
        ' is this tag already here'
        return self.tag(detector,datatype,resource,location) in self.holder   
    
    def Draw(self,Name,Value,tags):
        #print (InYears)

        Years = np.array(self.PlotYears)
        
        maxyears = Years[len(Years)-1]

        fig=plt.figure(figsize=(10,5))
        ax = fig.add_axes([0.2,0.2,0.7,0.7])
        ax.set_xlim(Years[0],maxyears)
        if len(Years)<10:
            ax.xaxis.set_major_locator(MultipleLocator(1))
        else:
            ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.spines['bottom'].set_position('zero')
        #print (Data)
        
        for tag in tags:
            parse = self.parseTag(tag)
            type = parse[0]
            if type not in self.DetColors:
                print (type, "not in ",self.DetColors)
            else:
                ypoints = makeArray(Years,self.holder[tag])
            #print ("y points",Value,type,ypoints)
                ax.plot(Years,ypoints,color=self.DetColors[type],\
                linestyle=self.DetLines[type],label="model "+type)
        
        ax.legend(frameon=False,loc='center left')
        ax.set_title(Name,fontsize=20)
        ax.set_xlabel("Year")
        ax.set_ylabel(Value + ", " + self.Units[Value])
        #print("ylim",ax.get_ylim())
        tmp = ax.get_ylim() 
        #print (tmp)
        tmp2 = (tmp[0],tmp[1]*1.2)
        print (tmp,tmp2)
        ax.set_ylim(top=tmp2[1])
        dunestyle.Preliminary()
        plt.grid()
        dunestyle.Preliminary()
        plt.savefig(Name+"-"+Value.replace(" ","-")+".png",transparent=False)
        #plt.savefig(Value+"_w.jpg",transparent=False)

        plt.show()



if __name__ == '__main__':
    ' test the methods'
    configfilename = "NearTerm_2024-06-12-2040.json"
    if os.path.exists(configfilename):
        with open(configfilename,'r') as f:
            config = commentjson.load(f)
    else:
        print ("no config file",configfilename)

    data = DataHolder(config)

    print ("\n--- inputs")
    for tag in data.listTags():
        data.printByTag(tag)

    print ("\n-------- totals ")
    newtags = data.sumAcross(category="Detectors",sumOver=config["Detectors"],sumName="Total")
    for newtag in newtags:
        data.printByTag(newtag)
    print ("\n-------- cumulate ")

    newtag = data.cumulateMe("SP","Events","dummy","ALL",{"DataTypes":"Events-Cumulative"},2)
    data.printByTag(newtag)

    print ("\n-------- extend")

    newtag = data.extendMe("SP","Events","dummy","ALL",{"DataTypes":"Events-Extended"},2)
    data.printByTag(newtag)
   
    print ("\n-------- scale ")
    data.printByTag(data.tag("SP","Events","dummy","ALL"))
    newtag = data.scale("SP","Events","dummy","ALL",{"DataTypes":"Scaled-Events","Resources":"Test-Scale"},2)
    data.printByTag(newtag)

    print ("\n--- results")
    for tag in data.listTags():
        data.printByTag(tag)

    tags = []
    for detector  in data.Detectors:
        tags.append(data.tag(detector,"Events","dummy","ALL"))
    print (tags)

    data.Draw("TestPix","Events",tags)

    