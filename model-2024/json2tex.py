import os, sys
import commentjson
import csv

def cleanname(line):
    
        line =  line.replace("#","\\#").replace("%","\\%").replace(" ","").replace("-","").replace("Comment","%%").replace("+","")
        line = line.replace("0000","")
        return line
    

def makeline(localname,value,header="",test=False):
    if "Comment" in localname:
        return ""
    name = cleanname(localname+header)
    if "23" in name:
        name = name.replace("23","TwentyThree")
    if "06" in name:
        name = name.replace("06","ZeroSix")
    if "2020" in name:
        name = name.replace("2020","TwentyTwenty")
    
    line = ""
    if "Actual" in name:
        return ""
    if "Comment" in name or "Changes" in name or "comment" in name:
        return "%%Comment %s %s %s\n"%(header,name,value)
    if "Format" in name:
        return "%%Format %s %s %s\n"%(header,name,value)
    if isinstance(value,str): 
        if "_" in value:
            value = value.replace("_","\_")
        template = "\\newcommand{\\config%s}{%s}\n"     
        line =  template%(name,value)
        if(test): line += "config%s = \\config%s \\\\  %% testing\n"%(name,name)
    if isinstance(value,dict):
        #print ("dict")
        for x,y in value.items():
            #print ("element", x,y, name, header)
            line += makeline(x,y,name)
    if isinstance(value,list):
        y = ','.join(map(str, value)) 
        line = "\\newcommand{\\config%s%s}{%s}\n"%(header,name,value)
        if(test): line += "config%s = \\config%s \\\\ %% testing\n"%(name,name)
    if isinstance(value,int):
        line = "\\newcommand{\\config%s}{%d}\n"%(name,(value)) 
        if(test): line += "config%s = \\config%s \\\\  %% testing\n"%(name,name)
    if isinstance(value,float):
        line = "\\newcommand{\\config%s}{%f}\n"%(name,(value)) 
        if(test): line += "config%s = \\config%s \\\\  %% testing\n"%(name,name)

    
    return line

def json2tex(config,test=False):
    output = ""
    for p,v in config.items():
        #print ("input", p,v)
        line = makeline(p,v,"",test)
        output += line
    return output

def makeDetectorTable(dir,name,config):
    detectors = config["Detectors"]
    table = {}    
    pars = config["SP"].keys()
    units = {'Raw-Data-Store':"MB",  'Reco-Data-Store':"MB", 'Reco-Sim-Store':"MB", 'Reco-Data-CPU':"hr", 'Reco-Sim-CPU':"hr", 'Reco-Data-GPU':"hr", 'Reco-Sim-GPU':"hr", 'Analysis-CPU':"fraction"}
    pars = list(units.keys())
    for p in pars:
        if p == "Comment": continue
        table[p] = {"parameter":p,"units":units[p]}
        for d in detectors:
            
            table[p][d] = config[d][p]
            #print (p,table[p])
    fieldnames = ["parameter","units"]+detectors
    
    s = commentjson.dumps(table,indent=4)
    #print (s)
    with open(os.path.join(dir,name), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for line in table.keys():
            #print ("line",table[line])
            writer.writerow(table[line])

def makeTable(dir,name,inputnames,config):
    table ={}
    print (config[inputnames[0]])
    fields = config[inputnames[0]].keys()
    print ("fields",fields)
    for f in fields:  
        table[f] = {"Parameters":f}
        for x in inputnames:
            table[f][x] = config[x][f]
    print (table)
    fieldnames = ["Parameters"]+inputnames
    print (fieldnames)
    with open(os.path.join(dir,name), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for line,values in table.items():
                print ("line",line,values)
                writer.writerow(values)

def makeSplitsTable(dir,genname,config):
    periods = config["Splits"].keys()
    resources = config["Splits"]["PD"].keys()

    for resource in resources:
        table = {}
        for period in periods:      
            print ("line",config["Splits"][period][resource])
            tiers = config["Splits"][period][resource].keys()
            for tier in tiers:
                tag = period+tier
                table[tag]={"Detector Class":period}|{"Data Type":tier}|config["Splits"][period][resource][tier]
                fieldnames = table[tag].keys()
                #print (table[tag])
        name = genname.replace(".csv","_%s.csv"%(resource))
        
        print ("fieldnames",fieldnames)
        print (table)
        with open(os.path.join(dir,name), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for line,values in table.items():
                print ("line",line,values)
                writer.writerow(values)
 
if __name__ == '__main__':
    TEST = False
    dirname = "NearTerm_2024-08-27-2030_noMWC"
    if TEST: dirname = "."
    configname = "NearTerm_2024-08-27-2040.json"
    configfile = open(configname,'r')
    config = commentjson.load(configfile)
    
    makeDetectorTable(dirname,configname.replace(".json","_detectors.csv"),config)
    makeSplitsTable(dirname,configname.replace(".json","_splits.csv"),config)
    
    print (config["DiskCopies"])
    makeTable(dirname,configname.replace(".json","_diskcopies.csv"),["DiskCopies","DiskLifetimes","TapeCopies","TapeLifetimes"],config)

    result = json2tex(config,test=TEST)
    if TEST:
        texname = configname.replace(".json","glossary.tex")
    else:
        texname = configname.replace(".json","macros.tex")
    texfile = open(os.path.join(dirname,texname),'w')
    if TEST: 
        texfile.write("\\input Header.tex\n")   
        texfile.write("\\baselineskip 18 pt\n")
    texfile.write(result)
    if TEST: 
        texfile.write("\\end{document}")
    texfile.close()
    configfile.close()
