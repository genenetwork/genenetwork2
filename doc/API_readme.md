# API Query Documentation #
---
# Fetching Dataset/Trait info/data #
---
## Fetch Species List ##

To get a list of species with data available in GN (and their associated names and ids):
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/species
[ { "FullName": "Mus musculus", "Id": 1, "Name": "mouse", "TaxonomyId": 10090 }, ... { "FullName": "Populus trichocarpa", "Id": 10, "Name": "poplar", "TaxonomyId": 3689 } ]
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

## Fetch Genotypes for Group/RISet ##
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/genotypes/BXD
```
Returns a CSV file with metadata in the first few rows, sample/strain names as columns, and markers as rows. Currently only works for genotypes we have stored in .geno files; I'll add the option to download BIMBAM files soon.

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

## Fetch Individual Dataset Info ##
### For mRNA Assay/"ProbeSet" ###

```
curl http://gn2-zach.genenetwork.org/api/v_pre1/dataset/HC_M2_0606_P
```
OR
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/dataset/bxd/HC_M2_0606_P```
{ "confidential": 0, "data_scale": "log2", "dataset_type": "mRNA expression", "full_name": "Hippocampus Consortium M430v2 (Jun06) PDNN", "id": 112, "name": "HC_M2_0606_P", "public": 2, "short_name": "Hippocampus M430v2 BXD 06/06 PDNN", "tissue": "Hippocampus mRNA", "tissue_id": 9 }
```
(This also has the option to specify group/riset)

### For "Phenotypes" (basically non-mRNA Expression; stuff like weight, sex, etc) ###
For these traits, the query fetches publication info and takes the group and phenotype 'ID' as input. For example:
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/dataset/bxd/10001
{ "dataset_type": "phenotype", "description": "Central nervous system, morphology: Cerebellum weight, whole, bilateral in adults of both sexes [mg]", "id": 10001, "name": "CBLWT2", "pubmed_id": 11438585, "title": "Genetic control of the mouse cerebellum: identification of quantitative trait loci modulating size and architecture", "year": "2001" }
```

## Fetch Sample Data for Dataset ##
``` 
curl http://gn2-zach.genenetwork.org/api/v_pre1/sample_data/HSNIH-PalmerPublish.csv
```

Returns a CSV file with sample/strain names as the columns and trait IDs as rows

## Fetch Sample Data for Single Trait ##
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/sample_data/HC_M2_0606_P/1436869_at
[ { "data_id": 23415463, "sample_name": "129S1/SvImJ", "sample_name_2": "129S1/SvImJ", "se": 0.123, "value": 8.201 }, { "data_id": 23415463, "sample_name": "A/J", "sample_name_2": "A/J", "se": 0.046, "value": 8.413 }, { "data_id": 23415463, "sample_name": "AKR/J", "sample_name_2": "AKR/J", "se": 0.134, "value": 8.856 }, ... ]
```

## Fetch Trait List for Dataset ##
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/traits/HXBBXHPublish.json
[ { "Additive": 0.0499967532467532, "Id": 10001, "LRS": 16.2831307029479, "Locus": "rs106114574", "PhenotypeId": 1449, "PublicationId": 319, "Sequence": 1 }, ... ]
```

Both JSON and CSV formats can be specified, with CSV as default. There is also an optional "ids_only" parameter that will only return a list of trait IDs.

## Fetch Trait Info (Name, Description, Location, etc) ##
### For mRNA Expression/"ProbeSet" ###
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/trait/HC_M2_0606_P/1436869_at
{ "additive": -0.214087568058076, "alias": "HHG1; HLP3; HPE3; SMMCI; Dsh; Hhg1", "chr": "5", "description": "sonic hedgehog (hedgehog)", "id": 99602, "locus": "rs8253327", "lrs": 12.7711275309832, "mb": 28.457155, "mean": 9.27909090909091, "name": "1436869_at", "p_value": 0.306, "se": null, "symbol": "Shh" }
```

### For "Phenotypes" ###
For phenotypes this just gets the  max LRS, its location, and additive effect (as calculated by qtlreaper)

Since each group/riset only has one phenotype "dataset", this query takes either the group/riset name or the group/riset name + "Publish" (for example "BXDPublish", which is the dataset name in the DB) as input
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/trait/BXD/10001
{ "additive": 2.39444435069444, "id": 4, "locus": "rs48756159", "lrs": 13.4974911471087 }
```

---

# Analyses #
---
## Mapping ##
Currently two mapping tools can be used - GEMMA and R/qtl. qtlreaper will be added later with Christian Fischer's RUST implementation - https://github.com/chfi/rust-qtlreaper

Each method's query takes the following parameters respectively (more will be added):
### GEMMA ###
* trait_id (*required*) - ID for trait being mapped
* db (*required*) - DB name for trait above (Short_Abbreviation listed when you query for datasets)
* use_loco - Whether to use LOCO (leave one chromosome out) method (default = false)
* maf - minor allele frequency (default = 0.01)

Example query:
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/mapping?trait_id=10015&db=BXDPublish&method=gemma&use_loco=true
```

### R/qtl ###
(See the R/qtl guide for information on some of these options - http://www.rqtl.org/manual/qtl-manual.pdf)
* trait_id (*required*) - ID for trait being mapped
* db (*required*) - DB name for trait above (Short_Abbreviation listed when you query for datasets)
* rqtl_method - hk (default) | ehk | em | imp | mr | mr-imp | mr-argmax ; Corresponds to the "method" option for the R/qtl scanone function.
* rqtl_model - normal (default) | binary | 2-part | np ; corresponds to the "model" option for the R/qtl scanone function
* num_perm - number of permutations; 0 by default
* control_marker - Name of marker to use as control; this relies on the user knowing the name of the marker they want to use as a covariate
* interval_mapping - Whether to use interval mapping; "false" by default
* pair_scan - *NYI*

Example query:
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/mapping?trait_id=1418701_at&db=HC_M2_0606_P&method=rqtl&num_perm=100
```

Some combinations of methods/models may not make sense. The R/qtl manual should be referred to for any questions on its use (specifically the scanone function in this case)

## Calculate Correlation ##
Currently only Sample and Tissue correlations are implemented

This query currently takes the following parameters (though more will be added):
* trait_id (*required*) - ID for trait used for correlation
* db (*required*) - DB name for the trait above (this is the Short_Abbreviation listed when you query for datasets)
* target_db (*required*) - Target DB name to be correlated against
* type - sample (default) | tissue
* method - pearson (default) | spearman
* return - Number of results to return (default = 500)

Example query:
```
curl http://gn2-zach.genenetwork.org/api/v_pre1/correlation?trait_id=1427571_at&db=HC_M2_0606_P&target_db=BXDPublish&type=sample&return_count=100
[ { "#_strains": 6, "p_value": 0.004804664723032055, "sample_r": -0.942857142857143, "trait": 20511 }, { "#_strains": 6, "p_value": 0.004804664723032055, "sample_r": -0.942857142857143, "trait": 20724 }, { "#_strains": 12, "p_value": 1.8288943424888848e-05, "sample_r": -0.9233615170820528, "trait": 13536 }, { "#_strains": 7, "p_value": 0.006807187408935392, "sample_r": 0.8928571428571429, "trait": 10157 }, { "#_strains": 7, "p_value": 0.006807187408935392, "sample_r": -0.8928571428571429, "trait": 20392 }, ... ]
```
