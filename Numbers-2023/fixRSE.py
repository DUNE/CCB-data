import os,sys,string

spread = sys.argv[1]

f = open(spread,'r')
g = open(spread.replace(".csv","-fixed.csv"),'w')

lines = f.readlines()

g.write(lines[0])
for l in lines[1:]:

    #print (l)
    x = l.strip().split(",")

    xlast = x[len(x)-1]
    print (x)
    newline = ""
    #print (x)
    for y in x:
        #print(y)

        if "TB" in y:
            s = y.split("TB")
            val = float(s[0])/1000.
            newline += "%6.3f,"%val
        elif "GB" in y:
            s = y.split("GB")
            val = float(s[0])/1000/1000.
            newline += "%6.3f,"%val
        elif "MB" in y:
            s = y.split("MB")
            val = float(s[0])/1000/1000./1000.
            newline += "%6.3f,"%val
        elif "PB" in y:
            s = y.split("PB")
            val = float(s[0])
            newline += "%6.3f,"%val
        else:
            newline += y+","

        #print (x,y,newline)
    g.write(newline[:-1]+"\n")
    print (newline[:-1]+"\n")
g.close()
