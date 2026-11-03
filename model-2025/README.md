# DUNE Offline Data Model code

## main code

The model itself is in files with names like

`2025-12-10.ipynb`  which is a jupyter notebook.

It can be converted into a python script via

~~~
../convert.sh 2025-12-10.ipynb
~~~

and then run as 

~~~
python 2025-12-10.py
~~~

The notebook needs no editing to start a run - it takes the configuration file, the
output directory and every other parameter from the json file (see below).

## configuration files

A run is configured by two files:

`NearTerm_2025-12-10-2040.json` and `NearTerm_2025-12-10-2040_timeline.csv` which
provide time independent and time dependent configurations.

The json file also contains everything needed to *start* the run, in its `Run` block,
so nothing has to be edited in the code itself:

~~~
  "Run":{
        "ConfigFile":"NearTerm_2025-12-10-2040.json", // this file
        "Notebook":"2025-12-10.ipynb",                // driver notebook
        "OutputDir":"",                               // derived from the name if empty
        "Glossary":true                               // also write a glossary to check macros
    },
~~~

The output subdirectory is derived from the config file name by replacing the nominal
end year with `MaxYear` and adding the memory weighting tag, so
`NearTerm_2025-12-10-2040.json` with `"MaxYear": 2030` writes into
`NearTerm_2025-12-10-2030_noMWC`.  Set `OutputDir` to override that.

To start a new run, copy the json (and timeline) files, update the `Run` block, and
run the notebook - it selects the config file that declares a `Run` block with the
highest `Version`.

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

## gpu processing

The model calculates GPU use per detector and data type but keeps it at the `Total`
site until the `Splits` table is applied.  `holder.GPUBreakdown(Dir,texfile)` does
that in one call and produces a figure and table for each GPU unit (MHr, wall time,
kHS23-Yr, cores) broken down:

* by site - `GPU-Processing-by-Site-<unit>.png`
* by detector - `GPU-Processing-by-Detector-<unit>.png`
* by data type - `GPU-Processing-by-Type-<unit>.png`

The three breakdowns each sum to the same total, which is unchanged from before the
split.  It is built out of smaller pieces, in case only some of it is wanted:

`holder.splitResourceBySite(resources)` spreads resources held at `Total` over the
sites using the per-detector-class fractions, and leaves series that already exist
alone, so it is safe to call twice.

`holder.gpuTotals(resources)` then makes the `Total` detector and data type series
that `Draw` needs for its total curve.

`holder.gpuResources()`, `holder.resourceUnits(resource)`, `holder.detectorSplit(det)`
and `holder.splitFactors(det,resource)` are the lookups those use.  Note that
`resourceUnits` reads the units back out of the holder rather than trusting
`BaseUnits` in the json file, which has to be kept in step by hand with the units
`Scales` actually produces.

## TeX output

~~~
python 2025-12-10.py
~~~ 

will run the main program and produce a subdirectory named after the configuration
file (see above) with all of the csv, png and tex files for individual plots.

it will also produce a file, `<jsonname>_results.csv` with a full dump of the holder contents. 

The notebook writes the LaTeX macros and summary tables for the run itself, via
`json2tex.runit(config=config)`.  They can also be made on their own:

~~~
python json2tex.py                                  # newest config in this directory
python json2tex.py NearTerm_2025-12-10-2040.json    # a particular one
python json2tex.py --no-glossary                    # macros only, no glossary
~~~

which puts tables and macros based on the json file into the subdirectory.  There is
no need to edit `json2tex.py` before running it.

`CCB-Report-2025-v6.tex` is an example which uses the macros and tables generated above to produce a report. 

In principle, you can auto-generate reports with different assumptions by changing the output subdirectory name.

## maintenance

There is a script `gitadd.sh` that adds only the active files. 









