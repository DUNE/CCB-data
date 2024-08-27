import os,time,sys,datetime, glob, fnmatch,string,subprocess, json

#import samweb_client
#samweb = samweb_client.SAMWebClient(experiment='dune')
import datetime
from metacat.webapi import MetaCatClient

DEBUG=True
mc_client = MetaCatClient(os.getenv("METACAT_SERVER_URL"))

if len(sys.argv) > 1:
    end = sys.argv[1]
else:
    end = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
year = int(end[0:4])
month = int(end[5:7])
day = int(end[8:10])

lastweek = datetime.datetime(year,month,day)
delta = datetime.timedelta(weeks=1)
print (lastweek,delta)

nweeks = 20
firstweek = (lastweek-nweeks*delta)

print (end,year,month,day)






August = True  # correct for partial year. 
#out = open("YearlySummary.csv",'w')
theline = "val, type, expt, trigger, tier,"

# these are the events sizes assumed in the model
MBPerEvent = {"protodune-sp":70,"protodune-dp":110,"hd-protodune":140,"vd-protodune":110,"fardet-hd":3750,"fardet-vd":8000,"ALL":100}
MBPerSimEvent = {"protodune-sp":220,"protodune-dp":220,"hd-protodune":220,"vd-protodune":220,"fardet-vd":20,"fardet-hd":20,"ALL":100}

codes = {"protodune-sp":"SP","protodune-dp":"DP","hd-protodune":"PDHD","vd-protodune":"PDVD","fardet-vd":"FDVD","fardet-hd":"FDHD","ALL":"ALL"}
  
for type in ["mc","detector"]:
    
    for expt in ["hd-protodune","vd-protodune","fardet-vd","fardet-hd","ALL"]:#,"neardet","fardet","fardet-sp","iceberg","test", "311","311_dp_light","physics","ALL","hd-protodune","vd-protodune"]:
        if DEBUG and expt != "hd-protodune":continue
        if type == "detector": 
            streams = ["physics","cosmics","test","commissioning","calibration","ALL"]
            EventSize = MBPerEvent[expt]
        else:
            streams = ["mc"]
            EventSize = MBPerSimEvent[expt]

        for stream in streams:

            out = open("WeeklySummary_%s_%s_%s_%s_%s.csv"%(type,expt,stream,str(firstweek)[0:10],str(lastweek)[0:10]),'w')
            line = theline
            for nweek in range(0,nweeks):
                week = firstweek + nweek*delta
                line += "%10s"%(str(week)[0:10])
                if nweek != nweeks-1:
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
                if tier != "ALL":
                    command += " and core.data_tier="+tier
                if type == "detector" and stream != "ALL":
                    command += " and core.data_stream=" + stream
                if expt != "ALL" :
                      command += " and core.run_type=" + expt
                allcommand = command + " and created_timestamp>=" +"%10s"%(str(firstweek)[0:10])
                allcommand += " and created_timestamp<" +"%10s"%(str(lastweek)[0:10])

                print ("precheck",allcommand)
                check = mc_client.query(query=allcommand,summary="count")
                if check["count"] == 0:
                    print ("nothing to see here",allcommand)
                    continue
                for nweek in range(0,nweeks):
                    week = firstweek + nweek*delta
                    if week != firstweek:
                        linefiles = linefiles+ ","
                        linesize = linesize + ","
                        lineevents = lineevents + ","
                    
                    thecommand = command + " and created_timestamp>=" +"%10s"%(str(week)[0:10])
                    thecommand += " and created_timestamp<" +"%10s"%(str(week+delta)[0:10])
                    
                    print (thecommand)
                    result = mc_client.query(query=thecommand,summary="count")
                    print(result)
                    
                    file_count = result["count"]
                    if file_count == None:
                        file_count = 0
                        events = 0
                
            
                    
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
                    
                    sumcount += file_count
                    lineevents = lineevents + "{:.3f}".format(events)
                    linefiles = linefiles + "%d"%(file_count)
                    linesize = linesize + "{:.1f}".format(ssize)
                    
       
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


        
