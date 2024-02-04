""" RSEparse.py

H. Schellman 1-31-2024

Reads in a json file with list of rucio RSE data and generates by rse and by country summaries

changes to TB units and makes csv files summarizing info for valid sites. 


physical size data from 

https://dune.monitoring.edi.scotgrid.ac.uk/app/dashboards#/view/7eb1cea0-ca5e-11ea-b9a5-15b75a959b33?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-1d,to:now))

RSE data from 

https://github.com/DUNE/data-mgmt-ops/blob/master/data-collections-manager/dcm_rucio_rses.py


"""

import os,sys,commentjson, csv

DEBUG=False

""" read in the data from the RSE_USAGE page """
p = open("external/DUNE_RSE_USAGE_2024-02-01.csv",'r')
physicaldata = {}
with p as csvfile:
    reader = csv.DictReader(csvfile)
    for line in reader:
        #print(line)
        line["RSE"]=line['\ufeffRSE']
        for key in line.keys():
            if "TB" in key:
                line[key]=float(line[key])
        line.pop('\ufeffRSE')
        print(line)
        physicaldata[line["RSE"]] = line

""" read in the data from the data collection RSE summaries """        
f = open("external/RSEs_dune.json")
rsedata = commentjson.load(f)


o = open("external/RSEdata.csv",'w')
oo = open("external/StorageByCountry.csv",'w')

""" these are patches to disable or set the size """
patches = {"FNAL_DCACHE":8780000,
           "CERN_PDUNE_CASTOR":-1,
           "FNAL_DCACHE_TEST":-1,
           "LANCASTER":-1,
            }
" here dcache is from Steve Timm, rest are set to -1 as the are not real anymore "



# use this to sort by country

countries = {
"CERN_PDUNE_CASTOR":"CERN",
"CERN_PDUNE_EOS":"CERN",
"DUNE_CERN_EOS":"CERN",
"DUNE_ES_PIC":"ES",
"DUNE_FR_CCIN2P3":"FR",
"DUNE_FR_CCIN2P3_DISK":"FR",
"DUNE_FR_CCIN2P3_TAPE":"FR",
"DUNE_FR_CCIN2P3_XROOTD":"FR",
"DUNE_IN_TIFR":"IN",
"DUNE_IT_INFN_CNAF":"IT",
"DUNE_UK_LANCASTER_CEPH":"UK",
"DUNE_US_BNL_SDCC":"US",
"DUNE_US_FNAL_DISK_STAGE":"FNAL",
"EDINBURGH":"UK",
"FNAL_DCACHE":"FNAL",
"FNAL_DCACHE_PERSISTENT":"FNAL",
"FNAL_DCACHE_STAGING":"FNAL",
"FNAL_DCACHE_TEST":"FNAL",
"FNAL_SCRATCH":"FNAL",
"FNAL_SCRATCH_DCACHE":"FNAL",
"IMPERIAL":"UK",
"LANCASTER":"UK",
"LIVERPOOL":"UK",
"MANCHESTER":"UK",
"NIKHEF":"NL",
"PRAGUE":"CZ",
"QMUL":"UK",
"RAL_ANTARES":"UK",
"RAL_ECHO":"UK",
"RAL-PP":"UK",
"SCRATCH_DCACHE":"US",
"SURFSARA":"NL",
"T3_US_NERSC":"US",
}

short = {}

for rse in rsedata:
    if DEBUG: print (rse)
    if rse["decommissioned"]: 
        continue
    
    fullname = rse["name"]
    if fullname in patches:
        print ("patch this RSE as it has no limit",fullname,patches[fullname])

        rse["account_lim"] = patches[fullname]
        if rse["account_lim"] < 0:
            continue

        #if rse["account_lim"] < rse["rse_usage"]:
        #    print ("can't use more than you have", fullname)
        #    rse["rse_usage"] = rse["account_lim"]
    if fullname not in patches and rse["type"] == "TAPE":
        print ("skip this RSE as it is tape",fullname)
        continue
    
    if rse["account_lim"] < 0:
        continue
    disksize = rse["account_lim"]/1000
    usage = rse["rse_usage"]/1000
    if fullname in physicaldata:
        disksize=physicaldata[fullname]['Allocation (TB)']
        usage = physicaldata[fullname]['Used (TB)']
        print ("found the disk size")
    else:
        print("physicaldata",fullname,list(physicaldata.keys()))
    info = {"country":countries[fullname],"name":fullname,"Allocation":disksize,"Used":usage,
        "account_lim":rse["account_lim"]/1000,"rse_usage":rse["rse_usage"]/1000,"frac":(usage/float(disksize)*100)}
    print (info)
    line = "%5s,%30s,%10.0f,%10.0f, %10.0f,%10.0f,%10.0f\n"%(info["country"],info["name"], info["Allocation"],info["Used"],info["account_lim"],info["rse_usage"],info["frac"])
    print (line)
    short[info["country"]+"_"+fullname] = info

rses = list(short.keys())
rses.sort()



line = "%5s,%30s,%10s,%10s,%10s,%10s,%10s\n"%("Country", "RSE","Allocation (TB)","Used (TB)","account_lim (TB)","rse_usage (TB)","percent used")
print (line)
o.write(line.replace('_',' '))

for name in rses:
    info = short[name]
    line = "%5s,%30s,%10.0f,%10.0f,%10.0f,%10.0f,%10.0f\n"%(info["country"],info["name"], info["Allocation"],info["Used"], info["account_lim"],info["rse_usage"],info["frac"])
    print (line)
    o.write(line.replace('_',' '))

o.close()

bycountry = {}

for key in rses:
    info = short[key]
    country = info["country"]
    if country in bycountry:
        
        bycountry[country]["account_lim"]+=info["account_lim"]
        bycountry[country]["Allocation"]+=info["Allocation"]
        bycountry[country]["Used"]+=info["Used"]
        bycountry[country]["rse_usage"]+=info["rse_usage"]
        bycountry[country]["frac"]=bycountry[country]["Used"]/bycountry[country]["Allocation"]*100
    else:
        bycountry[country] = {}
        bycountry[country]["country"]=key
        bycountry[country]["Allocation"]=info["Allocation"]
        bycountry[country]["Used"]=info["Used"]
        bycountry[country]["account_lim"]=info["account_lim"]
        bycountry[country]["rse_usage"]=info["rse_usage"]
        bycountry[country]["frac"]=bycountry[country]["Used"]/bycountry[country]["Allocation"]*100

 
line = "%5s,%10s,%10s,%10s,%10s,%s\n"%("Country", "Allocated (TB)", "used (TB)", "account_lim (TB)","rse_usage (TB)","percent used")
print (line)
oo.write(line.replace('_',' '))

nations = bycountry.keys()
totals = {}
totals["account_lim"]=0.0
totals["Allocation"]=0.0
totals["Used"]=0.0
totals["rse_usage"]=0.0
print (nations)
for key in nations:
    info = bycountry[key]
    print (key,info)
    print (key,info["account_lim"],info["rse_usage"])
    totals["Allocation"] += info["Allocation"]
    totals["Used"] += info["Used"]
    totals["account_lim"]+=info["account_lim"]
    totals["rse_usage"]+=info["rse_usage"]
    totals["frac"]=totals["Used"]/totals["Allocation"]*100
    line = "%5s,%10.0f,%10.0f,%10.0f,%10.0f,%10.0f\n"%(key, info["Allocation"],info["Used"],info["account_lim"],info["rse_usage"],info["frac"])
    print (line)
    oo.write(line.replace('_',' '))

line = "%5s,%10.0f,%10.0f,%10.0f,%10.0f,%10.0f\n"%("Total", totals["Allocation"],totals["Used"], totals["account_lim"],totals["rse_usage"],totals["frac"])
print (line)
oo.write(line.replace('_',' '))
oo.close()
        