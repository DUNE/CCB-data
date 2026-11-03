r'''Translate a json configuration file into LaTeX macros and csv tables.

Everything that identifies a run lives in the configuration file itself, in its
"Run" block:

    "Run":{
        "ConfigFile":"NearTerm_2025-12-10-2040.json", // which config this is
        "OutputDir":"",                               // optional, derived if empty
        "Glossary":true,                              // write a standalone glossary
        "Notebook":"2025-12-10.ipynb"                 // driver notebook, for reference
    },

so this script no longer has to be edited before running it:

    python json2tex.py                       # newest config in this directory
    python json2tex.py NearTerm_2025-12-10-2040.json
    python json2tex.py --no-glossary         # macros only, for a \input report

The notebook uses the same helpers (loadconfig / initialize / runit) so the config
file name, the output directory and the macros are computed in exactly one place.
'''

import os, sys
import commentjson
import csv

# the configuration file format this code understands
MINVERSION = 20

# json files written out by the model itself - never input configurations
GENERATEDSUFFIXES = ("_safe.json", "_holder.json", "_clean.json")

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
            value = value.replace("_","\\_")
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
 

# ---------------------------------------------------------------------------
# run identification: everything below is derived from the config file itself
# ---------------------------------------------------------------------------

def loadconfig(configname):
    '''read a (comment carrying) json configuration file and check its version'''
    with open(configname,'r') as configfile:
        config = commentjson.load(configfile)
    if "Version" not in config or config["Version"] < MINVERSION:
        raise ValueError("%s: this code expects Version >= %d"%(configname,MINVERSION))
    return config

def readconfig(configname):
    '''The config as a dict if the file is a model configuration, else None.

    Files the model writes out (*_safe.json, *_holder.json) and anything too old or
    malformed to be a configuration are skipped.
    '''
    if not configname.endswith(".json"): return None
    if any(configname.endswith(s) for s in GENERATEDSUFFIXES): return None
    try:
        config = loadconfig(configname)
    except Exception:
        return None
    if "MaxYear" not in config or "Detectors" not in config: return None
    return config

def find_config(configname=None,dir="."):
    '''Which configuration file is this run using?

    1. an explicit name wins,
    2. otherwise the newest configuration in `dir` that declares a Run block,
       falling back to the most recently edited one,
    3. and if that file's Run.ConfigFile points somewhere else, follow the pointer.
    '''
    if configname:
        if not configname.endswith(".json"): configname += ".json"
        if not os.path.exists(configname) and os.path.exists(os.path.join(dir,configname)):
            configname = os.path.join(dir,configname)
        if not os.path.exists(configname):
            raise FileNotFoundError("no config file %s"%configname)
        print ("config file",configname,"requested")
        return os.path.normpath(configname)

    candidates = []
    for f in sorted(os.listdir(dir)):
        path = os.path.join(dir,f)
        config = readconfig(path)
        if config is None: continue
        # a config that declares a Run block is one the model is meant to be driven by
        declared = "Run" in config
        candidates.append((declared,config.get("Version",0),os.path.getmtime(path),path,config))
    if not candidates:
        raise FileNotFoundError("no json configuration file found in %s"%os.path.abspath(dir))
    candidates.sort(reverse=True)
    configname = os.path.normpath(candidates[0][3])
    print ("config files found:", ", ".join(os.path.normpath(p) for *_,p,_ in candidates))

    # a config can point at the file that should actually be used
    pointer = candidates[0][4].get("Run",{}).get("ConfigFile")
    if pointer:
        pointer = os.path.normpath(os.path.join(os.path.dirname(configname),pointer))
        if pointer != configname and os.path.exists(pointer):
            print ("Run.ConfigFile points at",pointer)
            return pointer
    return configname

def output_dirname(config,configname,dirname=None):
    '''Directory the run writes into: the config name with the nominal end year
    replaced by MaxYear plus the memory weighting tag.  A non-empty Run.OutputDir
    (or the dirname argument) overrides the derived name.'''
    if not dirname:
        dirname = config.get("Run",{}).get("OutputDir")
    if dirname: return dirname

    shortname = os.path.basename(configname)
    for suffix in (".json",".JSON"):
        if shortname.endswith(suffix): shortname = shortname[:-len(suffix)]
    shortname = shortname.replace("2040","%d"%config["MaxYear"])
    shortname += "" if config.get("MWCWeight",0) else "_noMWC"
    return shortname

def initialize(configname=None,dirname=None,glossary=None,dir="."):
    '''Load the configuration and work out all of the names for the run.

    Returns (config, run) with run holding the derived names (configname, dirname,
    shortname, texfilename, tablefilename, glossary).  The output directory is
    created if needed.  The notebook calls this so that one json file defines the
    whole run.
    '''
    configname = find_config(configname,dir=dir)
    config = loadconfig(configname)
    config["filename"] = configname

    dirname = output_dirname(config,configname,dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if glossary is None:
        glossary = bool(config.get("Run",{}).get("Glossary",False))

    run = {"configname":configname,
           "dirname":dirname,
           "shortname":os.path.join(dirname,dirname),
           "texfilename":os.path.join(dirname,dirname+".tex"),
           "tablefilename":os.path.join(dirname,"tables.tex"),
           "glossary":glossary}
    print ("running",configname,"->",dirname,("(with glossary)" if glossary else ""))
    return config,run

def runit(configname=None,dirname=None,glossary=None,config=None):
    '''Write the LaTeX macros and csv summaries for one configuration.

    `configname`, `dirname` and `glossary` may be omitted - they come from the
    configuration file (see find_config / output_dirname).  Pass `config` if it has
    already been loaded, as it has in the notebook.
    '''
    if config is None:
        configname = find_config(configname)
        config = loadconfig(configname)
    elif not configname:
        configname = config.get("filename")
    if not configname:
        raise ValueError("no config file name: pass configname, or set config[\"filename\"]")
    if not dirname:
        dirname = output_dirname(config,configname)
    if glossary is None:
        glossary = bool(config.get("Run",{}).get("Glossary",False))

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # names are based on the file itself, not on the path it may be reached by
    base = os.path.basename(configname)
    makeDetectorTable(dirname,base.replace(".json","_detectors.csv"),config)
    makeSplitsTable(dirname,base.replace(".json","_splits.csv"),config)

    print (config["DiskCopies"])
    makeTable(dirname,base.replace(".json","_diskcopies.csv"),["DiskCopies","DiskLifetimes","TapeCopies","TapeLifetimes"],config)

    # macros.tex is what a report \input-s, so it is always written.
    result = json2tex(config)
    macros = os.path.join(dirname,base.replace(".json","macros.tex"))
    with open(macros,'w') as texfile:
        texfile.write(result)

    # the glossary is a standalone document listing every macro, for checking them
    if not glossary: return macros
    glossaryname = os.path.join(dirname,base.replace(".json","glossary.tex"))
    with open(glossaryname,'w') as texfile:
        texfile.write("\\input Header.tex\n")
        texfile.write("\\baselineskip 18 pt\n")
        texfile.write(json2tex(config,test=True))
        texfile.write("\\end{document}")
    return glossaryname

def usage(errcode=0):
    print ("usage: python json2tex.py [configfile.json] [--glossary] [--no-glossary] [--outdir DIR]")
    print ("       without a config file: use the newest configuration in this directory")
    sys.exit(errcode)

if __name__ == '__main__':
    args = sys.argv[1:]
    glossary = None
    dirname = None
    configname = None
    while args:
        arg = args.pop(0)
        if arg in ("-h","--help"): usage(0)
        elif arg in ("--glossary","--test"): glossary = True
        elif arg in ("--no-glossary","--no-test"): glossary = False
        elif arg in ("--outdir","-o"):
            if not args: usage(1)
            dirname = args.pop(0)
        elif arg.startswith("-"): usage(1)
        else: configname = arg
    try:
        written = runit(configname=configname,dirname=dirname,glossary=glossary)
    except (FileNotFoundError,ValueError) as err:
        print (err)
        sys.exit(1)
    print ("wrote",written)

