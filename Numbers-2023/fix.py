import string, os, sys

list = sys.argv[1:]

if not os.path.exists("fixed"): os.mkdir("fixed")

for i in list:
    print ("file",i)
    old = open(i,'r')
    new = open("fixed/"+i,'w')
    lines = old.readlines()
    for line in lines:
        print (line)
        print (line[-2:])
        newline = line
        if "," in line[-2:]:
            newline = line[0:-2]+"\n"
        
        print (newline)
        new.write(newline)
