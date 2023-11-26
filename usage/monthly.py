#!/usr/bin/env python
# coding: utf-8

# In[1]:


# link = "https://fifemon.fnal.gov/kibana/app/kibana#/visualize/edit/33d02c40-8b41-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'))&_a=(filters:!(),linked:!f,query:(language:lucene,query:'Jobsub_Group:dune'),uiState:(vis:(params:(sort:(columnIndex:!n,direction:!n)))),vis:(aggs:!((enabled:!t,id:'1',params:(field:SlotHours),schema:metric,type:sum),(enabled:!t,id:'3',params:(field:MachineAttrGLIDEIN_DUNESite0,missingBucket:!f,missingBucketLabel:Missing,order:desc,orderBy:'1',otherBucket:!f,otherBucketLabel:Other,size:50),schema:bucket,type:terms),(enabled:!t,id:'5',params:(customInterval:'2h',drop_partials:!f,extended_bounds:(),field:'@timestamp',interval:M,min_doc_count:1,timeRange:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'),useNormalizedEsInterval:!t),schema:bucket,type:date_histogram),(enabled:!t,id:'4',params:(filters:!((input:(query:'NOT(Owner:dunepro)%20AND%20NOT(Jobsub_SubGroup:mars)'),label:Analysis),(input:(query:'Owner:dunepro'),label:Production),(input:(query:'Jobsub_SubGroup:mars'),label:MARS),(input:(query:'*'),label:Total))),schema:bucket,type:filters)),params:(perPage:24,showMetricsAtAllLevels:!f,showPartialRows:!f,showTotal:!f,sort:(columnIndex:!n,direction:!n),totalFunc:sum),title:'DUNE%20monthly%20slot%20hours%20by%20site%20and%20role',type:table))"


# In[2]:


# go to that link, go to inspect and save as formatted csv


# In[3]:


# define  bydate(array=None,types=None,locations=None,dates=None,units=None,tag=None):


# In[4]:


def bydate(array=None,types=None,locations=None,dates=None,units=None,tag=None):
   # metdefhod that makes a table from an array indexed by type, location and date by location and date.
   # tag is a tag that tells what the array was
   # adds a sum across both row and column
   # output is a csv file of the table
   lowdate = dates[0]
   highdate = dates[-1]
   print (lowdate,highdate)
   header = "   time in %s by %s     "%(units,tag)
   header2 = header

   for date in dates:
       header += "%10s"%date
       header2 += ",%s"%date
   header += "     Total"
   header2 += ",Total\n"

   out = {}
   for type in types:
       outname = "output/%s_%s_%s_%s_%s.csv"%(type,tag,units,lowdate,highdate)
       out[type] = open(outname,'w')
       out[type].write(header2)

   print (locations) 

   for type in types:  
       totalbydate = {}
       for date in dates:
           totalbydate[date] = 0.0
       totaltotal = 0.0
       for site in locations:
           result = "%30s"%site
           outstring = "%s"%site
           total = 0.0

           for date in dates:
               result += " %10.3f"%(array[type][site][date])
               outstring += ", %10.3f"%(array[type][site][date])
               total += (array[type][site][date])
               totalbydate[date]+= (array[type][site][date])
           totaltotal+=total           
           outstring += ",%10.3f\n"%total
           #print (outstring)
           out[type].write(outstring)
       outstring = "%s"%"Total"
       for date in dates:
           outstring += ", %10.3f"%(totalbydate[date])
       outstring += ",%10.3f\n"%totaltotal 
       out[type].write(outstring)
       out[type].close()


# In[5]:


import csv

# ken
#  "https://fifemon.fnal.gov/kibana/app/kibana#/visualize/edit/33d02c40-8b41-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'))&_a=(filters:!(),linked:!f,query:(language:lucene,query:'Jobsub_Group:dune'),uiState:(vis:(params:(sort:(columnIndex:!n,direction:!n)))),vis:(aggs:!((enabled:!t,id:'1',params:(field:SlotHours),schema:metric,type:sum),(enabled:!t,id:'3',params:(field:MachineAttrGLIDEIN_DUNESite0,missingBucket:!f,missingBucketLabel:Missing,order:desc,orderBy:'1',otherBucket:!f,otherBucketLabel:Other,size:50),schema:bucket,type:terms),(enabled:!t,id:'5',params:(customInterval:'2h',drop_partials:!f,extended_bounds:(),field:'@timestamp',interval:M,min_doc_count:1,timeRange:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'),useNormalizedEsInterval:!t),schema:bucket,type:date_histogram),(enabled:!t,id:'4',params:(filters:!((input:(query:'NOT(Owner:dunepro)%20AND%20NOT(Jobsub_SubGroup:mars)'),label:Analysis),(input:(query:'Owner:dunepro'),label:Production),(input:(query:'Jobsub_SubGroup:mars'),label:MARS),(input:(query:'*'),label:Total))),schema:bucket,type:filters)),params:(perPage:24,showMetricsAtAllLevels:!f,showPartialRows:!f,showTotal:!f,sort:(columnIndex:!n,direction:!n),totalFunc:sum),title:'DUNE%20monthly%20slot%20hours%20by%20site%20and%20role',type:table))"

# wenlong https://fifemon.fnal.gov/kibana/app/kibana#/dashboard/83d7b0c0-8b1c-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-1y,mode:quick,to:now))&_a=(description:%27%27,filters:!(),fullScreenMode:!f,options:(darkTheme:!t,hidePanelTitles:!f,useMargins:!t),panels:!((embeddableConfig:(),gridData:(h:14,i:%271%27,w:48,x:0,y:0),id:%2757162130-8b1b-11ee-804b-5759672b811c%27,panelIndex:%271%27,type:visualization,version:%276.8.23%27),(embeddableConfig:(),gridData:(h:16,i:%272%27,w:48,x:0,y:14),id:%275ee81fc0-8b1c-11ee-804b-5759672b811c%27,panelIndex:%272%27,type:visualization,version:%276.8.23%27)),query:(language:lucene,query:%27%27),timeRestore:!t,title:fifebatch-jobs-dune,viewMode:view)

# choose your units

name = 'DUNE monthly slot hours by site and role-2.csv'
inunits="Hr"
HoursPerYear=(24*365)
HoursPerMonth=HoursPerYear/12.
CPUHrPerkHS23=1000/11.
Units = {"MHr":1000000.,"CoreYears":HoursPerYear,"kHS23-Hrs":CPUHrPerkHS23}
outunits = "kHS23-Hrs"

# make choices here
lowdate = "2022-01"
highdate = "2022-12" 
units=Units[outunits]


# In[6]:


Data = {}
ByCountry = {}
sites = []
types = []
dates = []
countries = []


# In[7]:


# read in csv and parse into array

with open(name,'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    
    for row in csv_reader:
        #print (row)
        line_count += 1
        if line_count == 1:
            labels = row
            continue
        site = row[0] 
        country = site.split("_")[0]
        date = row[1][0:7] # truncate the day
        type = row[2]
        value = float(row[3].replace(",",""))/units
        

        
        if type not in Data.keys():
            #print ("add type",type)
            Data[type]={}
            types.append(type)
            
        if site not in Data[type].keys():
            #print ("add site",site)
            Data[type][site]={}
        
        
        if type not in types: types.append(type)
        if site not in sites: sites.append(site)
        if date not in dates: dates.append(date)
        if country not in countries: countries.append(country)
        
        Data[type][site][date]=value
         
        
        # print (Data)
print (sites)
print (countries)  
print (dates)

sites.sort()
countries.sort()
 


# In[8]:


# fill in the blanks 

for type in types:
    for site in sites:
        if site not in Data[type].keys():
            Data[type][site]={}
        for date in dates:
            if date not in Data[type][site].keys():
                Data[type][site][date] = 0.0
        #print (type,site, Data[type][site])
        
# make a NoMARS class

types.append("NoMARS")
Data["NoMARS"] = {}
for site in sites:
    Data["NoMARS"][site] = {}
    for date in dates:
        Data["NoMARS"][site][date] = Data["Total"][site][date]-Data["MARS"][site][date]
        


# In[9]:




# trim the date slist
newdates = []
for date in dates:
    if date < lowdate or date > highdate:
                continue
    newdates.append(date)
dates = newdates
print (dates)


# In[10]:


print ("                                     Usage in %s between %s and %s"%(outunits,lowdate,highdate))
print ("%30s %10s %10s %10s %10s %10s"%("Site","Production","Analysis","NoMARS","MARS","Total"))


totalacrosssite={}
for type in types:
    totalacrosssite[type] = 0.0
for site in sites:
    use = {}
    for type in types:
        use[type] = 0.0        
        for date in dates:
            use[type] += Data[type][site][date]
        if outunits == "Cores": 
            print ("fix core ")
            use[type]/=12. 
        totalacrosssite[type] += use[type]
    
     
    print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%(site,use["Production"],use["Analysis"],use["NoMARS"],use["MARS"],use["Total"])) 

#totalacrosssite["NoMARS"] = totalacrosssite["Total"] - totalacrosssite["MARS"]
print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%("Total",totalacrosssite["Production"],totalacrosssite["Analysis"],totalacrosssite["NoMARS"],totalacrosssite["MARS"],totalacrosssite["Total"]))      


# In[ ]:





# In[11]:


# do by country
for type in types:
    ByCountry[type]={}
    for country in countries:
        ByCountry[type][country]={}
        for date in dates:
            ByCountry[type][country][date] = 0.0
    for site in sites:
        country = site.split("_")[0]
        for date in dates:
            ByCountry[type][country][date]+=Data[type][site][date]


# In[12]:


print ("                              Usage in %s between %s and %s"%(outunits,lowdate,highdate))
print ("%30s %10s %10s %10s %10s %10s"%("Country","Production","Analysis","NoMARS","MARS","Total"))


totalacrosssites={}
for type in types:
    totalacrosssite[type] = 0.0
for site in countries:
    use = {}
    for type in types:
        use[type] = 0.0        
        for date in dates:
            use[type] += ByCountry[type][site][date]
        totalacrosssite[type] += use[type]
    #use["NoMARS"] = use["Total"] - use["MARS"]  
    print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%(site,use["Production"],use["Analysis"],use["NoMARS"],use["MARS"],use["Total"])) 

totalacrosssite["NoMARS"] = totalacrosssite["Total"] - totalacrosssite["MARS"]
print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%("Total",totalacrosssite["Production"],totalacrosssite["Analysis"],totalacrosssite["NoMARS"],totalacrosssite["MARS"],totalacrosssite["Total"]))      


# In[13]:


# Make a table for each type:


# In[14]:


# header = "   time in %s by site        "%outunits
# header2 = header

# for date in dates:
#     header += "%10s"%date
#     header2 += ",%s"%date
# header += "     Total"
# header2 += ",Total\n"

# out = {}
# for type in types:
#     outname = "output/%s_BySite_%s_%s_%s.csv"%(type,outunits,lowdate,highdate)
#     out[type] = open(outname,'w')
#     out[type].write(header2+"\n")

# print (sites) 
# for type in types:   
#     for site in sites:
#         result = "%30s"%site
#         outstring = "%s"%site
#         total = 0.0
#         for date in dates:
#             result += " %10.3f"%Data[type][site][date]
#             outstring += ", %10.3f"%(Data[type][site][date])
#             total += Data[type][site][date]
#         #print (outstring)
#         outstring += ",%10.3f\n"%total
#         out[type].write(outstring)
#     out[type].close()


# In[15]:


bydate(array=Data,types=types,locations=sites,dates=dates,units=outunits,tag="BySite")


# In[16]:


bydate(array=ByCountry,types=types,locations=countries,dates=dates,units=outunits,tag="ByCountry")


# In[17]:


# header = "   time in %s by country      "%outunits
# header2 = header

# for date in dates:
#     header += "%10s"%date
#     header2 += ",%s"%date
# header += "     Total"
# header2 += ",Total\n"

# out = {}
# for type in types:
#     outname = "output/%s_ByCountry_%s_%s_%s.csv"%(type,outunits,lowdate,highdate)
#     out[type] = open(outname,'w')
#     out[type].write(header2)

# print (countries) 

# for type in types:  
#     totalbydate = {}
#     for date in dates:
#         totalbydate[date] = 0.0
#     totaltotal = 0.0
#     for site in countries:
#         result = "%30s"%site
#         outstring = "%s"%site
#         total = 0.0
        
#         for date in dates:
#             result += " %10.3f"%(ByCountry[type][site][date])
#             outstring += ", %10.3f"%(ByCountry[type][site][date])
#             total += (ByCountry[type][site][date])
#             totalbydate[date]+= (ByCountry[type][site][date])
#         totaltotal+=total           
#         outstring += ",%10.3f\n"%total
#         #print (outstring)
#         out[type].write(outstring)
#     outstring = "%s"%"Total"
#     for date in dates:
#         outstring += ", %10.3f"%(totalbydate[date])
#     outstring += ",%10.3f\n"%totaltotal 
#     out[type].write(outstring)
#     out[type].close()


# In[ ]:




