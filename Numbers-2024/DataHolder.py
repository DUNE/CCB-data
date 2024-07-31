
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
#import scipy
import dunestyle.matplotlib as dunestyle

DEBUG = True

class DataHolder:
    ''' Container for data for DUNE data volume estimates

    internally uses tags to split data by
    detector: protodune-VD, FDHD, FDVD ... 
    datatype: events, sim, reco, raw?
    resource: CPU, disk, tape
    location: of the resource (does this need to be separate)
    units: units
    years:  
    '''

    def __init__(self,theconfig=None,name="Base",debug=False):
        ' initialization, needs a config dictionary'
        self.holder={}
        self.name = name
        config = theconfig.copy()
        self.Indices = config["Indices"]
        self.Detectors = config["Detectors"] 
        self.DataTypes = config["DataTypes"] 
        self.NativeTypes = config["NativeTypes"]
        self.Resources = config["Resources"] 
        self.Locations = config["Locations"] 
        self.Units = config["Units"]
        self.config=config
        self.MaxYear = config["MaxYear"]
        self.MinYear = config["MinYear"]
        self.PlotUnits = config["Units"]
        self.debug = debug
        print ("detectors",self.Detectors)
        self.Years = config["Years"]
        self.size = len(self.Years)
        self.PlotYears = []
        for i in range(self.MinYear,self.MaxYear+1):
            self.PlotYears.append(i)
        self.slices={}
        self.DetColors=config["DetColors"]
        self.DetLines = config["DetLines"]
        
# fill out the actual data arrays
    def readTimeline(self):
        'read in the individual timelines from csv file'
        if "Timeline" in self.config:
            print ("Timeline from ", self.config["Timeline"])
        if not os.path.exists(self.config["Timeline"]):
            print ("timeline file ", self.config["Timeline"]," does not exist:")
        
        counter = 0
        with open(self.config["Timeline"], newline='') as csvfile:
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
                resource = row[2].strip()
                location = row[3].strip()
                units = row[4].strip()
                local = {}
                for year in self.Years:       
                    local[year] = float(row[year - self.Years[0]+5])
                if not self.hasTag(det,thetype,resource,location,units):
                    self.placeData(detector=det,datatype=thetype,resource=resource,location=location,units=units,series=local)
        csvfile.close()
        # if DEBUG:
        #     for x in self.holder:
        #         print ( x, self.holder)      
       
        # self.RequestYear=2024
        # if "RequestYear" in config:
        #     self.RequestYear= config["RequestYear"]

        # self.MWCWeight=config["MWCWeight"]    
        # self.Cap = config["Cap"]
        # self.BaseMemory = config["Base-Memory"]
        # self.CombinedDetectors = config["CombinedDetectors"]

        # self.DetectorParameters = list(config["SP"].keys())


        # if "Comment" in self.DetectorParameters:
        #     self.DetectorParameters.remove("Comment")
        
        
       

    def tag(self,detector,datatype,resource,location,units):
        ' make a tag from the categories '
        return "%s!%s!%s!%s!%s"%(detector,datatype,resource,location,units)
    
    def parseTag(self,tag):
        ' make a list of categories from a tag'
        items = tag.split("!")
        return items
    
    def tagToDict(self,tag):
        ' make a dict of categories from a tag'
        catlist = tag.split("!")
        newdict = {}
        #if DEBUG: print (catlist,self.Indices)
        for cat,index in self.Indices.items(): 
            if index >= len(catlist): continue
            #if DEBUG: print (cat,index)
            value = catlist[index]
            newdict[cat]=value
        return newdict
    
    def newTag(self,tag,newcategories):
        'generate a new tag with newkey substituted in category'
        items = self.parseTag(tag)
        if self.debug: print ("newTag",tag, newcategories)
        for category,value in newcategories.items():
            print ("check",category,value)
            items[self.Indices[category]] = value
        newtag = self.tag(items[0],items[1],items[2],items[3],items[4])
        if DEBUG:
            print ("newtag",tag,newtag)
        return newtag
    
    
    def checkIfInTag(self,tag,category,value):
        ' true if value is in right category in tag '
        index = self.Indices(category)
        return self.parseTag(tag)[index] == value
    
    def getData(self,detector,datatype,resource,location,units):
        ' return data by categories '
        return  self.holder[self.tag(detector,datatype,resource,location,units)]
    
    def clearHolder(self):
        ' clear out the list of series but keep configuration'
        self.holder={}

    def jsonDump(self,newfile):
        newfile = newfile.replace(".json","_holder.json")
        newlist = []
        for tag in self.holder:
            fields = tag.split("!")
            newlist.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3],"units":fields[4]}|self.holder[tag])
        f = open(newfile,'w')
        commentjson.dump(newlist,f,indent=4)
        f.close()
        return True
    
    def printSlice(self,name=None):
        for x in self.slices[name]:
            print("slice", name,x,self.holder[x])
    
    def csvDump(self,newfile):
        ' return data by categories '
        
        result = []
        for tag in self.holder:
            print (tag)
            fields = tag.split("!")
            result.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3],"units":fields[4]}|self.holder[tag])
        fieldnames = list(result[0].keys())
        with open(newfile, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for line in result:
                writer.writerow(line)
        return  result
    
    def placeData(self,detector,datatype,resource,location,units,series):
        ' make a new data entry '
        tag = self.tag(detector,datatype,resource,location,units)
        if tag in self.holder:
            print ("Will overwrite existing", tag)
        self.holder[tag] = series
        return tag

    # def makeEmpty(self,detector,datatype,resource,location,units):
    #     ' make a new data entry  full of zeros'
    #     return self.placeData(self,detector,datatype,resource,location,units,self.zeroes)


    def zeroes(self):
        ' make an array of zeroes'
        new = {}
        for y in self.Years:
            new[y] = 0.0
        return new
    
    def scaleByTag(self,tag,categories,factor):
        ' scale a time series by factor and rename with the keys listed in categories'
        newtag = self.newTag(tag,categories)
        if self.debug: print(tag)
        if tag not in self.holder:
            print ("Atempt to scale a non-existent tag",tag)
        if newtag in self.holder:
            print ("will overwrite existing data",newtag)
        else:
            self.holder[newtag]={}
        if self.debug: print("scale",factor)
        for y in self.Years:
            self.holder[newtag][y] = self.holder[tag][y]*factor 
        print ("newscale",self.holder[tag][2018],self.holder[newtag][2018])
        if self.debug: print(newtag)
        return newtag

    def scale(self,detector,datatype,resource,location,units,categories,factor):
        ' scale a time series by factor and rename with the keys listed in categories'
        tag = self.tag(detector,datatype,resource,location,units)
        if self.debug: print ("scale:",tag)
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
    
    def makeSlice(self,criteria=None,name=None):
        ''' pick out things that match certain criteria'''
        newslice = []
        if DEBUG: print ("Slice",criteria)
        for tag in self.holder.keys():
            struct = self.tagToDict(tag)
            match = True
            for cat in criteria.keys():
                if DEBUG: print ("match",cat,struct[cat],criteria[cat])
                if struct[cat] not in criteria[cat]:
                    match *= False
                    break
            if match: 
                newslice.append(tag)
                if DEBUG: print("new slice element",tag)
        self.slices[name] = newslice
        # returns list of tags
        return name
    
    def makeFilter(self,criteria=None):
        ''' pick out things that match certain criteria'''
        newfilter = []
        if DEBUG: print ("Slice",criteria)
        for tag in self.holder.keys():
            struct = self.tagToDict(tag)
            match = True
            for cat in criteria.keys():
                if DEBUG: print ("match",cat,struct[cat],criteria[cat])
                if struct[cat] not in criteria[cat]:
                    match *= False
                    break
            if match: 
                newfilter.append(tag)
                if DEBUG: print("new slice element",tag)
        return newfilter
            
    def sumAcrossFilters(self,filters=None,sumCat=None,sumName="Total"):
        
        newtags = []
        sumover = filters.pop(sumCat)
        print ("sumover",sumover)
        print (filters)
        tags = self.makeFilter(filters)
        print (tags)
        for tag in tags:
            print ("sumAcrossFilters",{sumCat:sumName})
            newtag = self.newTag(tag,{sumCat:sumName})
            print ("sumAcrossFilters:",newtag)
            if newtag in self.holder:
                print ("sumAcrossFilter replacing ", newtag)
            self.holder[newtag]=self.zeroes()
            for field in sumover:
                oldtag = self.newTag(tag,{sumCat:field})
                for y in self.Years:              
                    self.holder[newtag][y] += self.holder[oldtag][y]
            newtags.append(newtag)
        print (newtags)

                
        

                
                
    
        
    def sumAcrossSlice(self,category="Detectors",sumOver=None,slice=None,sumName="Total"):
        ' sum across sumOver members of a category and call it sumName'
        totals = {}
        index = self.Indices[category]
        if DEBUG: print ("index",index)
        inputs = []
        if slice == None:
            inputs = self.holder.keys()
        else:
            inputs = self.slices[slice]
            #sumName = slice + ":" + sumName
        if sumName in self.slices:
            print ("WARNING: overwriting a slice",sumName)
        self.slices[sumName]=[]
        for tag in inputs:
            types = self.parseTag(tag)
            if "Total" in types[index]: continue
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
            print ("add new total")
            self.slices[sumName].append(x)
        return list(totals.keys())
    
    def copyToNewHolder(self,otherholder=None,slice=None):
        ' copy specific items listed in tags to another holder'
        for x in self.slices[slice]:
            otherholder.holder[x] = self.holder[x].copy()
        otherholder.slices[slice]=self.slices[slice]

            
    
    def removeTag(self,tag):
        if tag in self.holder:
            self.holder.pop(tag)
            print ("tag",tag,"removed")

    def cumulateMe(self,det,datatype,resource,location,units,categories,period):
        ' cumulate over period years and give it name based on categories '
        tag = self.tag(det,datatype,resource,location,units)
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
        
    def extendMe(self,det,datatype,resource,location,units,categories,period): 
        ' extend a category and give it a new name based on categories'
        tag = self.tag(det,datatype,resource,location,units)
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
        
    def hasTag(self,detector,datatype,resource,location,units):
        ' is this tag already here'
        return self.tag(detector,datatype,resource,location,units) in self.holder   
    
    def Draw(self,Name,Value,Category,tags=None):
        #print (InYears)
        if tags == None:  tags = self.holder.keys()
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
        units = "unknown"
        for tag in tags:
            parse = self.parseTag(tag)
            type = parse[self.Indices[Category]]
            units = parse[4]
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
        ax.set_ylabel(Value + ", " + units)
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
    configfilename = "NearTerm_2024-07-12-2040.json"
    if os.path.exists(configfilename):
        with open(configfilename,'r') as f:
            config = commentjson.load(f)
    else:
        print ("no config file",configfilename)

    data = DataHolder(config)
    data.readTimeline()

    print ("\n--- inputs")
    for tag in data.listTags():
        data.printByTag(tag)

    print ("\n-------- scaling ")
    data.printByTag(data.tag("SP","Raw-Events","input","ALL","Million"))
    newtag = data.scale("SP","Raw-Events","input","ALL","Million",{"Units":"TB","Resources":"Store"},10.0)

     
    data.printByTag(newtag)



    print ("\n-------- totals ")
    newtags = data.sumAcross(category="Detectors",sumOver=config["Detectors"],sumName="Total")
    for newtag in newtags:
        data.printByTag(newtag)
    print ("\n-------- cumulate ")

     

    newtag = data.cumulateMe("SP","Raw-Events","input","ALL","Million",{"DataTypes":"Events-Cumulative"},2)
    data.printByTag(newtag)

    print ("\n-------- extend")

    newtag = data.extendMe("SP","Raw-Events","input","ALL","Million",{"DataTypes":"Events-Extended"},2)
    data.printByTag(newtag)
   
    print ("\n-------- scale ")
    data.printByTag(data.tag("SP","Raw-Events","input","ALL","Million"))
    newtag = data.scale("SP","Raw-Events","input","ALL","Million",{"DataTypes":"Scaled-Events","Resources":"Test-Scale"},2)
    data.printByTag(newtag)

    print ("\n--- results")
    for tag in data.listTags():
        data.printByTag(tag)

    tags = []
    for detector  in data.Detectors:
        tags.append(data.tag(detector,"Raw-Events","input","ALL","Million"))
    print (tags)

    data.Draw("TestPix","RawEVents","Detectors",tags)

    