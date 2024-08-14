import os,time,sys,datetime, glob, fnmatch,string,subprocess, json

#import samweb_client
#samweb = samweb_client.SAMWebClient(experiment='dune')
from metacat.webapi import MetaCatClient
mc_client = MetaCatClient(os.getenv("METACAT_SERVER_URL"))
firstyear = 2018
lastyear = 2024
August = True  # correct for partial year. 
#out = open("YearlySummary.csv",'w')
theline = "val, type, expt, trigger, tier,"

# these are the events sizes assumed in the model
MBPerEvent = {"protodune-sp":70,"protodune-dp":110,"hd-protodune":140,"vd-protodune":110,"fardet-hd":3750,"fardet-vd":8000,"ALL":100}
MBPerSimEvent = {"protodune-sp":220,"protodune-dp":220,"hd-protodune":220,"vd-protodune":220,"fardet-vd":20,"fardet-hd":20,"ALL":100}

codes = {"protodune-sp":"SP","protodune-dp":"DP","hd-protodune":"PDHD","vd-protodune":"PDVD","fardet-vd":"FDVD","fardet-hd":"FDHD","ALL":"ALL"}
  
for type in ["mc","detector"]:
    
    for expt in ["protodune-sp","hd-protodune","protodune-dp","vd-protodune","fardet-vd","fardet-hd","ALL"]:#,"neardet","fardet","fardet-sp","iceberg","test", "311","311_dp_light","physics","ALL","hd-protodune","vd-protodune"]:
        if type == "detector": 
            streams = ["physics","cosmics","test","commissioning","calibration","ALL"]
            EventSize = MBPerEvent[expt]
        else:
            streams = ["mc"]
            EventSize = MBPerSimEvent[expt]

        for stream in streams:

            out = open("YearlySummary_%s_%s_%s_%d_%d.csv"%(type,expt,stream,firstyear,lastyear),'w')
            line = theline
            for year in range(firstyear,lastyear+1):
                line += "%d"%(year)
                if year != lastyear:
                    line = line + ","
                else:
                    line = line + "\n"
            out.write(line)
            print (line)
            for tier in ["raw","trigprim","full-reconstructed","reco-recalibrated","pandora_info","pandora-info","hit-reconstructed","simulated","detector-simulated","ALL"]:
                
                if type == "detector" and tier in ("simulated","detector-simulated"):
                    continue
                if type == "mc" and tier in ["raw","trigprim"]:
                    continue
                linefiles = "files, %s, %s, %s, %s,"%(type,codes[expt],stream,tier)
                lineevents = "M Events, %s, %s, %s, %s,"%(type,codes[expt],stream,tier)
                linesize = "size (TB), %s,  %s, %s, %s,"%(type,codes[expt],stream,tier)
                sumevents = 0
                otherevents = 0
                sumcount = 0
                othersize = 0
                #for year in range(firstyear,lastyear+1):
                #  if year != firstyear:
                #    linefiles = linefiles+ ","
                #    linesize = linesize + ","
                command = "files where "
                command += " core.file_type=" + type
                if tier != "ALL": command += " and core.data_tier="+tier
                if type == "detector" and stream != "ALL": command += " and core.data_stream=" + stream
                if expt != "ALL" : command += " and core.run_type=" + expt
                allcommand = command + " and created_timestamp>=" +"%d-01-01"%(firstyear)
                allcommand += " and created_timestamp<=" +"%d-12-31"%(lastyear)
                check = mc_client.query(query=allcommand,summary="count")
                if check["count"] == 0:
                    print ("nothing to see here",allcommand)
                    continue
                for year in range(firstyear,lastyear+1):
                    if year != firstyear:
                        linefiles = linefiles+ ","
                        linesize = linesize + ","
                        lineevents = lineevents + ","
                    #if( type != "mc"):
                    #  command += " and run_type " + expt
                    thecommand = command + " and created_timestamp>=" +"%d-01-01"%(year)
                    thecommand += " and created_timestamp<=" +"%d-12-31"%(year)
                    #command = command.replace("ALL","%")
                    print (thecommand)
                    result = mc_client.query(query=thecommand,summary="count")
                    print(result)
                    
                    file_count = result["count"]
                    if file_count == None:
                        file_count = 0
                        events = 0
                
                    #events = 0
                    #print (" events is ",events)
                    #sumevents += events
                    
                    ssize = result["total_size"]
                    if ssize == None:
                        ssize = 0
                    ssize = ssize/1000/1000/1000/1000.
                    if file_count > 0:
                        fsize = ssize/file_count
                        events = ssize/EventSize
                    else:
                        fsize = 0.0
                        events = 0
                    #print ("events",events)
                    if year == "2024" and August:
                        ssize *=1.5
                        events *=1.5
                        file_count *=1.5
                    sumcount += file_count
                    lineevents = lineevents + "{:.3f}".format(events)
                    linefiles = linefiles + "%d"%(file_count)
                    linesize = linesize + "{:.1f}".format(ssize)
                    
        #          else:
        #            linefiles = linefiles+ "\n"
        #            linesize = linesize + "\n"
        #          print (year, expt,tier,stream,file_count,events,"%s TB"%ssize,fsize," MB")
                    linesize = linesize.replace("%","ALL")
                    lineevents = lineevents.replace("%","ALL")
                    linefiles = linefiles.replace("%","ALL")
                linefiles = linefiles+ "\n"
                lineevents = lineevents + "\n"
                linesize = linesize + "\n"
                #if sumevents == 0:
                #  continue
                out.write(linefiles)
                out.write(linesize)
                out.write(lineevents)
                print (linefiles.replace(",","\t"))
                print (linesize.replace(",","\t"))
                print (lineevents.replace(",","\t"))
            out.close()


        
