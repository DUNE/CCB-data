import sys,os

fname = sys.argv[1]
if ".json" not in fname or not os.path.exists(fname):
    print ("input must be a json file name")
    sys.exit(0)

gname = fname.replace(".json","_clean.json")
print (fname, gname)
f = open(fname,'r')
g = open(gname,'w')

lines = f.readlines()
f.close()
for line in lines:
    newline = line.split("#")[0]
    g.write(newline)

g.close()