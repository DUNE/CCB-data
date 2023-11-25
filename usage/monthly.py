import csv

Data = {}
sites = []
types = []
dates = []
with open('DUNE monthly slot hours by site and role-2.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    
    for row in csv_reader:
        print (row)
        line_count += 1
        if line_count == 1:
            labels = row
            continue
        site = row[0]   
        date = row[1]
        type = row[2]
        value = row[3]
        

        
        if type not in Data.keys():
            print ("add type",type)
            Data[type]={}
            types.append(type)
            
        if site not in Data[type].keys():
            print ("add site",site)
            Data[type][site]={}
        
        if type not in types: types.append(type)
        if site not in sites: sites.append(site)
        if date not in dates: dates.append(date)
            
#         if date not in Data[type][site].keys():
#             print ("add date",date)
#             dates.append(date)
        
        Data[type][site][date]=value
        
        # print (Data)
print (sites,types,dates)        
       
for type in types:
    for site in sites:
        if site not in Data[type].keys():
            Data[type][site]={}
        for date in dates:
            if date not in Data[type][site].keys():
                Data[type][site][date] = 0.0
        print (type,site, Data[type][site])
            




        
       
        
        