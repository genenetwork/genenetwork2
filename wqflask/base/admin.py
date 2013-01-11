# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by GeneNetwork Core Team 2010/10/20





#XZ, 04/02/2009: we should put this into database.


###LIST of databases used into gene name query


ADMIN_search_dbs = {
                    'rat': {'PERITONEAL FAT': ['FT_2A_0605_Rz'],
                            'KIDNEY': ['KI_2A_0405_Rz'],
                            'ADRENAL GLAND': ['HXB_Adrenal_1208'],
                            'HEART': ['HXB_Heart_1208']
                           },
                    'mouse': {'CEREBELLUM': ['CB_M_0305_R'],
                              'STRIATUM': ['SA_M2_0905_R', 'SA_M2_0405_RC', 'UTHSC_1107_RankInv', 'Striatum_Exon_0209'],
                              'HIPPOCAMPUS': ['HC_M2_0606_R', 'UMUTAffyExon_0209_RMA'],
                              'WHOLE BRAIN': ['BR_M2_1106_R', 'IBR_M_0106_R', 'BRF2_M_0805_R', 'UCLA_BHF2_BRAIN_0605'],
                              'LIVER': ['LV_G_0106_B', 'UCLA_BHF2_LIVER_0605'],
                              'EYE': ['Eye_M2_0908_R'],
                              'HEMATOPOIETIC STEM CELLS': ['HC_U_0304_R'],
                              'KIDNEY': ['MA_M2_0806_R'],
                              'MAMMARY TUMORS': ['MA_M_0704_R', 'NCI_Agil_Mam_Tum_RMA_0409'],
                              'PREFRONTAL CORTEX': ['VCUSal_1206_R'],
                              'SPLEEN': ['IoP_SPL_RMA_0509'],
                              'NUCLEUS ACCUMBENS': ['VCUSalo_1007_R'],
                              'NEOCORTEX': ['HQFNeoc_0208_RankInv'],
                              'ADIPOSE': ['UCLA_BHF2_ADIPOSE_0605'],
                              'RETINA': ['Illum_Retina_BXD_RankInv0410']
                             },
                    'human': {
                              'LYMPHOBLAST B CELL': ['Human_1008', 'UT_CEPH_RankInv0909'],
                              'WHOLE BRAIN': ['GSE5281_F_RMA0709', 'GSE15222_F_RI_0409']
                             }
                   }


###LIST of tissue alias

ADMIN_tissue_alias = {'CEREBELLUM': ['Cb'],
                      'STRIATUM': ['Str'],
                      'HIPPOCAMPUS': ['Hip'],
                      'WHOLE BRAIN': ['Brn'],
                      'LIVER': ['Liv'],
                      'EYE': ['Eye'],
                      'PERITONEAL FAT': ['Fat'],
                      'HEMATOPOIETIC STEM CELLS': ['Hsc'],
                      'KIDNEY': ['Kid'],
                      'ADRENAL GLAND': ['Adr'],
                      'HEART': ['Hea'],
                      'MAMMARY TUMORS': ['Mam'],
                      'PREFRONTAL CORTEX': ['Pfc'],
                      'SPLEEN': ['Spl'],
                      'NUCLEUS ACCUMBENS': ['Nac'],
                      'NEOCORTEX': ['Ctx'],
                      'ADIPOSE': ['Wfat'],
                      'RETINA': ['Ret']
                     }
