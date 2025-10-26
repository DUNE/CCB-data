# DUNE Offline Data Model code

## main code

The model itself is in files with names like

`2024-08-25.ipynb`  which is a jupyter notebook.

It can be converted into a python script via

~~~
../convert.sh 2024-08-25.ipynb
~~~

and then run as 

~~~
python 2024-08-25.py
~~~

## configuration files

The driver is configured via two files:

`NearTerm_2024-08-27-2040.json` and `NearTerm_2024-08-27-2040_timeline.csv` which
provide time independent and time dependent configurations. 

Those drivers can be translated into LaTeX compatible tables and commands via the script `json2tex`.  

## utility files

`NumberUtils.py` is mainly obsolete and only used in a few places.

`DataHolder.py` is the main engine for the simulation.  It has methods to read and transform inputs and to summarize them as graphs and tables.  It includes a small test suite for most methods. 

## internal model 

The internal model is based on classifying time series (year by year) by "Categories"

0. Detector - which of the many DUNE detectors is it?
1. DataType - what kind of data is it? analogous to data_tier 
2. Resource - CPU, Disk, Tape ... 
3. Location - Where is the resource - currently US, CERN, Global
4. Units - what are the units? A data series can be stored with different units. 

Valid values for all of these categories are listed in the json file. 

For each time series a tag constructed from these variables is used to index the information within the `DataHolder`

tag = Detector!DataType!Resource!Location!Units

each tag is associated with a time series stored in `self.holder[tag]` and an explanation stored in `self.explanations[tag]`.

Given the large number of detectors, data type, resources and locations, the program ends up with ~1,500 time series after all combinations and aggregations are done.  

## algorithm

each internal object can be transformed by `scaling`, `cumulation` and `extension`. 

groups of objects can be defined by `filters` and then aggregated and output.

filters have the form:

~~~
aFilter =  {"Detectors":[<detectors>],
            "DataTypes":[<datatypes>],
            "Resources":[<resources>],
            "Locations":[<locations>],
            "Units":[<units>]
            }
~~~

that filter can then be changed into a list of tag which can be summed over and passed to the graphics routines.

## output

The results can be output via the methods:

`holder.csvDump(dir,name,filter,dropColumns,format)` which produces a csv dump of the full holder or of subsets based on the filter.  `dropColumns` and `format` allow you to only output some fields and maintain a consistent format. 

`figname = holder.Draw(Dir,Title,YAxis,Resource,Category,filter,format)` takes a subset defined by `filter` and plots a `Resource` with separate curves for categories within `Category`.   `Title` gives the plot a title and a name while `YAxis` labels the y axis.  (The x axis is years).  The Draw method returns the path to the output figure.

One can then do:

`texname = holder.TexBoth(figname,caption,label)` which will produce LaTeX which both draws the plot and adds a table with the values.

## TeX output

~~~
python 2024-08-25.py
~~~ 

will run the main program and produce a subdirectory `<jsonname>_noMWC` with all of the csv, png and tex files for individual plots.

it will also produce a file, `<jsonname>_results.csv` with a full dump of the holder contents. 

To produce a report, first make a LaTeX summary of the configuration.

~~~
python json2tex.py
~~~

which puts tables and macros based on the json file into the subdirectory.

`CCB-Report-2025-v0.tex` is an example which uses the macros and tables generated above to produce a report. 

In principle, you can auto-generate reports with different assumptions by changing the output subdirectory name.

## maintenance

There is a script `gitadd.sh` that adds only the active files. 









