Theses are Python2 scripts used for uploading data into the MySQL
database (current as per April 2018)


Last updated by A.Centeno 4-2-18
==========================
load_genotypes.py
==========================
Mainly used to enter genotype batch records
Run load_genotypes.py as:
python delete_genotypes.py /home/acenteno/copyfrom_spring211/Maintenance/dataset/Arthur-Geno-Pheno-Data/Load_Genotypes/config.ini

==========================
delete_genotypes.py
==========================
Mainly used to delete genotype batch records
Run delete_genotypes.py as:
python delete_genotypes.py /home/acenteno/copyfrom_spring211/Maintenance/dataset/Arthur-Geno-Pheno-Data/Delete_Genotypes/config.ini

==========================
load_phenotypes.py
==========================
Mainly used to enter phenotype trait batch records
Run load_phenotypes.py as:
python load_phenotypes.py /home/acenteno/copyfrom_spring211/Maintenance/dataset/Arthur-Geno-Pheno-Data/Load_Phenotypes/config.ini

==========================
delete_phenotypes.py
==========================
Mainly used to delete phenotype trait full records
Run delete_phenotypes.py as:
python delete_phenotypes.py /home/acenteno/copyfrom_spring211/Maintenance/dataset/Arthur-Geno-Pheno-Data/Delete_Phenotypes/config.ini

==========================
QTL_Reaper_v6.py
==========================
Mainly used to perform QTL reaper and obtain Max LRS values.
Run QTL_Reaper_v6.py as:
python QTL_Reaper_v6.py (and GN accession number here)

==========================
Update_Case_Attributes_MySQL_tab.py
==========================
Mainly used to enter Case attributes.
Run Update_Case_Attributes_MySQL_tab.py as:
python Update_Case_Attributes_MySQL_tab.py

==========================
readProbeSetMean_v7.py
==========================
Mainly used to enter mean expression data.
Run readProbeSetMean_v7.py as:
python readProbeSetMean_v7.py

==========================
readProbeSetSE_v7.py
==========================
Mainly used to enter Standard Error values from expression data.
Run readProbeSetSE_v7.py as:
python readProbeSetSE_v7.py

==========================
MYSQL command CALCULATE MEANS NEW Structure:
==========================
Mainly used to calculate mean from expression data values.
update ProbeSetXRef set mean = (select AVG(value) from ProbeSetData where ProbeSetData.Id = ProbeSetXRef.DataId) where ProbeSetXRef.ProbeSetFreezeId = 811;
