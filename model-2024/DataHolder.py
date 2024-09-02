
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
        self.test = config["Test"]
        self.Indices = config["Indices"]
        
        self.Detectors = config["Detectors"] 
        self.DataTypes = config["DataTypes"] 
        if self.test:
            self.Detectors = config["TestDetectors"] 
            self.DataTypes = config["TestTypes"] 
            
        self.NativeTypes = config["NativeTypes"]
        self.Resources = config["Resources"] 
        self.Locations = config["Locations"] 
        self.Units = config["Units"]
        self.UnitFormats = config["UnitFormats"]
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
        #self.slices={}
        self.DetColors=config["DetColors"]
        self.DetLines = config["DetLines"]
        self.filters={}
        self.tagsets={}
        self.nosum=["Total","Sub-Total"]
        self.explanation={}
        self.showPlot=False
        
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
                    self.placeData(detector=det,datatype=thetype,resource=resource,location=location,units=units,series=local,explanation="Inputs from "+self.config["Timeline"])
        csvfile.close()
        
    def tag(self,detector,datatype,resource,location,units):
        ' make a tag from the categories '
        return "%s!%s!%s!%s!%s"%(detector,datatype,resource,location,units)
    
    def tagToList(self,tag):
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
        'generate a new tag with the info in newcategories substituted in category'
        items = self.tagToList(tag)
        if self.debug: print ("newTag:",tag, newcategories)
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
        return self.tagToList(tag)[index] == value
    
    def getData(self,detector,datatype,resource,location,units):
        ' return data by categories '
        return  self.holder[self.tag(detector,datatype,resource,location,units)]
    
    def clearHolder(self):
        ' clear out the list of series but keep configuration'
        self.holder={}

    def jsonDump(self,dir=".",name="test.json"):
        'Dump the holder in json format'
        name = name.replace(".json","_holder.json")
        newlist = []
        for tag in self.holder:
            fields = tag.split("!")
            newlist.append({"detector":fields[0],"datatype":fields[1],"resource":fields[2],"location":fields[3],"units":fields[4]}| self.holder[tag]|{"Explanation":self.explanation[tag]})
        f = open(os.path.join(dir,name),'w')
        commentjson.dump(newlist,f,indent=4)
        f.close()
        return True
    
    def csvDump(self,dir=".",name="empty.csv",plotrange=True,filter=None,dropColumns=None,format="%.3f"):
        'Dump the holder in csv format, restrict to plot yeas if plotrange is True '
        #print ("csvDump")
        #if self.debug: print ("test of debug")
        result = []
    
        if filter is None:
            tags = self.holder.keys()
        else:
            tags = self.makeTagSet(filter)

        for tag in tags:
        
            newline=None
            if not plotrange:
                newline = (self.tagToDict(tag) | self.holder[tag] | {"Explanation":self.explanation[tag]})
            else:
                short = {}
                for year in range(self.MinYear,self.MaxYear+1):
                    short[year]=format%self.holder[tag][year]
                newline = (self.tagToDict(tag) | short | {"Explanation":self.explanation[tag]})
            #print (newline)
            if dropColumns is not None:
                for x in dropColumns:
                    newline.pop(x)
            result.append(newline)
            
                
                
        if len(result) > 0:
            fieldnames = list(result[0].keys())

            print (dir,name)    
            with open(os.path.join(dir,name), 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for line in result:
                    writer.writerow(line)
            return os.path.join(dir,name)
        else:
            return None
    
    def placeData(self,detector,datatype,resource,location,units,series,explanation=None):
        ' make a new data entry '
        tag = self.tag(detector,datatype,resource,location,units)
        if tag in self.holder:
            print ("WARNING placeData Will overwrite existing", tag)
        self.holder[tag] = series
        self.explanation[tag] = explanation
        return tag

    def zeroes(self):
        ' make an array of zeroes'
        new = {}
        for y in self.Years:
            new[y] = 0.0
        return new
    
    def scaleByTag(self,tag,categories,factor,explanation=None):
        ' scale a time series by factor and rename with the keys listed in categories'

        if tag not in self.holder:
        #     print ("Atempt to scale a non-existent tag",tag)
            return None
        newtag = self.newTag(tag,categories)
        if newtag in self.holder:
            print ("WARNING scaleByTag will overwrite existing data",newtag)
        else:
            self.holder[newtag]={}
        if self.debug: print("scale",factor)
        for y in self.Years:
            self.holder[newtag][y] = self.holder[tag][y]*factor 
        self.explanation[newtag]=explanation
        #print ("newscale",self.holder[tag][2018],self.holder[newtag][2018])
        if self.debug: print(newtag)
        return newtag

    def scale(self,detector,datatype,resource,location,units,categories,factor,explanation=None):
        ' scale a time series by factor and rename with the keys listed in categories'
        tag = self.tag(detector,datatype,resource,location,units)
        if self.debug: print ("scale:",tag)
        return self.scaleByTag(tag,categories,factor,explanation)
    
    def cleanFilter(self,filter=None):
        thefilter = filter.copy()
        if self.debug: print("raw filter",filter)
        defaults = {"Detectors":self.Detectors,
                    "DataTypes":self.DataTypes,
                    "Resources":self.Resources,
                    "Locations":self.Locations+["Total"],
                    "Units":None
                    }
        for x,default in defaults.items():
            if x not in thefilter:
                thefilter[x] = default
                if self.debug:
                    print("adding default to filter",x,default)
        for x,value in thefilter.items():
            if x == "Units" and value == None:
                print ("must supply units for any filter")
                return {}
            #print ("cleanFilter:",x,type(value))
            if type(value) is not list:
                thefilter[x] = [value]
                print("WARNING: filter has wrong entry type - correcting",x,value,thefilter[x])
        if self.debug: print("full filter",thefilter)
        return thefilter

        
    def storeFilter(self,filter=None,name=None):
        self.filters[name]=self.cleanFilter(filter)

    def makeTagSet(self,filter=None,name=None):
        ''' pick out things that match certain criteria'''
        newtagset = []
        filter=self.cleanFilter(filter)
        if self.debug: print ("maketagset:",filter,name)
        for detector in filter["Detectors"]:
            for datatype in filter["DataTypes"]:
                for resource in filter["Resources"]:
                    for location in filter["Locations"]:
                        for unit in filter["Units"]:
                            tag = self.tag(detector,datatype,resource,location,unit)
                            if self.debug: print ("new tag",tag)
                            if tag not in self.holder:
                                if self.debug: print ("tag not in holder",tag)
                                continue
                            newtagset.append(tag)
    
        if name is not None:
            if name in self.tagsets:
                print ("WARNING makeTagSet replacing tagset",name)
            self.tagsets[name]=newtags
            if self.debug: print ("Store tagset",name)
        if self.debug:
            for t in newtagset:
                print ("new tag",t)
        return newtagset
            
    def sumAcrossFilters(self,filter=None,sumCat=None,sumName="Total",explanation=None):
        newtags = []
        local = self.cleanFilter(filter.copy())
        
        for x in self.nosum:
            if x in local[sumCat]:
                if self.debug: print ("Remove Total from",x,sumCat)
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
            #if newtag in self.holder:
                #print ("WARNING sumAcrossFilter replacing ", newtag)
            self.holder[newtag]=self.zeroes()
            self.explanation[newtag]=explanation
            for field in sumover:
                oldtag = self.newTag(tag,{sumCat:field})
                if oldtag in self.holder:
                    for y in self.Years:              
                        self.holder[newtag][y] += self.holder[oldtag][y]
            if self.debug:
                print (newtag,self.holder[newtag])
            if newtag not in newtags:
                newtags.append(newtag)
            else:
                if self.debug: print ("WARNING: possible duplicate tag",newtag)
                
        if self.debug: print ("sumAcrossFilters:",sumCat,newtags)
        return newtags


    def sumAcrossAll(self,filter=filter,sumName="Total",explanation=None):
        
        newtags = []
        if self.debug:
            print ("sumacross",filter)
        for category in ["Detectors","DataTypes"]:
            newtags += self.sumAcrossFilters(filter=filter,sumCat=category,sumName=sumName,explanation=explanation)
        # make Total Total
        newfilter=filter.copy()
        newfilter["Detectors"]=[sumName]
        if self.debug:
            print ("sumacross", newfilter)
        newtags += self.sumAcrossFilters(filter=newfilter,sumCat="DataTypes",sumName=sumName,explanation=explanation)
        return newtags
        #print ("sumacross",newtags)
    
    # def copyToNewHolder(self,otherholder=None,filter=None):
    #      ' copy specific items listed in tags to another holder'
    #      tags = maketagset(filter)
    #      for x in self.slices[slice]:
    #          otherholder.holder[x] = self.holder[x].copy()
    #      otherholder.slices[slice]=self.slices[slice]
  
    def removeTag(self,tag):
        if tag in self.holder:
            self.holder.pop(tag)
            self.explanation.pop(tag)
            print ("tag",tag,"removed")

    def cumulateMe(self,detector,datatype,resource,location,units,categories,period,explanation=None):
        ' cumulate over period years and give it name based on categories '
        tag = self.tag(detector,datatype,resource,location,units)
        if self.debug:  print ("test cumulation")
        if tag not in self.holder:
            if self.debug: print ("WARNING: cannot cumulate missing tag",tag)
            return None
        if self.debug: 
            print ("precumulate",tag,self.holder[tag])
        newtag = self.newTag(tag,categories)
        new = cumulateMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        self.explanation[newtag]=explanation
        if self.debug: 
            print ("postcumlate",newtag,self.holder[newtag])
        return newtag
        
    def extendMe(self,det,datatype,resource,location,units,categories,period,explanation=None): 
        ' extend a category and give it a new name based on categories'
        tag = self.tag(det,datatype,resource,location,units)
        if self.debug: 
            print ("\n preextend",tag,self.holder[tag])
        newtag = self.newTag(tag,categories)
        new = extendMap(self.Years,self.holder[tag],period)
        self.holder[newtag]=new
        self.explanation[newtag]=explanation
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
            print ("\n",tag,self.holder[tag],self.explanation[tag])
        
    def hasTag(self,detector,datatype,resource,location,units):
        ' is this tag already here'
        return self.tag(detector,datatype,resource,location,units) in self.holder   
    
    def Draw(self,Dir,Title,YAxis,Resource,Category,filter=filter,format=None):
        ''' 
        Dir = directory to put in
        Title = title at top and name of output file
        YAxis = label for the Y axis 
        Category = categories to show as separate lines
        thefilter = filter to use to define plot'''
        #print (InYears)
        thefilter = filter.copy()
        print ("precheck", thefilter)
        if "Total" not in thefilter[Category]:
            print ("adding Total to ",thefilter[Category])
            thefilter[Category] +=  ["Total"]
        thefilter["Resources"]=[Resource]
        if self.debug: print ("draw filter",thefilter)
        tags = self.makeTagSet(thefilter)

        # figure out units - CPU has several so a bit complex
        if format is None:
            format = self.UnitFormats[filter["Units"][0]]
            if len(format) > 1 and " " in Resource:
                unit = Resource.split(" ")[1]
                
                format = self.UnitFormats[unit]
                print ('unit',Resource,unit,format)
                
            #print ("set format",Title,filter["Units"], format)
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
            #parse = self.tagToList(tag)
            tagDict = self.tagToDict(tag)
            type = tagDict[Category]
            units = tagDict["Units"]
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
        #print (tmp,tmp2)
        ax.set_ylim(top=tmp2[1])
        dunestyle.Preliminary()
        plt.grid()
        dunestyle.Preliminary()
        #savename = (Dir+"/"+Dir+"_").replace("/._","/")+Title.replace(" ","-")+"-"+YAxis.replace(" ","-")+".png"
        savename = (Dir+"/").replace("/._","/")+Title.replace(" ","-")+"-"+YAxis.replace(" ","-")+".png"
        plt.savefig(savename,transparent=False)
        tablename = os.path.basename(savename.replace(".png",".csv"))
        drops = ["Resources","Explanation","Detectors","DataTypes","Locations","Units"]
        drops.remove(Category)
        self.csvDump(Dir,name=tablename,filter=thefilter,dropColumns=drops,format=format)
        #plt.savefig(Value+"_w.jpg",transparent=False)

        if self.showPlot: 
            plt.show()
        else:
            plt.close()
        return savename
    
    def TexFigure(self,name,caption,label=None):
        if label is None: label = name
        label = label.replace(" ","-")
        s = "\\begin{figure}[h]\n\\centering"
        s += "\\includegraphics[height=0.4\\textwidth]{%s}"%((name))
        s += "\\caption{%s}\n"%caption
        s += "\\label{fig:%s}\n"%label
        s += "\\end{figure}\n"
        return s
    
    def TexTable(self,name,caption,label):
        label = label.replace(" ","-")
        s = "\\begin{table}[h]\n\\centering"
        s += "{\\footnotesize\\csvautotabularright{%s}}"%((name))
        s += "\\label{tab:%s}\n"%label
        s += "\\caption{%s}\n"%caption
        s += "\\end{table}\n"
        return s
    
    def TexBoth2(self,figname,caption,label=None):
        
        if figname is None:
            return "%% empty file"+figname
        
        csvname = figname.replace(".png",".csv")
        texname = figname.replace(".png",".tex")
        texfile = open(texname,'w')
        if label is None: label = name
        label = label.replace(" ","-")
        s = "\\begin{figure}[ht]\n\\centering"
        s += "\\includegraphics[height=0.4\\textwidth]{%s}"%((figname))
        #print (s)
        s += "\\end{figure}\n"
        s += self.TexTable(csvname,caption,label)
        s += "\\pagebreak\n"
        texfile.write(s)
        texfile.close()
        return s

    def TexBoth(self,figname,caption,label=None):
        
        if figname is None:
            return "%% empty file"+figname
        csvname = figname.replace(".png",".csv")
        texname = figname.replace(".png",".tex")
        texfile = open(texname,'w')
        if label is None: label = name
    
        label = label.replace(" ","-").replace("_","-")
        if self.debug: print ("names", figname,csvname,texname,label)
        s = "\\begin{figure}[ht]\n\\centering\n"
        s += "\\includegraphics[height=0.4\\textwidth]{%s}"%((figname))
        #print (s)
        s += "\\\\"
        s += "{\\footnotesize\\csvautotabularright{%s}}"%((csvname))
        s += "\\label{tab:%s}\n"%label
        s += "\\caption{%s}\n"%caption
        s += "\\end{figure}\n"
        #s += self.TexTable(csvname,caption,label)

        s += "\\pagebreak\n"
        texfile.write(s)
        texfile.close()
        return s

    


if __name__ == '__main__':
    ' test the methods'
    configfilename = "NearTerm_2024-08-14-2040.json"
    if os.path.exists(configfilename):
        with open(configfilename,'r') as f:
            config = commentjson.load(f)
    else:
        print ("no config file",configfilename)

    texfile = "test.tex"
    
    tex = open("test.tex",'w')
    tex.write("\\input Header.tex\n")


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
    
    filter = {"Detectors":data.Detectors,"DataTypes":["Test","TP"],"Resources":"input","Locations":"Total","Units":"TB"}
    newtags = data.sumAcrossAll(filter=filter,sumName="Total",explanation="Test of sumAcross Detectors")
    for newtag in newtags:
        data.printByTag(newtag)
    print ("\n-------- cumulate ")

     

    newtag = data.cumulateMe("SP","Raw-Events","input","Total","Million",{"DataTypes":"Events-Cumulative"},2,explanation="Test of Cumulation")
    data.printByTag(newtag)

    print ("\n-------- extend")

    newtag = data.extendMe("SP","Raw-Events","input","Total","Million",{"DataTypes":"Events-Extended"},2,"Test of Extension")
    data.printByTag(newtag)
   
    print ("\n-------- scale ")
    data.printByTag(data.tag("SP","Raw-Events","input","Total","Million"))
    newtag = data.scale("SP","Raw-Events","input","Total","Million",{"DataTypes":"Scaled-Events","Resources":"Test-Scale"},2)
    data.printByTag(newtag)

    print ("\n--- results")
    for tag in data.listTags():
        data.printByTag(tag)

    # tags = []

    
    # for detector  in data.Detectors:
    #     tags.append(data.tag(detector,"Raw-Events","input","Total","Million"))
    # print (tags)
    SumFilter = {"Detectors":data.Detectors,"DataTypes":data.DataTypes,"Resources":"input","Locations":["Total"],"Units":["Million"]}

    SumFilter = {"Resources":"input","Locations":["Total"],"Units":["Million"]}
    # this has a deliberage error which cleanFilter should fix when you make the tagset
    
    test = data.makeTagSet(SumFilter)
    print (test)
    data.debug=True
    data.sumAcrossAll(filter=SumFilter,sumName="Total",explanation="Test of sumAcross Detectors")
    data.debug=DEBUG

    Drawfilter= {"Detectors":data.Detectors+["Total"],"DataTypes":["Total"],"Resources":["input"],"Locations":["Total"],"Units":["Million"]}

    table = data.csvDump(name="Events.csv",filter=Drawfilter,dropColumns=["Resources","Locations","Explanation"])
    #tex.write(data.TexBoth("Events.csv","events.","events"))

    pic = data.Draw(Dir=".",Title="test of graphics",YAxis="Events",Resource="input",Category="Detectors",filter=Drawfilter)
    #tex.write(data.TexFigure(pic,caption="test figure",label="testpic"))
    new = data.TexBoth(pic,caption="test figure",label="testpic")
    print (new)
    tex.write(new)
    tex.write("\\end{document}\n")
    data.csvDump(name="test.csv")
    