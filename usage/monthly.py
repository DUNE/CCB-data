#!/usr/bin/env python
# coding: utf-8

# In[1]:


# link = "https://fifemon.fnal.gov/kibana/app/kibana#/visualize/edit/33d02c40-8b41-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'))&_a=(filters:!(),linked:!f,query:(language:lucene,query:'Jobsub_Group:dune'),uiState:(vis:(params:(sort:(columnIndex:!n,direction:!n)))),vis:(aggs:!((enabled:!t,id:'1',params:(field:SlotHours),schema:metric,type:sum),(enabled:!t,id:'3',params:(field:MachineAttrGLIDEIN_DUNESite0,missingBucket:!f,missingBucketLabel:Missing,order:desc,orderBy:'1',otherBucket:!f,otherBucketLabel:Other,size:50),schema:bucket,type:terms),(enabled:!t,id:'5',params:(customInterval:'2h',drop_partials:!f,extended_bounds:(),field:'@timestamp',interval:M,min_doc_count:1,timeRange:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'),useNormalizedEsInterval:!t),schema:bucket,type:date_histogram),(enabled:!t,id:'4',params:(filters:!((input:(query:'NOT(Owner:dunepro)%20AND%20NOT(Jobsub_SubGroup:mars)'),label:Analysis),(input:(query:'Owner:dunepro'),label:Production),(input:(query:'Jobsub_SubGroup:mars'),label:MARS),(input:(query:'*'),label:Total))),schema:bucket,type:filters)),params:(perPage:24,showMetricsAtAllLevels:!f,showPartialRows:!f,showTotal:!f,sort:(columnIndex:!n,direction:!n),totalFunc:sum),title:'DUNE%20monthly%20slot%20hours%20by%20site%20and%20role',type:table))"


# In[2]:


# go to that link, go to inspect and save as formatted csv


# In[ ]:





# In[3]:


import csv

# ken
#  "https://fifemon.fnal.gov/kibana/app/kibana#/visualize/edit/33d02c40-8b41-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'))&_a=(filters:!(),linked:!f,query:(language:lucene,query:'Jobsub_Group:dune'),uiState:(vis:(params:(sort:(columnIndex:!n,direction:!n)))),vis:(aggs:!((enabled:!t,id:'1',params:(field:SlotHours),schema:metric,type:sum),(enabled:!t,id:'3',params:(field:MachineAttrGLIDEIN_DUNESite0,missingBucket:!f,missingBucketLabel:Missing,order:desc,orderBy:'1',otherBucket:!f,otherBucketLabel:Other,size:50),schema:bucket,type:terms),(enabled:!t,id:'5',params:(customInterval:'2h',drop_partials:!f,extended_bounds:(),field:'@timestamp',interval:M,min_doc_count:1,timeRange:(from:'2022-01-01T06:00:00.000Z',mode:absolute,to:'2023-11-25T03:09:25.714Z'),useNormalizedEsInterval:!t),schema:bucket,type:date_histogram),(enabled:!t,id:'4',params:(filters:!((input:(query:'NOT(Owner:dunepro)%20AND%20NOT(Jobsub_SubGroup:mars)'),label:Analysis),(input:(query:'Owner:dunepro'),label:Production),(input:(query:'Jobsub_SubGroup:mars'),label:MARS),(input:(query:'*'),label:Total))),schema:bucket,type:filters)),params:(perPage:24,showMetricsAtAllLevels:!f,showPartialRows:!f,showTotal:!f,sort:(columnIndex:!n,direction:!n),totalFunc:sum),title:'DUNE%20monthly%20slot%20hours%20by%20site%20and%20role',type:table))"

# wenlong https://fifemon.fnal.gov/kibana/app/kibana#/dashboard/83d7b0c0-8b1c-11ee-804b-5759672b811c?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-1y,mode:quick,to:now))&_a=(description:%27%27,filters:!(),fullScreenMode:!f,options:(darkTheme:!t,hidePanelTitles:!f,useMargins:!t),panels:!((embeddableConfig:(),gridData:(h:14,i:%271%27,w:48,x:0,y:0),id:%2757162130-8b1b-11ee-804b-5759672b811c%27,panelIndex:%271%27,type:visualization,version:%276.8.23%27),(embeddableConfig:(),gridData:(h:16,i:%272%27,w:48,x:0,y:14),id:%275ee81fc0-8b1c-11ee-804b-5759672b811c%27,panelIndex:%272%27,type:visualization,version:%276.8.23%27)),query:(language:lucene,query:%27%27),timeRestore:!t,title:fifebatch-jobs-dune,viewMode:view)


name = 'DUNE monthly slot hours by site and role-2.csv'
inunits="Hr"
outunits = "MHr"
units=1000000.
Data = {}
ByCountry = {}
sites = []
types = []
dates = []
countries = []


# In[4]:


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
 


# In[5]:


# fill in the blanks and sort by country

for type in types:
    for site in sites:
        if site not in Data[type].keys():
            Data[type][site]={}
        for date in dates:
            if date not in Data[type][site].keys():
                Data[type][site][date] = 0.0
        #print (type,site, Data[type][site])
        


# In[6]:


lowdate = "2022-11"
highdate = "2023-10"


# In[7]:


print ("Usage in %s between %s and %s"%(outunits,lowdate,highdate))
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
        totalacrosssite[type] += use[type]
    use["NoMARS"] = use["Total"] - use["MARS"]  
    print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%(site,use["Production"],use["Analysis"],use["NoMARS"],use["MARS"],use["Total"])) 

totalacrosssite["NoMARS"] = totalacrosssite["Total"] - totalacrosssite["MARS"]
print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%("Total",totalacrosssite["Production"],totalacrosssite["Analysis"],totalacrosssite["NoMARS"],totalacrosssite["MARS"],totalacrosssite["Total"]))      


# In[ ]:





# In[8]:


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


# In[9]:


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
    use["NoMARS"] = use["Total"] - use["MARS"]  
    print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%(site,use["Production"],use["Analysis"],use["NoMARS"],use["MARS"],use["Total"])) 

totalacrosssite["NoMARS"] = totalacrosssite["Total"] - totalacrosssite["MARS"]
print ("%30s %10.3f %10.3f %10.3f %10.3f %10.3f"%("Total",totalacrosssite["Production"],totalacrosssite["Analysis"],totalacrosssite["NoMARS"],totalacrosssite["MARS"],totalacrosssite["Total"]))      


# In[ ]:




