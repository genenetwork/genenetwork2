# API Command Documentation #

## Fetch Species List ##

To get a list of species with data available in GN (and their associated names and ids):
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/species
[
  {
    "FullName": "Mus musculus", 
    "Id": 1, 
    "Name": "mouse", 
    "TaxonomyId": 10090
  }, 
  ...
  {
    "FullName": "Populus trichocarpa", 
    "Id": 10, 
    "Name": "poplar", 
    "TaxonomyId": 3689
  }
]
```

Or to get a single species info:
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/species/mouse
``` 
OR 
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/species/mouse.json
```

*For all queries where the last field is a user-specified name/ID, there will be the option to append a file format type. Currently there is only JSON (and it will default to JSON if none is provided), but other formats will be added later*

## Fetch Groups/RISets ##

This query can optionally filter by species:

```
curl http://gn2-zach.genenetwork.org/api/v_pre1/groups (for all species)
```
OR
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/mouse/groups (for just mouse groups/RISets)
[ { "DisplayName": "BXD", "FullName": "BXD RI Family", "GeneticType": "riset", "Id": 1, "MappingMethodId": "1", "Name": "BXD", "SpeciesId": 1, "public": 2 }, ... { "DisplayName": "AIL LGSM F34 and F39-43 (GBS)", "FullName": "AIL LGSM F34 and F39-43 (GBS)", "GeneticType": "intercross", "Id": 72, "MappingMethodId": "2", "Name": "AIL-LGSM-F34-F39-43-GBS", "SpeciesId": 1, "public": 2 } ]
```

## Fetch Datasets ##
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/datasets/bxd
```
OR
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/datasets/mouse/bxd
[ { "AvgID": 1, "CreateTime": "Fri, 01 Aug 2003 00:00:00 GMT", "DataScale": "log2", "FullName": "UTHSC/ETHZ/EPFL BXD Liver Polar Metabolites Extraction A, CD Cohorts (Mar 2017) log2", "Id": 1, "Long_Abbreviation": "BXDMicroArray_ProbeSet_August03", "ProbeFreezeId": 3, "ShortName": "Brain U74Av2 08/03 MAS5", "Short_Abbreviation": "Br_U_0803_M", "confidentiality": 0, "public": 0 }, ... { "AvgID": 3, "CreateTime": "Tue, 14 Aug 2018 00:00:00 GMT", "DataScale": "log2", "FullName": "EPFL/LISP BXD CD Liver Affy Mouse Gene 1.0 ST (Aug18) RMA", "Id": 859, "Long_Abbreviation": "EPFLMouseLiverCDRMAApr18", "ProbeFreezeId": 181, "ShortName": "EPFL/LISP BXD CD Liver Affy Mouse Gene 1.0 ST (Aug18) RMA", "Short_Abbreviation": "EPFLMouseLiverCDRMA0818", "confidentiality": 0, "public": 1 } ]
```
(I added the option to specify species just in case we end up with the same group name across multiple species at some point, though it's currently unnecessary)




