#NumberUtils.py

# Utility function: object = cummulate(object,lifetime)
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import math
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
import numpy as np
import dunestyle.matplotlib as dunestyle

def makeArray(years,map):

    #years = list(map.keys())
    array = np.zeros(len(years))
    i = 0
    for year in years:
        array[i] = map[year]
        i +=1

    return array

def SumOver1(second,thing): # loop over first index to make a sum
    new = {}
    firstindex = list(thing.keys())[0]
    print (firstindex,second,thing[firstindex].keys())
    years = thing[firstindex][second].keys()

    for y in years:
        new[y]=0.0
    for y in years:
        for index in thing.keys():
            if "Total" in index: continue
            new[y] += thing[index][second][y]
    return new

def SumOver2(first,thing): # loop over second index to make a sum
    new = {}
    firstindex = list(thing[first].keys())[0]

    years = thing[first][firstindex].keys()

    for y in years:
        new[y]=0.0
    for y in years:
        for index in thing.keys():
            if "Total" in index: continue
            new[y] += thing[index][second][y]
    return new


# Utility function: string = dump(datatype,det,object)

# make a dump of a record

def dump(det,datatype,a,Units):
    s = ""
    s  += "%5s, %10s (%s)"%(det,datatype,Units[datatype])
    for j in range(0,len(a)):
        s += ", "
        s += "%8.1f"%a[j]
    s += "\n"
    return s

def ToCSV1(name,second,years,values,Units,Formats,shorter=None): # loop over first index to make csv n
# shorter is an alternative list instead of looping over all entries
    f = open(name+".csv",'w')
    # needs first as a hint to get the right secondary index set
    #print (first, values[first].keys())
    #years = values[first][second].keys()
    if shorter == None:
        items = list(values.keys())
    else:
        items = shorter
    print ("CVS1 items",items,values.keys())
    comma = "\t,"
    s = second + comma
    for year in years:
        s += "%d \t,"%year
    s = s[0:-3]
    s += "\n"
    f.write(s)
    #print ("CSV1", list(values.keys()))
    stotal = ""
    for l in items:
        if not second in values[l].keys(): # sorry, this type doesn't have this key
            print ("CSV1: no such key", l, second)
            continue
        s = l + "(%s)"%Units[second] + comma
        v = values[l][second]
        for y in years:
            #print (Formats[second])
            s += (Formats[second]+" \t,")%(values[l][second][y])
        s = s[0:-3]
        s +="\n"
        if "Total" not in l: # put total at the end
            f.write(s)
        else:
            stotal = s
    f.write(stotal[0:-2])
    f.close


def ToCSV2(name,first,years,values,Units,Formats): # loop over second index to make csv
    f = open(name+".csv",'w')
    second = list(values[first].keys())[0]
    #years = values[first][second].keys()
    loop = list(values[first].keys())
    comma = "\t,"
    s = first + comma
    for year in years:
        s += "%d \t,"%year
    s = s[0:-3]
    s += "\n"
    f.write(s)
    stotal = ""
    for l in loop:
        s = l + " (%s)"%Units[first] + comma
        v = values[first][l]
        for y in years:
            #print (Formats[first])
            s += (Formats[first]+" \t,")%(values[first][l][y])
        s = s[0:-3]
        s +="\n"
        if "Total" not in l: # put total at the end
            f.write(s)
        else:
            stotal = s
    f.write(stotal)
    f.close


# sum backwards over lifetime of record
def cumulateMap(years,a,lifetime=100):
    lifetimebase = math.floor(lifetime)
    lifetimeextra = lifetime - lifetimebase
  #print(lifetimeextra)
    b = {}
    for i in years:
        b[i] = 0.0

    if lifetimeextra == 0:
        for i in years:
            begin = max(years[0],i-lifetimebase+1)
            for j in range(begin,i+1):
                b[i] += a[j]
 # here for partial years.
    else:
        for i in years:
            begin = max(years[0],i-lifetimebase+1)
            for j in range(begin,i+1):
                b[i] += a[j]
            if begin > years[0]:
            #print ("fix for partial",i,a[i],b[i],a[begin-1],b[i]+a[begin-1]*lifetimeextra)
                b[i]+= a[begin-1]*lifetimeextra
  #print ("cumulateMap",a,b)
  #print (b)
    return b

# sum backwards over lifetime of record
def extendMap(years,a,lifetime=0):
    lifetimebase = math.floor(lifetime)
    lifetimeextra = lifetime - lifetimebase
  #print(lifetimeextra)
    b = {}
    for i in years:
        b[i] = a[i] 
    for i in years:
        # only extend if needed
        if a[i] != 0:
            continue
        for j in range(1,lifetimebase+1):
            if i-j < years[0]:
                continue
            if a[i-j] != 0:
                #print ("extend",i,j,a[i],a[i-j])
                b[i]= a[i-j] 
                break
        
    
   
    return b

# Utility function: DrawDet(Value,Years,Data,Types,Units,detcolors,detlines)

# for detector values
def DrawDet(Name,Value,InYears,Data,Types,Units,detcolors,detlines,points=None):
    #print (InYears)
    Years = np.array(InYears)
    #print (Years)
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
    toplot = Data[Value]
    for type in Types:
        if type not in toplot.keys():
            continue
        if type not in detcolors:
            print (type, "not in ",detcolors)
        else:
            ypoints = makeArray(InYears,toplot[type])
        #print ("y points",Value,type,ypoints)
            ax.plot(Years,ypoints,color=detcolors[type],\
            linestyle=detlines[type],label="model "+type)
    if points != None:
        for y in points:
            for t in points[y]:
                #print ("t is ",t)
                if t in detcolors:
                    ax.plot(y,points[y][t],color=detcolors[t],\
                    marker="s",label="actual "+ t,markerfacecolor='none')
                else:
                    print (t ,"not in ", detcolors)
    ax.legend(frameon=False,loc='center left')
    ax.set_title(Value,fontsize=20)
    ax.set_xlabel("Year")
    if(Units != None): ax.set_ylabel(Value + ", " + Units[Value])
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


# Utility function: DrawType(Value,Years,Data,Types,Units,typecolors,typelines)

# draw by data type (transpose of the detectors)

def DrawType(Name,Value,Years,Data,Types,Units,typecolors,typelines,points=None,contributions=None):
    fig=plt.figure(figsize=(10,5))
    ax = fig.add_axes([0.2,0.2,0.7,0.7])
    maxyears = Years[-1]
    ax.set_xlim(Years[0],maxyears)
    if len(Years)<10:
        ax.xaxis.set_major_locator(MultipleLocator(1))
    else:
        ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.spines['bottom'].set_position('zero')


    for type in Types:
      #print ("test",type, Value, Data[type])
        if Data[type][Value] != None:
            ypoints = makeArray(Years,Data[type][Value])
            ax.plot(Years,ypoints,color=typecolors[type],\
            linestyle=typelines[type],label="model "+type)
    if points != None:
        for y in points:
            for t in points[y]:
                ypoints = makeArray(Data[t][Value])
                ax.plot(int(y),ypoints,color=typecolors[t],\
                marker="o",label="actual "+t,markerfacecolor='none')

    if contributions != None:
        for y in contributions:
            for t in contributions[y]:
                if t in typecolors:
                    ax.plot(y,contributions[y][t],color=typecolors[t],\
                    marker="s",label="actual  "+t)
                else:
                    print (" no such color",t, typecolors)
    ax.legend(frameon=False,loc='center left')
    ax.set_xlabel("Year")
    
    if Units != None: ax.set_ylabel(Value + ", " + Units[Value])
    ax.set_title(Value,fontsize=20)
    #print("ylim",ax.get_ylim())
    tmp = ax.get_ylim() 
    #print (tmp)
    tmp2 = (tmp[0],tmp[1]*1.2)
    print (tmp,tmp2)
    ax.set_ylim(top=tmp2[1])
    dunestyle.Preliminary()
    plt.grid()
    plt.savefig(Name + "-"+Value.replace(" ","-")+".png",transparent=False)
    #plt.savefig(Value+"_w.jpg",transparent=False)

    plt.show()

def DrawTex(shortname,figure,caption,label):
    s = "\\begin{figure}[h]\n\\centering"
    s += "\\includegraphics[height=0.4\\textwidth]{%s-%s}"%(shortname,figure)
    s += "\\caption{%s}\n"%caption
    s += "\\label{fig:%s}\n"%label
    s += "\\end{figure}\n"
    return s

def BothTex(shortname,figure,caption,label):
    print ("Call bothtex",shortname,figure)
    s = "\\begin{figure}[h]\n\\centering"
    s += "\\includegraphics[height=0.4\\textwidth]{%s-%s}"%(shortname,figure)
    s += "\n"
    s += "\\csvautotabularright{%s}"%(shortname+"-"+figure.replace(".png",".csv"))
    s += "\\caption{%s}\n"%caption
    s += "\\label{fig:%s}\n"%label
    s += "\\end{figure}\n"
    return s

def TableTex(shortname,caption,label):
    s = "\\begin{table}[h]\n\\centering{\footnotesize"
    s += "\\csvautotabularright{%s}}"%(shortname+".csv")
    s += "\\label{tab:%s}\n"%label
    s += "\\caption{%s}\n"%caption
    s += "\\end{table}\n"
    return s
