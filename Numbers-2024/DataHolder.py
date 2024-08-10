
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

DEBUG = False

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
        print ("make a new holder")
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
        self.filters={}
        self.tagsets={}
        self.nosum=["Total","Sub-Total"]
        
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
                if self.debug: print (row)
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
        #if self.debug: print ("newTag:",tag, newcategories)
        for category,value in newcategories.items():
            #print ("check",category,value)
            items[self.Indices[category]] = value
        newtag = self.tag(items[0],items[1],items[2],items[3],items[4])
        # if self.debug:
        #     print ("newTag:",tag,newtag)
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
        #print ("csvDump")
        #if self.debug: print ("test of debug")
        result = []
        for tag in self.holder:
            #if self.debug: print (tag)
            fields = tag.split("!")
            result.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3],"units":fields[4]}|self.holder[tag])
        fieldnames = list(result[0].keys())
        with open(newfile, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for line in result:
                writer.writerow(line)
        #return  result
    
    def placeData(self,detector,datatype,resource,location,units,series):
        ' make a new data entry '
        tag = self.tag(detector,datatype,resource,location,units)
        if tag in self.holder:
            print ("WARNING placeData Will overwrite existing", tag)
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
        if self.debug: print("scaleByTag new tag", tag,newtag)
        if tag not in self.holder:
            print ("Atempt to scale a non-existent tag",tag)
            return None
        if newtag in self.holder:
            print ("WARNING scaleByTag will overwrite existing data",newtag)
        else:
            self.holder[newtag]={}
        if self.debug: print("scale",factor)
        for y in self.Years:
            self.holder[newtag][y] = self.holder[tag][y]*factor 
        #print ("newscale",self.holder[tag][2018],self.holder[newtag][2018])
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
        if self.debug: print ("Slice",criteria)
        for tag in self.holder.keys():
            struct = self.tagToDict(tag)
            match = True
            for cat in criteria.keys():
                if self.debug: print ("match",cat,struct[cat],criteria[cat])
                if struct[cat] not in criteria[cat]:
                    match *= False
                    break
            if match: 
                newslice.append(tag)
                if self.debug: print("new slice element",tag)
        self.slices[name] = newslice
        # returns list of tags
        return name
    
    def storeFilter(self,filter=None,name=None):
        self.filters[name]=filter

    def makeTagSet(self,filter=None,name=None):
        ''' pick out things that match certain criteria'''
        newtagset = []
        if self.debug: print ("maketagset:",filter)
        for tag in self.holder.keys():
            struct = self.tagToDict(tag)
            match = True
            for cat in filter.keys():
                if self.debug: print ("maketagset:",cat,struct[cat],filter[cat])
                if struct[cat] not in filter[cat]:
                    if self.debug: print("match fails",cat)
                    match *= False
                    break
            if match: 
                newtagset.append(tag)
                if self.debug: print("maketagset: new tagset element",tag)
        if self.debug: print ("Name is ",name,len(newtagset))
        if name is not None:
            if name in self.tagsets:
                print ("WARNING makeTagSet replacing tagset",name)
            self.tagsets[name]=newtags
            if self.debug: print ("Store tagset",name)
        return newtagset
            
    def sumAcrossFilters(self,filter=None,sumCat=None,sumName="Total"):
        
        newtags = []
        local = filter.copy()
        
        for x in self.nosum:
            if x in local[sumCat]:
                print ("Remove Total from",x,sumCat)
                local[sumCat].remove(x)
        sumover = local[sumCat]
        if self.debug: print ("sumover",sumover)
        if self.debug: print (filter)
        tags = self.makeTagSet(local,None)
        if self.debug: print (tags)
        for tag in tags:
            if self.debug: print ("sumAcrossFilters",{sumCat:sumName})   
            newtag = self.newTag(tag,{sumCat:sumName})
            if self.debug: print ("sumAcrossFilters:",newtag)
            if newtag in self.holder:
                print ("WARNING sumAcrossFilter replacing ", newtag)
            self.holder[newtag]=self.zeroes()
            for field in sumover:
                oldtag = self.newTag(tag,{sumCat:field})
                if oldtag in self.holder:
                    for y in self.Years:              
                        self.holder[newtag][y] += self.holder[oldtag][y]
            newtags.append(newtag)
        if self.debug: print ("sumAcrossFilters:",sumCat,newtags)
        return newtags


    def sumAcrossAll(self,filter=filter,sumName="Total"):
        
        newtags = []
        for category in ["Detectors","DataTypes"]:
            if category == "DataTypes":
                filter["Detectors"]=["Total"]
            print ("All",filter)
            newtags += self.sumAcrossFilters(filter=filter,sumCat=category,sumName=sumName)
        print ("sumacross",newtags)
        
    def sumAcrossSlice(self,category="Detectors",sumOver=None,slice=None,sumName="Total"):
        ' sum across sumOver members of a category and call it sumName'
        totals = {}
        index = self.Indices[category]
        if self.debug:  print ("index",index)
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
            if self.debug: 
                print ("Sums",x,totals[x])
        for x in totals:
            self.holder[x] = totals[x]
            if self.debug: print ("add new total")
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

    def cumulateMe(self,detector,datatype,resource,location,units,categories,period):
        ' cumulate over period years and give it name based on categories '
        tag = self.tag(detector,datatype,resource,location,units)
        if self.debug:  print ("test cumulation")
        if tag not in self.holder:
            print ("cannot cumulate missing tag",tag)
            return None
        if self.debug: 
            print ("precumulate",tag,self.holder[tag])
        newtag = self.newTag(tag,categories)
        new = cumulateMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        if self.debug: 
            print ("postcumlate",newtag,self.holder[newtag])
        return newtag
        
    def extendMe(self,det,datatype,resource,location,units,categories,period): 
        ' extend a category and give it a new name based on categories'
        tag = self.tag(det,datatype,resource,location,units)
        if self.debug: 
            print ("\n preextend",tag,self.holder[tag])
        
        newtag = self.newTag(tag,categories)
        new = extendMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        if self.debug: 
            print ("postextend",newtag,self.holder[newtag])
        return newtag


    def listTags(self):
        ' list all the tags'
        return (list(self.holder.keys()))
    
    def printByTag(self,tag):
        ' print by tag'
        if tag is None or tag not in self.holder:
            print ("WARNING printByTag request to print nonexistent tag",tag)
        else:
            print ("\n",tag,self.holder[tag])
        
    def hasTag(self,detector,datatype,resource,location,units):
        ' is this tag already here'
        return self.tag(detector,datatype,resource,location,units) in self.holder   
    
    def Draw(self,Title,YAxis,Category,filter=filter):
        ''' Name = title at top
        Value = thing to plot
        Category = categories to show as separate lines
        tags = list of tags, needs to be filtered'''
        #print (InYears)
        
        filter[Category] += ["Total"]
        tags = self.makeTagSet(filter)
        if self.debug:
            print("Draw",YAxis,Category,tags)
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
        unitcheck = []
        for tag in tags:
             
            parse = self.parseTag(tag)
            type = parse[self.Indices[Category]]
            units = parse[4]
            if units not in unitcheck:
                unitcheck.append(units)
                if len(unitcheck) > 1:
                    print ("Draw ERROR: units are mixed up - ",unitcheck)
                    return
            if type not in self.DetColors:
                print (type, "not in ",self.DetColors)
                self.DetColors[type]="black"
                self.DetLines[type]="dashed"
            
            ypoints = makeArray(Years,self.holder[tag])
            #print ("y points",Value,type,ypoints)
            ax.plot(Years,ypoints,color=self.DetColors[type],\
            linestyle=self.DetLines[type],label="model "+type)
        
        ax.legend(frameon=False,loc='center left')
        ax.set_title(Title,fontsize=20)
        ax.set_xlabel("Year")
        ax.set_ylabel(YAxis + ", " + units)
        #print("ylim",ax.get_ylim())
        tmp = ax.get_ylim() 
        #print (tmp)
        tmp2 = (tmp[0],tmp[1]*1.2)
        print (tmp,tmp2)
        ax.set_ylim(top=tmp2[1])
        dunestyle.Preliminary()
        plt.grid()
        dunestyle.Preliminary()
        plt.savefig(Title+"-"+YAxis.replace(" ","-")+".png",transparent=False)
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
    data.printByTag(data.tag("SP","Raw-Events","input","Total","Million"))
    newtag = data.scale("SP","Raw-Events","input","Total","Million",{"Units":"TB","Resources":"Store"},10.0)

     
    data.printByTag(newtag)



    print ("\n-------- totals ")
    newtags = data.sumAcross(category="Detectors",sumOver=config["Detectors"],sumName="Total")
    for newtag in newtags:
        data.printByTag(newtag)
    print ("\n-------- cumulate ")

     

    newtag = data.cumulateMe("SP","Raw-Events","input","Total","Million",{"DataTypes":"Events-Cumulative"},2)
    data.printByTag(newtag)

    print ("\n-------- extend")

    newtag = data.extendMe("SP","Raw-Events","input","Total","Million",{"DataTypes":"Events-Extended"},2)
    data.printByTag(newtag)
   
    print ("\n-------- scale ")
    data.printByTag(data.tag("SP","Raw-Events","input","Total","Million"))
    newtag = data.scale("SP","Raw-Events","input","Total","Million",{"DataTypes":"Scaled-Events","Resources":"Test-Scale"},2)
    data.printByTag(newtag)

    print ("\n--- results")
    for tag in data.listTags():
        data.printByTag(tag)

    tags = []
    for detector  in data.Detectors:
        tags.append(data.tag(detector,"Raw-Events","input","Total","Million"))
    print (tags)

    data.Draw("TestPix","RawEVents","Detectors",tags)

    