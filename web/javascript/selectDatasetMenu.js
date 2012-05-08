var sArr = [
{txt:'',val:''},
{txt:'Human',val:'human'},
{txt:'Macaque monkey',val:'macaque monkey'},
{txt:'Mouse',val:'mouse'},
{txt:'Rat',val:'rat'},
{txt:'Drosophila',val:'drosophila'},
{txt:'Arabidopsis thaliana',val:'arabidopsis'},
{txt:'Barley',val:'barley'},
{txt:'Soybean',val:'soybean'},
{txt:'Tomato',val:'tomato'},
{txt:'All Species',val:'All Species'}];

var gArr = [
{txt:'',val:''},
{txt:'AD Cases & Controls (Liang)',val:'AD-cases-controls'},
{txt:'AD Cases & Controls (Myers)',val:'AD-cases-controls-Myers'},
{txt:'AKXD',val:'AKXD'},
{txt:'AXB/BXA',val:'AXBXA'},
{txt:'B6BTBRF2',val:'B6BTBRF2'},
{txt:'B6D2F2',val:'B6D2F2'},
{txt:'BayXSha',val:'BayXSha'},
{txt:'BDF2 UCLA',val:'BDF2-1999'},
{txt:'BDF2-2005',val:'BDF2-2005'},
{txt:'BHF2 (Apoe Null) UCLA',val:'BHF2'},
{txt:'BH/HB F2 UCLA',val:'BHHBF2'},
{txt:'BXD',val:'BXD'},
{txt:'BXH',val:'BXH'},
{txt:'CANDLE',val:'CANDLE'},
{txt:'CEPH Families',val:'CEPH-2004'},
{txt:'ColXBur',val:'ColXBur'},
{txt:'ColXCvi',val:'ColXCvi'},
{txt:'CastB6/B6Cast F2 UCLA',val:'CTB6F2'},
{txt:'CXB',val:'CXB'},
{txt:'Drosophila Genetic Reference Panel',val:'DGRP'},
{txt:'Harvard Brain Tissue Resource Center',val:'HB'},
{txt:'Human Liver Cohort',val:'HLC'},
{txt:'Heterogeneous Stock',val:'HS'},
{txt:'Heterogeneous Stock Collaborative Cross',val:'HS-CC'},
{txt:'KIN/YSM',val:'HSB'},
{txt:'HXB/BXH',val:'HXBBXH'},
{txt:'J12XJ58F2',val:'J12XJ58F2'},
{txt:'LXP',val:'LXP'},
{txt:'LXS',val:'LXS'},
{txt:'Macaca fasicularis (Cynomolgus monkey)',val:'Macaca-fasicularis'},
{txt:'Mouse Diversity Panel',val:'MDP'},
{txt:'NZB/FVB N2 NCI',val:'NZBXFVB-N2'},
{txt:'Oregon-R x 2b3',val:'Oregon-R_x_2b3'},
{txt:'QSM',val:'QSM'},
{txt:'UIOWA SRxSHRSP F2',val:'SRxSHRSPF2'},
{txt:'SXM',val:'SXM'},
{txt:'All Groups',val:'all groups'}];

var tArr = [
{txt:'',val:''},
{txt:'Adipose mRNA',val:'Adipose'},
{txt:'Adrenal Gland mRNA',val:'Adrenal Gland'},
{txt:'Amygdala mRNA',val:'Amygdala'},
{txt:'Brain mRNA',val:'Brain'},
{txt:'Cartilage mRNA',val:'Cartilage'},
{txt:'Caudal Ganglionic Eminence mRNA',val:'Caudal Ganglionic Eminence'},
{txt:'Cerebellar Cortex mRNA',val:'Cerebellar Cortex'},
{txt:'Cerebellum mRNA',val:'Cerebellum'},
{txt:'Diencephalon mRNA',val:'Diencephalon'},
{txt:'Dorsal Thalamus mRNA',val:'Dorsal Thalamus'},
{txt:'Dorsolateral Prefrontal Cortex mRNA',val:'Dorsolateral Prefrontal Cortex'},
{txt:'Embryo mRNA',val:'Embryo'},
{txt:'Eye mRNA',val:'Eye'},
{txt:'Frontal Cerebral Wall mRNA',val:'Frontal Cerebral Wall'},
{txt:'Heart mRNA',val:'Heart'},
{txt:'Hematopoietic Cells mRNA',val:'Hematopoietic Cells'},
{txt:'Hippocampus mRNA',val:'Hippocampus'},
{txt:'Hypothalamus mRNA',val:'Hypothalamus'},
{txt:'Inferior Temporal Cortex mRNA',val:'Inferior Temporal Cortex'},
{txt:'Kidney mRNA',val:'Kidney'},
{txt:'Lateral Ganglionic Eminence mRNA',val:'Lateral Ganglionic Eminence'},
{txt:'Leaf mRNA',val:'Leaf'},
{txt:'Leucocytes mRNA',val:'Leucocytes'},
{txt:'Liver mRNA',val:'Liver'},
{txt:'Lung mRNA',val:'Lung'},
{txt:'Lymphoblast B-cell mRNA',val:'Lymphoblast B-cell'},
{txt:'Mammary Tumors mRNA',val:'Mammary Tumors'},
{txt:'Medial Ganglionic Eminence mRNA',val:'Medial Ganglionic Eminence'},
{txt:'Medial Prefrontal Cortex mRNA',val:'Medial Prefrontal Cortex'},
{txt:'Mediodorsal Nucleus of Thalamus mRNA',val:'Mediodorsal Nucleus of Thalamus'},
{txt:'Midbrain mRNA',val:'Midbrain'},
{txt:'Muscle mRNA',val:'Muscle'},
{txt:'Neocortex mRNA',val:'Neocortex'},
{txt:'Newborn Cord Blood mRNA',val:'Newborn Cord Blood'},
{txt:'Nucleus Accumbens mRNA',val:'Nucleus Accumbens'},
{txt:'Occipital Cerebral Wall mRNA',val:'Occipital Cerebral Wall'},
{txt:'Orbital Prefrontal Cortex mRNA',val:'Orbital Prefrontal Cortex'},
{txt:'Parietal Cerebral Wall mRNA',val:'Parietal Cerebral Wall'},
{txt:'Peritoneal Fat mRNA',val:'Peritoneal Fat'},
{txt:'Posterior Inferior Parietal Cortex mRNA',val:'Posterior Inferior Parietal Cortex'},
{txt:'Posterior Superior Temporal Cortex mRNA',val:'Posterior Superior Temporal Cortex'},
{txt:'Prefrontal Cortex mRNA',val:'Prefrontal Cortex'},
{txt:'Primary Auditory (A1) Cortex mRNA',val:'Primary Auditory (A1) Cortex'},
{txt:'Primary Motor (M1) Cortex mRNA',val:'Primary Motor (M1) Cortex'},
{txt:'Primary Somatosensory (S1) Cortex mRNA',val:'Primary Somatosensory (S1) Cortex'},
{txt:'Primary Visual Cortex mRNA',val:'Primary Visual Cortex'},
{txt:'Retina mRNA',val:'Retina'},
{txt:'Spleen mRNA',val:'Spleen'},
{txt:'Striatum mRNA',val:'Striatum'},
{txt:'T Cell (helper) mRNA',val:'T Cell (helper)'},
{txt:'T Cell (regulatory) mRNA',val:'T Cell (regulatory)'},
{txt:'Temporal Cerebral Wall mRNA',val:'Temporal Cerebral Wall'},
{txt:'Thymus mRNA',val:'Thymus'},
{txt:'Upper (Rostral) Rhombic Lip mRNA',val:'Upper (Rostral) Rhombic Lip'},
{txt:'Ventral Forebrain mRNA',val:'Ventral Forebrain'},
{txt:'Ventral Tegmental Area mRNA',val:'Ventral Tegmental Area'},
{txt:'Ventrolateral Prefrontal Cortex mRNA',val:'Ventrolateral Prefrontal Cortex'},
{txt:'Whole Body mRNA',val:'Whole Body'},
{txt:'Phenotypes',val:'Phenotypes'},
{txt:'Genotypes',val:'Genotypes'}];

var dArr = [
{txt:'',val:''},
{txt:'GSE15222 Human Brain Normal Myers (Apr09) RankInv',val:'GSE15222_F_N_RI_0409'},
{txt:'GSE15222 Human Brain Alzheimer Myers (Apr09) RankInv',val:'GSE15222_F_A_RI_0409'},
{txt:'INIA Macaca fasicularis Nucleus Accumbens (Jan10) RMA **',val:'INIA_MacFas_Ac_RMA_0110'},
{txt:'UCLA CTB6/B6CTF2 Brain (2005) mlratio',val:'UCLA_CTB6B6CTF2_BRAIN_2005'},
{txt:'INIA Macaca fasicularis Hippocampus (Jan10) RMA **',val:'INIA_MacFas_Hc_RMA_0110'},
{txt:'UCLA CTB6/B6CTF2 Liver (2005) mlratio',val:'UCLA_CTB6B6CTF2_LIVER_2005'},
{txt:'UCLA CTB6/B6CTF2 Muscle (2005) mlratio',val:'UCLA_CTB6B6CTF2_MUSCLE_2005'},
{txt:'UCLA CTB6/B6CTF2 Adipose (2005) mlratio',val:'UCLA_CTB6B6CTF2_ADIPOSE_2005'},
{txt:'UCLA CTB6B6CTF2 Adipose Female mlratio **',val:'UCLA_CTB6B6CTF2_ADIPOSE_FEMALE'},
{txt:'UCLA CTB6B6CTF2 Brain Female mlratio **',val:'UCLA_CTB6B6CTF2_BRAIN_FEMALE'},
{txt:'UCLA CTB6B6CTF2 Muscle Female mlratio **',val:'UCLA_CTB6B6CTF2_MUSCLE_FEMALE'},
{txt:'UCLA CTB6B6CTF2 Liver Female mlratio **',val:'UCLA_CTB6B6CTF2_LIVER_FEMALE'},
{txt:'INIA Macaca fasicularis Amygdala (Jan10) RMA **',val:'INIA_MacFas_AMG_RMA_0110'},
{txt:'VU BXD Midbrain Agilent SurePrint G3 Mouse GE (May12) Quantile',val:'VUBXDMouseMidBrainQ0512'},
{txt:'GSE16780 UCLA Hybrid MDP Liver Affy HT M430A (Sep11) RMA',val:'GSE16780_UCLA_ML0911'},
{txt:'EPFL/LISP BXD CD Muscle Affy Mouse Gene 1.0 ST (Dec11) RMA **',val:'EPFLMouseMuscleCDRMA1211'},
{txt:'EPFL/LISP BXD Muscle Affy Mouse Gene 1.0 ST (Dec11) RMA **',val:'EPFLMouseMuscleRMA1211'},
{txt:'EPFL/LISP BXD HFD Muscle Affy Mouse Gene 1.0 ST (Dec11) RMA **',val:'EPFLMouseMuscleHFDRMA1211'},
{txt:'BIDMC/UTHSC Dev Striatum P14 ILMv6.2 (Nov11) RankInv **',val:'DevStriatum_ILM6.2P14RInv_1111'},
{txt:'BIDMC/UTHSC Dev Striatum P3 ILMv6.2 (Nov11) RankInv **',val:'DevStriatum_ILM6.2P3RInv_1111'},
{txt:'BIDMC/UTHSC Dev Neocortex P14 ILMv6.2 (Nov11) RankInv',val:'DevNeocortex_ILM6.2P14RInv_1111'},
{txt:'BIDMC/UTHSC Dev Neocortex P3 ILMv6.2 (Nov11) RankInv',val:'DevNeocortex_ILM6.2P3RInv_1111'},
{txt:'HEI Retina Illumina V6.2 (April 2010) RankInv',val:'Illum_Retina_BXD_RankInv0410'},
{txt:'B6D2 ONC Illumina v6.1 (Apr12) RankInv **',val:'B6D2ONCILM_0412'},
{txt:'ONC Retina Illumina V6.2 (Apr12) RankInv **',val:'ONCRetILM6_0412'},
{txt:'HEI ONC Retina Illumina V6.2 (Sep11) RankInv **',val:'HEIONCRetILM6_0911'},
{txt:'HEI ONC vs Control Retina Illumina V6.2 (Sep11) RankInv **',val:'HEIONCvsCRetILM6_0911'},
{txt:'G2 HEI ONC Retina Illumina V6.2 (Sep11) RankInv **',val:'G2HEIONCRetILM6_0911'},
{txt:'JAX Liver Affy M430 2.0 (Jul11) MDP',val:'JAX_CSB_L_0711'},
{txt:'JAX Liver HF Affy M430 2.0 (Jul11) MDP',val:'JAX_CSB_L_HF_0711'},
{txt:'JAX Liver 6C Affy M430 2.0 (Jul11) MDP',val:'JAX_CSB_L_6C_0711'},
{txt:'CANDLE Newborn Cord ILMv6.3 (Jun11) QUANT **',val:'CANDLE_NB_0711'},
{txt:'KIN/YSM Human HIP Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_HIP_0711'},
{txt:'KIN/YSM Human MFC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_MFC_0711'},
{txt:'KIN/YSM Human VFC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_VFC_0711'},
{txt:'KIN/YSM Human VF Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_VF_0711'},
{txt:'KIN/YSM Human MGE Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_MGE_0711'},
{txt:'KIN/YSM Human OC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_OC_0711'},
{txt:'KIN/YSM Human V1C Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_V1C_0711'},
{txt:'KIN/YSM Human URL Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_URL_0711'},
{txt:'KIN/YSM Human TC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_TC_0711'},
{txt:'KIN/YSM Human STR Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_STR_0711'},
{txt:'KIN/YSM Human OFC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_OFC_0711'},
{txt:'KIN/YSM Human PC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_PC_0711'},
{txt:'KIN/YSM Human S1C Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_S1C_0711'},
{txt:'KIN/YSM Human MD Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_MD_0711'},
{txt:'KIN/YSM Human STC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_STC_0711'},
{txt:'KIN/YSM Human FC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_FC_0711'},
{txt:'KIN/YSM Human DIE Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_DIE_0711'},
{txt:'KIN/YSM Human DFC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_DFC_0711'},
{txt:'KIN/YSM Human CGE Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_CGE_0711'},
{txt:'KIN/YSM Human DTH Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_DTH_0711'},
{txt:'KIN/YSM Human CBC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_CBC_0711'},
{txt:'KIN/YSM Human AMY Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_AMY_0711'},
{txt:'KIN/YSM Human A1C Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_A1C_0711'},
{txt:'KIN/YSM Human IPC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_IPC_0711'},
{txt:'KIN/YSM Human ITC Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_ITC_0711'},
{txt:'KIN/YSM Human LGE Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_LGE_0711'},
{txt:'KIN/YSM Human M1C Affy Hu-Exon 1.0 ST (Jul11) Quantile **',val:'KIN_YSM_M1C_0711'},
{txt:'HBTRC-MLC Human Cerebellum Agilent (Jun11) mlratio',val:'HBTRC-MLC_0611'},
{txt:'HBTRC-MLC Human Cerebellum Agilent Normal (Jun11) mlratio',val:'HBTRC-MLC_N_0611'},
{txt:'HBTRC-MLC Human Prefrontal Cortex Agilent (Jun11) mlratio',val:'HBTRC-MLPFC_0611'},
{txt:'HBTRC-MLC Human Prefrontal Cortex Agilent Normal (Jun11) mlratio',val:'HBTRC-MLPFC_N_0611'},
{txt:'HBTRC-MLC Human Cerebellum Agilent AD (Jun11) mlratio',val:'HBTRC-MLC_AD_0611'},
{txt:'HBTRC-MLC Human Visual Cortex Agilent (Jun11) mlratio',val:'HBTRC-MLVC_0611'},
{txt:'HBTRC-MLC Human Prefrontal Cortex Agilent AD (Jun11) mlratio',val:'HBTRC-MLPFC_AD_0611'},
{txt:'HBTRC-MLC Human Visual Cortex Agilent Normal (Jun11) mlratio',val:'HBTRC-MLVC_N_0611'},
{txt:'HBTRC-MLC Human Cerebellum Agilent HD (Jun11) mlratio',val:'HBTRC-MLC_HD_0611'},
{txt:'HBTRC-MLC Human Visual Cortex Agilent AD (Jun11) mlratio',val:'HBTRC-MLVC_AD_0611'},
{txt:'HBTRC-MLC Human Prefrontal Cortex Agilent HD (Jun11) mlratio',val:'HBTRC-MLPFC_HD_0611'},
{txt:'HBTRC-MLC Human Visual Cortex Agilent HD (Jun11) mlratio',val:'HBTRC-MLVC_HD_0611'},
{txt:'INIA Amygdala Cohort Affy MoGene 1.0 ST (Mar11) RMA',val:'INIA_AmgCoh_0311'},
{txt:'INIA Amygdala Affy MoGene 1.0 ST (Nov10) RMA',val:'INIA_Amg_BLA_RMA_1110'},
{txt:'INIA Amygdala Affy MoGene 1.0 ST (Nov10) RMA Male',val:'INIA_Amg_BLA_RMA_M_1110'},
{txt:'INIA Amygdala Affy MoGene 1.0 ST (Nov10) RMA Female',val:'INIA_Amg_BLA_RMA_F_1110'},
{txt:'GSE9588 Human Liver Normal (Mar11) Both Sexes',val:'HLC_0311'},
{txt:'GSE9588 Human Liver Normal (Mar11) Males',val:'HLCM_0311'},
{txt:'HZI Thelp M430v2 (Feb11) RMA',val:'RTHC_0211_R'},
{txt:'GSE5281 Human Brain Normal Full Liang (Jul09) RMA',val:'GSE5281_F_RMA_N_0709'},
{txt:'GSE5281 Human Brain Alzheimer Full Liang (Jul09) RMA',val:'GSE5281_F_RMA_Alzh_0709'},
{txt:'OHSU HS-CC Striatum ILM6v1 (Feb11) RankInv',val:'OHSU_HS-CC_ILMStr_0211'},
{txt:'HEI Retina Females Illumina V6.2 (Dec10) RankInv **',val:'ILM_Retina_BXD_F_RankInv1210'},
{txt:'HEI Retina Males Illumina V6.2 (Dec10) RankInv **',val:'ILM_Retina_BXD_M_RankInv1210'},
{txt:'HEI Retina F-M Illumina V6.2 (Dec10) RankInv **',val:'ILM_Retina_BXD_FM_RankInv1210'},
{txt:'G2NEI Retina Illumina V6.2 (April 2010) RankInv **',val:'G2NEI_ILM_Retina_BXD_RI0410'},
{txt:'NCSU Drosophila Whole Body (Jan11) RMA',val:'NCSU_DrosWB_LC_RMA_0111'},
{txt:'UNC Agilent G4121A Liver LOWESS Stanford (Jan06) Females',val:'LV_G_0106_F'},
{txt:'UNC Agilent G4121A Liver LOWESS Stanford (Jan06) Males',val:'LV_G_0106_M'},
{txt:'UNC Agilent G4121A Liver LOWESS Stanford (Jan06) Both Sexes',val:'LV_G_0106_B'},
{txt:'GenEx BXD Sal Liver Affy M430 2.0 (Feb11) RMA Females **',val:'GenEx_BXD_liverSal_RMA_F_0211'},
{txt:'GenEx BXD Sal Liver Affy M430 2.0 (Feb11) RMA Males **',val:'GenEx_BXD_liverSal_RMA_M_0211'},
{txt:'GenEx BXD Sal Liver Affy M430 2.0 (Feb11) RMA Both Sexes **',val:'GenEx_BXD_liverSal_RMA_0211'},
{txt:'GenEx BXD EtOH Liver Affy M430 2.0 (Feb11) RMA Females **',val:'GenEx_BXD_liverEt_RMA_F_0211'},
{txt:'GenEx BXD EtOH Liver Affy M430 2.0 (Feb11) RMA Males **',val:'GenEx_BXD_liverEt_RMA_M_0211'},
{txt:'GenEx BXD EtOH Liver Affy M430 2.0 (Feb11) RMA Both Sexes **',val:'GenEx_BXD_liverEt_RMA_0211'},
{txt:'SUH BXD Liver Affy Mouse Gene 1.0 ST (Jun11) RMA **',val:'SUH_Liv_RMA_0611'},
{txt:'HQF BXD Striatum ILM6.1 (Dec10v2) RankInv',val:'UTHSC_Striatum_RankInv_1210'},
{txt:'HQF BXD Striatum ILM6.1 (Dec10) RankInv',val:'UTHSC_Str_RankInv_1210'},
{txt:'HQF BXD Neocortex ILM6v1.1 (Dec10v2) RankInv',val:'HQFNeoc_1210v2_RankInv'},
{txt:'UTHSC Affy MoGene 1.0 ST Spleen (Dec10) RMA',val:'UTHSC_SPL_RMA_1210'},
{txt:'HQF BXD Neocortex ILM6v1.1 (Dec10) RankInv',val:'HQFNeoc_1210_RankInv'},
{txt:'INIA Hypothalamus Affy MoGene 1.0 ST (Nov10)',val:'INIA_Hyp_RMA_1110'},
{txt:'INIA Hypothalamus Affy MoGene 1.0 ST (Nov10) Male',val:'INIA_Hyp_M_RMA_1110'},
{txt:'INIA Hypothalamus Affy MoGene 1.0 ST (Nov10) Female',val:'INIA_Hyp_F_RMA_1110'},
{txt:'UMUTAffy Hippocampus Exon (Feb09) RMA MDP',val:'UMUTAffyExon_0209_RMA_MDP'},
{txt:'UTHSC Affy MoGene 1.0 ST Spleen (Oct10) RMA',val:'UTHSC_SPL_RMA_1010'},
{txt:'Hippocampus Consortium M430v2 (Jun06) RMA MDP',val:'HC_M2_0606_MDP'},
{txt:'OX UK HS ILM6v1.1 Lung (May 2010) RankInv',val:'OXUKHS_ILMLung_RI0510'},
{txt:'OX UK HS ILM6v1.1 Hippocampus (May 2010) RankInv',val:'OXUKHS_ILMHipp_RI0510'},
{txt:'OX UK HS ILM6v1.1 Liver (May 2010) RankInv',val:'OXUKHS_ILMLiver_RI0510'},
{txt:'INIA Macaca fasicularis Prefrontal Cortex (Jan10) RMA **',val:'INIA_MacFas_Pf_RMA_0110'},
{txt:'INIA Macaca fasicularis Brain (Jan10) RMA **',val:'INIA_MacFas_brain_RMA_0110'},
{txt:'UAB Whole body D.m. mRNA control (Oct09) RMA',val:'UAB_DrosWB_LC_RMA_1009'},
{txt:'UAB Whole body D.m. mRNA lead (pbAc) (Oct09) RMA',val:'UAB_DrosWB_LE_RMA_1009'},
{txt:'UMCG Stem Cells ILM6v1.1 (Apr09) original',val:'UMCG_0907_HemaStem_ori'},
{txt:'UMCG Stem Cells ILM6v1.1 (Apr09) transformed',val:'UMCG_0907_HemaStem'},
{txt:'UMCG Progenitor Cells ILM6v1.1 (Apr09) original',val:'UMCG_0907_Pro_ori'},
{txt:'UMCG Progenitor Cells ILM6v1.1 (Apr09) transformed',val:'UMCG_0907_Pro'},
{txt:'UMCG Erythroid Cells ILM6v1.1 (Apr09) original',val:'UMCG_0907_Eryth_ori'},
{txt:'UMCG Erythroid Cells ILM6v1.1 (Apr09) transformed',val:'UMCG_0907_Eryth'},
{txt:'UMCG Myeloid Cells ILM6v1.1 (Apr09) original',val:'UMCG_0907_Myeloid_ori'},
{txt:'UMCG Myeloid Cells ILM6v1.1 (Apr09) transformed',val:'UMCG_0907_Myeloid'},
{txt:'UTHSC CEPH B-cells Illumina (Sep09) RankInv',val:'UT_CEPH_RankInv0909'},
{txt:'Mouse kidney M430v2 Female (Aug06) RMA',val:'MA_M2F_0706_R'},
{txt:'Mouse kidney M430v2 Male (Aug06) RMA',val:'MA_M2M_0706_R'},
{txt:'Barley1 Leaf INOC TTKS (Aug09) MAS5',val:'B1LI0809M5'},
{txt:'Barley1 Leaf INOC TTKS (Aug09) RMA',val:'B1LI0809R'},
{txt:'Barley1 Leaf MOCK TTKS (Aug09) MAS5',val:'B1MI0809M5'},
{txt:'Barley1 Leaf MOCK TTKS (Aug09) RMA',val:'B1MI0809R'},
{txt:'GSE15222 Human Brain Myers (Apr09) RankInv',val:'GSE15222_F_RI_0409'},
{txt:'GSE5281 Human Brain Full Liang (Jul09) RMA',val:'GSE5281_F_RMA0709'},
{txt:'GSE5281 Human Brain Best 102 Liang (Jul09) RMA',val:'GSE5281_RMA0709'},
{txt:'UT Hippocampus Affy RaEx 1.0 Exon (Jul09) RMA',val:'UT_HippRatEx_RMA_0709'},
{txt:'VCU BXD VTA Et vs Sal M430 2.0 (Jun09) Sscore **',val:'VCUEtvsSal_0609_R'},
{txt:'VCU BXD VTA Sal M430 2.0 (Jun09) RMA **',val:'VCUSal_0609_R'},
{txt:'VCU BXD VTA EtOH M430 2.0 (Jun09) RMA **',val:'VCUEtOH_0609_R'},
{txt:'IoP Affy MOE 430v2 Spleen (May09) RMA',val:'IoP_SPL_RMA_0509'},
{txt:'NCI Mammary M430v2 (Apr09) RMA',val:'NCI_Mam_Tum_RMA_0409'},
{txt:'NCI Mammary LMT miRNA v2 (Apr09) RMA',val:'NCI_Agil_Mam_Tum_RMA_0409'},
{txt:'MDC/CAS/UCL Liver 230v2 (Dec08) RMA',val:'HXB_Liver_1208'},
{txt:'MDC/CAS/UCL Heart 230_V2 (Dec08) RMA',val:'HXB_Heart_1208'},
{txt:'MDC/CAS/UCL Adrenal 230A (Dec08) RMA',val:'HXB_Adrenal_1208'},
{txt:'UWA Illumina Spleen (Nov08) RSN **',val:'Illum_BXD_Spl_1108'},
{txt:'UWA Illumina Thymus (Nov08) RSN **',val:'Illum_BXD_Thy_1108'},
{txt:'UWA Illumina PBL (Nov08) RSN **',val:'Illum_BXD_PBL_1108'},
{txt:'Monks CEPH B-cells Agilent (Dec04) Log10Ratio',val:'Human_1008'},
{txt:'UTK Spleen ILM6.1 (Jan10) VST',val:'UTK_BXDSpl_VST_0110'},
{txt:'Eye AXBXA Illumina V6.2(Oct08) RankInv Beta',val:'Eye_AXBXA_1008_RankInv'},
{txt:'Eye M430v2 (Sep08) RMA',val:'Eye_M2_0908_R'},
{txt:'Eye M430v2 Mutant Gpnmb (Sep08) RMA **',val:'Eye_M2_0908_R_NB'},
{txt:'Eye M430v2 WT Gpnmb (Sep08) RMA **',val:'Eye_M2_0908_R_ND'},
{txt:'Eye M430v2 WT Tyrp1 (Sep08) RMA **',val:'Eye_M2_0908_R_WT'},
{txt:'Eye M430v2 WT WT (Sep08) RMA **',val:'Eye_M2_0908_WTWT'},
{txt:'Eye M430v2 Mutant Tyrp1 (Sep08) RMA **',val:'Eye_M2_0908_R_MT'},
{txt:'BXD Glaucoma Affy M430 2.0 Trial (Sep11) RMA **',val:'BXD_GLA_0911'},
{txt:'UCLA BXH and BXD Cartilage v2',val:'UCLA_BXHBXD_CARTILAGE_V2'},
{txt:'UCLA BXD and BXH Cartilage v2',val:'UCLA_BXDBXH_CARTILAGE_V2'},
{txt:'UCLA BXH and BXD Cartilage',val:'UCLA_BXHBXD_CARTILAGE'},
{txt:'UCLA BXD and BXH Cartilage',val:'UCLA_BXDBXH_CARTILAGE'},
{txt:'UCLA BHF2 Liver Male mlratio',val:'UCLA_BHF2_LIVER_MALE'},
{txt:'UCLA BHF2 Brain Female mlratio',val:'UCLA_BHF2_BRAIN_FEMALE'},
{txt:'UCLA BHF2 Brain Male mlratio',val:'UCLA_BHF2_BRAIN_MALE'},
{txt:'UCLA BHF2 Adipose Female mlratio',val:'UCLA_BHF2_ADIPOSE_FEMALE'},
{txt:'UCLA BHF2 Adipose Male mlratio',val:'UCLA_BHF2_ADIPOSE_MALE'},
{txt:'UCLA CTB6B6CTF2 Liver Male mlratio **',val:'UCLA_CTB6B6CTF2_LIVER_MALE'},
{txt:'UCLA CTB6B6CTF2 Adipose Male mlratio **',val:'UCLA_CTB6B6CTF2_ADIPOSE_MALE'},
{txt:'UCLA CTB6B6CTF2 Brain Male mlratio **',val:'UCLA_CTB6B6CTF2_BRAIN_MALE'},
{txt:'UCLA CTB6B6CTF2 Muscle Male mlratio **',val:'UCLA_CTB6B6CTF2_MUSCLE_MALE'},
{txt:'UCLA BHF2 Liver Female mlratio',val:'UCLA_BHF2_LIVER_FEMALE'},
{txt:'UCLA BHHBF2 Muscle Female Only',val:'UCLA_BHHBF2_MUSCLE_FEMALE'},
{txt:'UCLA BHHBF2 Brain Female Only',val:'UCLA_BHHBF2_BRAIN_FEMALE'},
{txt:'UCLA BHHBF2 Brain Male Only',val:'UCLA_BHHBF2_BRAIN_MALE'},
{txt:'UCLA BHHBF2 Adipose Female Only',val:'UCLA_BHHBF2_ADIPOSE_FEMALE'},
{txt:'UCLA BHHBF2 Adipose Male Only',val:'UCLA_BHHBF2_ADIPOSE_MALE'},
{txt:'UCLA BHF2 Muscle Female mlratio **',val:'UCLA_BHF2_MUSCLE_FEMALE'},
{txt:'UCLA BHF2 Muscle Male mlratio **',val:'UCLA_BHF2_MUSCLE_MALE'},
{txt:'UCLA BHHBF2 Liver Female Only',val:'UCLA_BHHBF2_LIVER_FEMALE'},
{txt:'UCLA BHHBF2 Muscle Male Only',val:'UCLA_BHHBF2_MUSCLE_MALE'},
{txt:'UCLA BHHBF2 Liver Male Only',val:'UCLA_BHHBF2_LIVER_MALE'},
{txt:'UCLA BXD Cartilage',val:'UCLA_BXD_CARTILAGE'},
{txt:'UCLA BXH Cartilage',val:'UCLA_BXH_CARTILAGE'},
{txt:'UCLA BHHBF2 Brain (2005) mlratio **',val:'UCLA_BHHBF2_BRAIN_2005'},
{txt:'UCLA BHHBF2 Liver (2005) mlratio **',val:'UCLA_BHHBF2_LIVER_2005'},
{txt:'UCLA BHHBF2 Muscle (2005) mlratio **',val:'UCLA_BHHBF2_MUSCLE_2005'},
{txt:'UCLA BHHBF2 Adipose (2005) mlratio **',val:'UCLA_BHHBF2_ADIPOSE_2005'},
{txt:'UCLA BHF2 Adipose (June05) mlratio',val:'UCLA_BHF2_ADIPOSE_0605'},
{txt:'UCLA BHF2 Brain (June05) mlratio',val:'UCLA_BHF2_BRAIN_0605'},
{txt:'UCLA BHF2 Liver (June05) mlratio',val:'UCLA_BHF2_LIVER_0605'},
{txt:'UCLA BHF2 Muscle (June05) mlratio **',val:'UCLA_BHF2_MUSCLE_0605'},
{txt:'UCLA BDF2 Liver (1999) mlratio',val:'UCLA_BDF2_LIVER_1999'},
{txt:'HZI Lung M430v2 (Apr08) RMA',val:'HZI_0408_R'},
{txt:'HZI Lung M430v2 (Apr08) MAS5',val:'HZI_0408_M'},
{txt:'HQF BXD Neocortex ILM6v1.1 (Feb08) RankInv',val:'HQFNeoc_0208_RankInv'},
{txt:'VCU BXD NA Sal M430 2.0 (Oct07) RMA',val:'VCUSalo_1007_R'},
{txt:'VCU BXD NA EtOH M430 2.0 (Oct07) RMA **',val:'VCUEtOH_1007_R'},
{txt:'VCU BXD NA Et vs Sal M430 2.0 (Oct07) Sscore **',val:'VCUSal_1007_R'},
{txt:'Stuart Spleen M430v2 (Nov07) RMA',val:'STSPL_1107_R'},
{txt:'HQF BXD Striatum ILM6.1 (Nov07) RankInv',val:'UTHSC_1107_RankInv'},
{txt:'Hippocampus Illumina (Aug07) LOESS',val:'Illum_LXS_Hipp_loess0807'},
{txt:'Hippocampus Illumina (Aug07) LOESS_NB',val:'Illum_LXS_Hipp_loess_nb0807'},
{txt:'Hippocampus Illumina (Aug07) QUANT',val:'Illum_LXS_Hipp_quant0807'},
{txt:'Hippocampus Illumina (Aug07) QUANT_NB',val:'Illum_LXS_Hipp_quant_nb0807'},
{txt:'Hippocampus Illumina (Aug07) RSN',val:'Illum_LXS_Hipp_rsn0807'},
{txt:'Hippocampus Illumina (Aug07) RSN_NB',val:'Illum_LXS_Hipp_rsn_nb0807'},
{txt:'VCU BXD PFC EtOH M430 2.0 (Dec06) RMA',val:'VCUEtOH_1206_R'},
{txt:'VCU BXD PFC Sal M430 2.0 (Dec06) RMA',val:'VCUSal_1206_R'},
{txt:'VCU BXD PFC Et vs Sal M430 2.0 (Dec06) Sscore',val:'VCUSal_1006_R'},
{txt:'VCU BXD PFC CIE Air M430 2.0 (Jan11) RMA **',val:'VCU_PF_Air_0111_R'},
{txt:'VCU BXD PFC CIE EtOH M430 2.0 (Jan11) RMA **',val:'VCU_PF_Et_0111_R'},
{txt:'VCU BXD PFC EtOH vs CIE Air M430 2.0 (Jan11) Sscore **',val:'VCU_PF_AvE_0111_Ss'},
{txt:'Hippocampus Illumina (May07) RankInv',val:'Hipp_Illumina_RankInv_0507'},
{txt:'VCU LXS PFC EtOH M430A 2.0 (Aug06) RMA **',val:'VCUEtOH_0806_R'},
{txt:'VCU LXS PFC Sal M430A 2.0 (Aug06) RMA',val:'VCUSal_0806_R'},
{txt:'VCU LXS PFC Et vs Sal M430A 2.0 (Aug06) Sscore **',val:'VCUEt_vs_Sal_0806_R'},
{txt:'Barley1 Leaf MAS 5.0 SCRI (Dec06)',val:'B30_K_1206_M'},
{txt:'Barley1 Embryo gcRMA SCRI (Dec06)',val:'B139_K_1206_R'},
{txt:'Barley1 Leaf gcRMAn SCRI (Dec06)',val:'B30_K_1206_Rn'},
{txt:'Barley1 Embryo MAS 5.0 SCRI (Dec06)',val:'B139_K_1206_M'},
{txt:'Barley1 Leaf gcRMA SCRI (Dec06)',val:'B30_K_1206_R'},
{txt:'HZI Treg M430v2 (Feb11) RMA',val:'RTC_1106_R'},
{txt:'UCHSC BXD Whole Brain M430 2.0 (Nov06) RMA',val:'BR_M2_1106_R'},
{txt:'UIOWA Eye mRNA RAE230v2 (Sep06) RMA',val:'UIOWA_Eye_RMA_0906'},
{txt:'Mouse kidney M430v2 Sex Balanced (Aug06) RMA',val:'MA_M2_0806_R'},
{txt:'Mouse Kidney M430v2 Sex Balanced (Aug06) PDNN',val:'MA_M2_0806_P'},
{txt:'Mouse Kidney M430v2 (Jul06) PDNN',val:'MA_M2_0706_P'},
{txt:'Mouse Kidney M430v2 (Jul06) RMA',val:'MA_M2_0706_R'},
{txt:'Barley1 Embryo0 gcRMA SCRI (Apr06)',val:'B150_K_0406_R'},
{txt:'INIA Brain mRNA M430 (Jun06) RMA',val:'IBR_M_0606_R'},
{txt:'Hippocampus Consortium M430v2 (Jun06) PDNN',val:'HC_M2_0606_P'},
{txt:'Hippocampus Consortium M430v2 (Jun06) MAS5',val:'HC_M2_0606_M'},
{txt:'Hippocampus Consortium M430v2 (Jun06) RMA',val:'HC_M2_0606_R'},
{txt:'INIA Brain mRNA M430 (Jan06) PDNN',val:'IBR_M_0106_P'},
{txt:'INIA Brain mRNA M430 (Jan06) RMA',val:'IBR_M_0106_R'},
{txt:'Hippocampus Consortium M430v2 CXB (Dec05) RMA',val:'HC_M2CB_1205_R'},
{txt:'Hippocampus Consortium M430v2 CXB (Dec05) PDNN',val:'HC_M2CB_1205_P'},
{txt:'UTHSC Brain mRNA U74Av2 (Nov05) PDNN',val:'BR_U_1105_P'},
{txt:'UMUTAffy Hippocampus Exon (Feb09) RMA',val:'UMUTAffyExon_0209_RMA'},
{txt:'UTHSC Hippocampus Illumina v6.1 NON (Sep09) RankInv',val:'UT_ILM_BXD_hipp_NON_0909'},
{txt:'UTHSC Hippocampus Illumina v6.1 NOS (Sep09) RankInv',val:'UT_ILM_BXD_hipp_NOS_0909'},
{txt:'UTHSC Hippocampus Illumina v6.1 NOE (Sep09) RankInv',val:'UT_ILM_BXD_hipp_NOE_0909'},
{txt:'UTHSC Hippocampus Illumina v6.1 RSS (Sep09) RankInv',val:'UT_ILM_BXD_hipp_RSS_0909'},
{txt:'UTHSC Hippocampus Illumina v6.1 RSE (Sep09) RankInv',val:'UT_ILM_BXD_hipp_RSE_0909'},
{txt:'OHSU/VA B6D2F2 Striatum M430v2 (Sep05) MAS5',val:'SA_M2_0905_M'},
{txt:'OHSU/VA B6D2F2 Striatum M430v2 (Sep05) PDNN',val:'SA_M2_0905_P'},
{txt:'OHSU/VA B6D2F2 Striatum M430v2 (Sep05) RMA',val:'SA_M2_0905_R'},
{txt:'UTHSC Brain mRNA U74Av2 (Aug05) RMA',val:'BR_U_0805_R'},
{txt:'UTHSC Brain mRNA U74Av2 (Aug05) PDNN',val:'BR_U_0805_P'},
{txt:'UTHSC Brain mRNA U74Av2 (Aug05) MAS5',val:'BR_U_0805_M'},
{txt:'MDC/CAS/ICL Peritoneal Fat 230A (Aug05) MAS5',val:'FT_2A_0805_M'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430 (Aug05) RMA',val:'BRF2_M_0805_R'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430 (Aug05) PDNN',val:'BRF2_M_0805_P'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430 (Aug05) MAS5',val:'BRF2_M_0805_M'},
{txt:'MDC/CAS/ICL Peritoneal Fat 230A (Jun05) RMA 2z+8',val:'FT_2A_0605_Rz'},
{txt:'HBP Rosen Striatum M430V2 (Apr05) MAS5 Clean',val:'SA_M2_0405_MC'},
{txt:'GE-NIAAA Cerebellum mRNA M430v2 (May05) RMA',val:'GCB_M2_0505_R'},
{txt:'GE-NIAAA Cerebellum mRNA M430v2 (May05) MAS5',val:'GCB_M2_0505_M'},
{txt:'GE-NIAAA Cerebellum mRNA M430v2 (May05) PDNN',val:'GCB_M2_0505_P'},
{txt:'MDC/CAS/ICL Kidney 230A (Apr05) MAS5',val:'KI_2A_0405_M'},
{txt:'HBP Rosen Striatum M430V2 (Apr05) RMA Clean',val:'SA_M2_0405_RC'},
{txt:'HBP Rosen Striatum M430V2 (Apr05) PDNN Clean',val:'SA_M2_0405_PC'},
{txt:'HBP Rosen Striatum M430V2 (Apr05) SScore',val:'SA_M2_0405_SS'},
{txt:'HBP Rosen Striatum M430V2 (Apr05) RMA Orig',val:'SA_M2_0405_RR'},
{txt:'MDC/CAS/ICL Kidney 230A (Apr05) RMA 2z+8',val:'KI_2A_0405_Rz'},
{txt:'MDC/CAS/ICL Kidney 230A (Apr05) RMA',val:'KI_2A_0405_R'},
{txt:'SJUT Cerebellum mRNA M430 (Mar05) RMA',val:'CB_M_0305_R'},
{txt:'SJUT Cerebellum mRNA M430 (Mar05) MAS5',val:'CB_M_0305_M'},
{txt:'SJUT Cerebellum mRNA M430 (Mar05) PDNN',val:'CB_M_0305_P'},
{txt:'HQF Striatum Exon (Feb09) RMA',val:'Striatum_Exon_0209'},
{txt:'BIDMC/UTHSC Dev Striatum P3 ILMv6.2 (Nov10) RankInv **',val:'DevStriatum_ILM6.2P3RInv_1110'},
{txt:'BIDMC/UTHSC Dev Neocortex P3 ILMv6.2 (Nov10) RankInv',val:'DevNeocortex_ILM6.2P3RInv_1110'},
{txt:'BIDMC/UTHSC Dev Neocortex P14 ILMv6.2 (Nov10) RankInv',val:'DevNeocortex_ILM6.2P14RInv_1110'},
{txt:'BIDMC/UTHSC Dev Striatum P14 ILMv6.2 (Nov10) RankInv **',val:'DevStriatum_ILM6.2P14RInv_1110'},
{txt:'SJUT Cerebellum mRNA M430 (Oct04) MAS5',val:'CB_M_1004_M'},
{txt:'SJUT Cerebellum mRNA M430 (Oct04) RMA',val:'CB_M_1004_R'},
{txt:'SJUT Cerebellum mRNA M430 (Oct04) PDNN',val:'CB_M_1004_P'},
{txt:'(B6 x BTBR)F2-ob/ob Liver mRNA M430 (Jul04) MAS5',val:'LVF2_M_0704_M'},
{txt:'(B6 x BTBR)F2-ob/ob Liver mRNA M430 (Jul04) RMA',val:'LVF2_M_0704_R'},
{txt:'NCI Mammary mRNA M430 (July04) RMA',val:'MA_M_0704_R'},
{txt:'NCI Mammary mRNA M430 (July04) MAS5',val:'MA_M_0704_M'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430A (Mar04) PDNN',val:'BRF2_M_0304_P'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430A (Mar04) RMA',val:'BRF2_M_0304_R'},
{txt:'GNF Stem Cells U74Av2 (Mar04) RMA',val:'HC_U_0304_R'},
{txt:'OHSU/VA B6D2F2 Brain mRNA M430A (Mar04) MAS5',val:'BRF2_M_0304_M'},
{txt:'INIA Brain mRNA M430 (Feb04) PDNN',val:'CB_M_0204_P'},
{txt:'SJUT Cerebellum mRNA M430 (Oct03) MAS5',val:'CB_M_1003_M'},
{txt:'Hippocampus Illumina NON (Oct08) RankInv beta',val:'Illum_LXS_Hipp_NON_1008'},
{txt:'Hippocampus Illumina RSE (Oct08) RankInv beta',val:'Illum_LXS_Hipp_RSE_1008'},
{txt:'GSE9588 Human Liver Normal (Mar11) Females',val:'HLCF_0311'},
{txt:'Hippocampus Illumina NOE (Oct08) RankInv beta',val:'Illum_LXS_Hipp_NOE_1008'},
{txt:'Hippocampus Illumina NOS (Oct08) RankInv beta',val:'Illum_LXS_Hipp_NOS_1008'},
{txt:'Hippocampus Illumina RSS (Oct08) RankInv beta',val:'Illum_LXS_Hipp_RSS_1008'},
{txt:'CANDLE Published Phenotypes',val:'CANDLEPublish'},
{txt:'HLC Published Phenotypes',val:'HLCPublish'},
{txt:'AKXD Genotypes',val:'AKXDGeno'},
{txt:'AXBXA Published Phenotypes',val:'AXBXAPublish'},
{txt:'AXBXA Genotypes',val:'AXBXAGeno'},
{txt:'B6BTBRF2 Published Phenotypes',val:'B6BTBRF2Publish'},
{txt:'B6BTBRF2 Genotypes',val:'B6BTBRF2Geno'},
{txt:'B6D2F2 Genotypes',val:'B6D2F2Geno'},
{txt:'BDF2-1999 Genotypes',val:'BDF2-1999Geno'},
{txt:'BDF2-2005 Genotypes',val:'BDF2-2005Geno'},
{txt:'BHF2 Genotypes',val:'BHF2Geno'},
{txt:'BHHBF2 Genotypes',val:'BHHBF2Geno'},
{txt:'BXD Published Phenotypes',val:'BXDPublish'},
{txt:'BXD Genotypes',val:'BXDGeno'},
{txt:'BXH Published Phenotypes',val:'BXHPublish'},
{txt:'BXH Genotypes',val:'BXHGeno'},
{txt:'CTB6F2 Published Phenotypes',val:'CTB6F2Publish'},
{txt:'CTB6F2 Genotypes',val:'CTB6F2Geno'},
{txt:'CXB Published Phenotypes',val:'CXBPublish'},
{txt:'CXB Genotypes',val:'CXBGeno'},
{txt:'LXS Published Phenotypes',val:'LXSPublish'},
{txt:'LXS Genotypes',val:'LXSGeno'},
{txt:'Mouse Phenome Database',val:'MDPPublish'},
{txt:'MDP Genotypes',val:'MDPGeno'},
{txt:'NZBXFVB-N2 Published Phenotypes',val:'NZBXFVB-N2Publish'},
{txt:'HXBBXH Published Phenotypes',val:'HXBBXHPublish'},
{txt:'HXBBXH Genotypes',val:'HXBBXHGeno'},
{txt:'BayXSha Published Phenotypes',val:'BayXShaPublish'},
{txt:'BayXSha Genotypes',val:'BayXShaGeno'},
{txt:'ColXBur Published Phenotypes',val:'ColXBurPublish'},
{txt:'ColXBur Genotypes',val:'ColXBurGeno'},
{txt:'ColXCvi Published Phenotypes',val:'ColXCviPublish'},
{txt:'ColXCvi Genotypes',val:'ColXCviGeno'},
{txt:'SXM Published Phenotypes',val:'SXMPublish'},
{txt:'SXM Genotypes',val:'SXMGeno'},
{txt:'J12XJ58F2 Published Phenotypes',val:'J12XJ58F2Publish'},
{txt:'LXP Published Phenotypes',val:'LXPPublish'},
{txt:'All Phenotypes',val:'_allPublish'}];

var lArr = [
 null,
[1,1,4,79],
[1,1,4,80],
[1,1,4,131],
[1,1,4,132],
[1,2,4,1],
[1,2,4,2],
[1,2,4,130],
[1,14,59,292],
[1,14,34,32],
[1,15,26,123],
[1,15,26,146],
[1,21,8,60],
[1,21,8,61],
[1,21,8,64],
[1,21,8,68],
[1,21,42,62],
[1,21,42,63],
[1,21,42,66],
[1,21,42,70],
[1,21,46,65],
[1,21,46,67],
[1,21,46,69],
[1,21,46,71],
[1,22,59,293],
[1,22,24,76],
[1,22,24,77],
[1,22,24,288],
[1,25,3,54],
[1,25,6,51],
[1,25,7,53],
[1,25,9,49],
[1,25,10,52],
[1,25,11,50],
[1,25,14,48],
[1,25,17,33],
[1,25,19,57],
[1,25,21,58],
[1,25,28,37],
[1,25,29,34],
[1,25,30,46],
[1,25,36,38],
[1,25,37,43],
[1,25,38,44],
[1,25,40,56],
[1,25,41,47],
[1,25,43,55],
[1,25,44,59],
[1,25,45,45],
[1,25,46,39],
[1,25,49,42],
[1,25,52,41],
[1,25,54,40],
[1,25,55,36],
[1,25,57,35],
[2,30,3,13],
[2,30,4,112],
[2,30,17,5],
[2,30,35,3],
[2,30,42,111],
[3,3,60,294],
[3,3,27,139],
[3,3,27,278],
[3,3,27,279],
[3,4,59,295],
[3,4,60,296],
[3,4,13,148],
[3,5,59,297],
[3,5,60,298],
[3,5,24,276],
[3,5,24,277],
[3,6,60,299],
[3,6,4,250],
[3,6,4,251],
[3,6,4,252],
[3,6,4,280],
[3,6,4,281],
[3,6,4,283],
[3,8,60,300],
[3,8,24,190],
[3,9,60,301],
[3,9,49,243],
[3,9,49,244],
[3,9,49,245],
[3,10,60,302],
[3,10,1,163],
[3,10,1,164],
[3,10,1,186],
[3,10,4,161],
[3,10,4,162],
[3,10,4,187],
[3,10,24,160],
[3,10,24,169],
[3,10,24,188],
[3,10,32,175],
[3,10,32,176],
[3,10,32,189],
[3,11,60,303],
[3,11,1,173],
[3,11,1,174],
[3,11,1,185],
[3,11,4,171],
[3,11,4,172],
[3,11,4,182],
[3,11,24,177],
[3,11,24,179],
[3,11,24,183],
[3,11,32,170],
[3,11,32,178],
[3,11,32,184],
[3,12,59,304],
[3,12,60,305],
[3,12,3,72],
[3,12,3,73],
[3,12,3,74],
[3,12,3,75],
[3,12,4,221],
[3,12,4,228],
[3,12,4,232],
[3,12,4,233],
[3,12,4,236],
[3,12,4,246],
[3,12,4,247],
[3,12,4,248],
[3,12,4,284],
[3,12,5,157],
[3,12,5,159],
[3,12,5,180],
[3,12,8,255],
[3,12,8,256],
[3,12,8,257],
[3,12,8,265],
[3,12,8,266],
[3,12,8,267],
[3,12,8,273],
[3,12,8,274],
[3,12,8,275],
[3,12,8,285],
[3,12,13,149],
[3,12,13,150],
[3,12,13,151],
[3,12,13,152],
[3,12,13,153],
[3,12,13,154],
[3,12,13,155],
[3,12,16,115],
[3,12,16,116],
[3,12,16,117],
[3,12,16,118],
[3,12,16,119],
[3,12,16,120],
[3,12,16,121],
[3,12,16,122],
[3,12,16,282],
[3,12,17,229],
[3,12,17,230],
[3,12,17,231],
[3,12,17,237],
[3,12,17,238],
[3,12,17,239],
[3,12,17,240],
[3,12,17,241],
[3,12,17,242],
[3,12,18,102],
[3,12,18,103],
[3,12,18,104],
[3,12,20,124],
[3,12,20,125],
[3,12,20,223],
[3,12,20,224],
[3,12,20,225],
[3,12,20,226],
[3,12,23,145],
[3,12,24,15],
[3,12,24,87],
[3,12,24,88],
[3,12,24,89],
[3,12,24,90],
[3,12,24,91],
[3,12,24,92],
[3,12,24,93],
[3,12,24,94],
[3,12,24,95],
[3,12,24,96],
[3,12,25,191],
[3,12,25,192],
[3,12,31,14],
[3,12,32,16],
[3,12,32,17],
[3,12,32,18],
[3,12,33,21],
[3,12,33,22],
[3,12,33,99],
[3,12,33,101],
[3,12,33,193],
[3,12,33,270],
[3,12,33,271],
[3,12,35,194],
[3,12,35,195],
[3,12,35,196],
[3,12,42,205],
[3,12,42,206],
[3,12,42,207],
[3,12,42,208],
[3,12,42,209],
[3,12,42,210],
[3,12,47,23],
[3,12,47,24],
[3,12,47,25],
[3,12,47,26],
[3,12,47,27],
[3,12,47,28],
[3,12,47,82],
[3,12,47,83],
[3,12,47,84],
[3,12,47,85],
[3,12,48,100],
[3,12,48,106],
[3,12,48,137],
[3,12,48,143],
[3,12,48,147],
[3,12,49,19],
[3,12,49,20],
[3,12,49,97],
[3,12,49,98],
[3,12,49,198],
[3,12,49,254],
[3,12,49,259],
[3,12,49,260],
[3,12,49,261],
[3,12,49,262],
[3,12,49,268],
[3,12,49,269],
[3,12,49,272],
[3,12,50,78],
[3,12,51,220],
[3,12,53,144],
[3,12,56,134],
[3,12,56,135],
[3,12,56,136],
[3,13,59,306],
[3,13,60,307],
[3,13,5,156],
[3,13,5,158],
[3,13,5,181],
[3,18,59,308],
[3,18,60,309],
[3,18,1,8],
[3,18,1,9],
[3,18,1,166],
[3,18,4,4],
[3,18,4,10],
[3,18,4,167],
[3,18,24,6],
[3,18,24,12],
[3,18,24,165],
[3,18,32,7],
[3,18,32,11],
[3,18,32,168],
[3,19,59,310],
[3,19,60,311],
[3,19,17,234],
[3,19,17,235],
[3,19,48,197],
[3,23,17,109],
[3,23,24,110],
[3,23,25,108],
[3,24,49,81],
[3,29,59,312],
[3,29,60,313],
[3,29,17,199],
[3,29,17,200],
[3,29,17,201],
[3,29,17,202],
[3,29,17,203],
[3,29,17,204],
[3,29,17,211],
[3,29,17,286],
[3,29,17,287],
[3,29,17,289],
[3,29,17,290],
[3,29,17,291],
[3,29,42,212],
[3,29,42,213],
[3,29,42,214],
[3,31,59,314],
[3,31,60,315],
[3,31,17,105],
[3,31,17,107],
[3,31,24,29],
[3,31,24,30],
[3,31,24,31],
[3,32,59,316],
[3,32,27,138],
[4,26,59,317],
[4,26,60,318],
[4,26,2,142],
[4,26,15,141],
[4,26,17,133],
[4,26,20,258],
[4,26,20,263],
[4,26,20,264],
[4,26,24,140],
[4,26,39,249],
[4,26,39,253],
[4,35,13,222],
[5,20,58,86],
[5,33,58,113],
[5,33,58,114],
[6,7,59,319],
[6,7,60,320],
[6,16,59,321],
[6,16,60,322],
[6,17,59,323],
[6,17,60,324],
[7,34,22,126],
[7,34,22,127],
[7,34,22,128],
[7,34,22,129],
[7,36,59,325],
[7,36,60,326],
[7,36,12,216],
[7,36,12,218],
[7,36,12,227],
[7,36,22,215],
[7,36,22,217],
[7,36,22,219],
[8,27,59,327],
[9,28,59,328],
[10,37,59,329]];



/* 
*  function: based on different browser use, will have different initial actions; 
*  Once the index.html page is loaded, this function will be called
*/
function initialDatasetSelection()
{		
	defaultSpecies =getDefaultValue('species');
	defaultSet =getDefaultValue('cross');
	defaultType =getDefaultValue('tissue');
	defaultDB =getDefaultValue('database');
	
	if (navigator.userAgent.indexOf('MSIE')>=0)
	{
		sOptions = fillOptionsForIE(null,defaultSpecies);
		var menu0 ="<SELECT NAME='species' ID='species' SIZE='1' onChange='fillOptions(\"species\");'>"+sOptions+"</Select>";
		document.getElementById('menu0').innerHTML = menu0;
		
		gOptions = fillOptionsForIE('species',defaultSet);
		var menu1 ="<Select NAME='cross' size=1 id='cross' onchange='fillOptions(\"cross\");'>"+gOptions+"</Select><input type=\"button\" class=\"button\" value=\"Info\" onCLick=\"javascript:crossinfo();\">";
		document.getElementById('menu1').innerHTML =menu1;
		
		tOptions = fillOptionsForIE('cross',defaultType);
		var menu2 ="<Select NAME='tissue' size=1 id='tissue' onchange='fillOptions(\"tissue\");'>"+tOptions+"</Select>";
		document.getElementById('menu2').innerHTML =menu2;
		
		dOptions = fillOptionsForIE('tissue',defaultDB);
		var menu3 ="<Select NAME='database' size=1 id='database'>"+dOptions+"</Select><input type=\"button\" class=\"button\" value=\"Info\" onCLick=\"javascript:databaseinfo();\">";
		document.getElementById('menu3').innerHTML =menu3;
		
	}else{
		fillOptions(null);
    }
	searchtip();
}

/* 
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*  defaultValue (default Value of species, cross,tissue or database)
*  function: special for IE browser,setting options value for select menu dynamically based on linkage array(lArr), 
*  output: options string
*/
function fillOptionsForIE(selectObjId,defaultValue)
{	
	var options='';	
	if(selectObjId==null)
	{	
		var len = sArr.length;
		for (var i=1; i < len; i++) { 
		    // setting Species' option			
			if( sArr[i].val==defaultValue){
				options =options+"<option selected=\"selected\" value='"+sArr[i].val+"'>"+sArr[i].txt+"</option>";
			}else{
				options =options+"<option value='"+sArr[i].val+"'>"+sArr[i].txt+"</option>";
			}
		}	
	}else if(selectObjId=='species')
	{
		var speciesObj = document.getElementById('species');
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get group(cross) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&!Contains(arr,lArr[i][1]))
			{
				arr[idx++]=lArr[i][1];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("cross");
		for (var i=0; i < len; i++) {
			// setting Group's option
			if( gArr[arr[i]].val==defaultValue){
				options =options+"<option selected=\"selected\" value='"+gArr[arr[i]].val+"'>"+gArr[arr[i]].txt+"</option>";
			}else{
				options =options+"<option value='"+gArr[arr[i]].val+"'>"+gArr[arr[i]].txt+"</option>";
			}
			
		}
	}else if(selectObjId=='cross')
	{
		var speciesObj = document.getElementById('species');
		var groupObj = document.getElementById('cross');
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get type(tissue) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&!Contains(arr,lArr[i][2]))
			{
				arr[idx++]=lArr[i][2];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("tissue");
		for (var i=0; i < len; i++) {
			// setting Type's option
			if( tArr[arr[i]].val==defaultValue){
				options =options+"<option selected=\"selected\" value='"+tArr[arr[i]].val+"'>"+tArr[arr[i]].txt+"</option>";
			}else{
				options =options+"<option value='"+tArr[arr[i]].val+"'>"+tArr[arr[i]].txt+"</option>";
			}
		}

	}else if(selectObjId=='tissue')
	{
		var speciesObj = document.getElementById('species');
		var groupObj = document.getElementById('cross');
		var typeObj = document.getElementById('tissue');

		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get dataset(database) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&lArr[i][2]==(getIndexByValue('tissue',typeObj.value)).toString()&&!Contains(arr,lArr[i][3]))
			{
				arr[idx++]=lArr[i][3];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("database");
		for (var i=0; i < len; i++) {
			// setting Database's option			
			if( dArr[arr[i]].val==defaultValue){
				options =options+"<option SELECTED value='"+dArr[arr[i]].val+"'>"+dArr[arr[i]].txt+"</option>";
			}else{
				options =options+"<option value='"+dArr[arr[i]].val+"'>"+dArr[arr[i]].txt+"</option>";
			}
		}
	}	
	return options;
}
/* 
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*  function: setting options value for select menu dynamically based on linkage array(lArr)
*  output: null
*/
function fillOptions(selectObjId)
{	
	if(selectObjId==null)
	{

		var speciesObj = document.getElementById('species');	
		var len = sArr.length;
		for (var i=1; i < len; i++) { 
		    // setting Species' option
			speciesObj.options[i-1] = new Option(sArr[i].txt, sArr[i].val);
		}
		updateChocie('species');
	
	}else if(selectObjId=='species')
	{
		var speciesObj = document.getElementById('species');
		var groupObj = document.getElementById('cross');
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get group(cross) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&!Contains(arr,lArr[i][1]))
			{
				arr[idx++]=lArr[i][1];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("cross");
		for (var i=0; i < len; i++) {
			// setting Group's option
			groupObj.options[idx++] = new Option(gArr[arr[i]].txt, gArr[arr[i]].val); 
		}
		updateChocie('cross');

	}else if(selectObjId=='cross')
	{
		var speciesObj = document.getElementById('species');
		var groupObj = document.getElementById('cross');
		var typeObj = document.getElementById('tissue');
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get type(tissue) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&!Contains(arr,lArr[i][2]))
			{
				arr[idx++]=lArr[i][2];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("tissue");
		for (var i=0; i < len; i++) {
			// setting Type's option
			typeObj.options[idx++] = new Option(tArr[arr[i]].txt, tArr[arr[i]].val); 
		}
		updateChocie('tissue');

	}else if(selectObjId=='tissue')
	{
		var speciesObj = document.getElementById('species');
		var groupObj = document.getElementById('cross');
		var typeObj = document.getElementById('tissue');
		var databaseObj = document.getElementById('database');

		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get dataset(database) info from lArr
			if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&lArr[i][2]==(getIndexByValue('tissue',typeObj.value)).toString()&&!Contains(arr,lArr[i][3]))
			{
				arr[idx++]=lArr[i][3];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("database");
		for (var i=0; i < len; i++) {
			// setting Database's option
			databaseObj.options[idx++] = new Option(dArr[arr[i]].txt, dArr[arr[i]].val); 
		}
		updateChocie('database');
	}	
}

/* 
*  input: arr (targeted array); obj (targeted value)
*  function: check whether targeted array contains targeted value or not
*  output: return true, if array contains targeted value, otherwise return false
*/
function Contains(arr,obj) { 
	var i = arr.length; 
	while (i--) { 
		if (arr[i] == obj) { 
			return true; 
		}
	} 
	return false; 
} 

/* 
* input: selectObj (designated select menu, such as species, cross, etc... )
* function: clear designated select menu's option
* output: null
*/
function removeOptions(selectObj) {     
	if (typeof selectObj != 'object'){         
		selectObj = document.getElementById(selectObj);
	}        
	var len = selectObj.options.length;      
	for (var i=0; i < len; i++)     {         
		// clear current selection       
		selectObj.options[0] = null;    
	} 
} 

/* 
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*         Value: target value
*  function: retrieve Index info of target value in designated array
*  output: index info
*/
function getIndexByValue(selectObjId,val)
{
	if(selectObjId=='species')
	{
		for(var i=1;i<sArr.length;i++){
			if(sArr[i].val==val)
				return i;				
		}
	}else if(selectObjId=='cross')
	{
		for(var i=1;i<gArr.length;i++)
			if(gArr[i].val==val)
				return i;
	}else if(selectObjId=='tissue')
	{
		for(var i=1;i<tArr.length;i++)
			if(tArr[i].val==val)
				return i;
	}
	else return;
}

/* 
*  input: objId (designated select menu, such as species, cross, etc... )
*  		  val(targeted value)
*  function: setting option's selected status for designated select menu based on target value, also update the following select menu in the main search page 
*  output: return true if selected status has been set, otherwise return false.
*/
function setChoice(objId,val)
{
	var Obj = document.getElementById(objId);
	var idx=-1;

	for(i=0;i<Obj.options.length;i++){
		if(Obj.options[i].value==val){
			idx=i;
			break;
		}
	}
	
	if(idx>=0){
		//setting option's selected status 
		Obj.options[idx].selected=true;
		//update the following select menu 
		fillOptions(objId);
	}else{
		Obj.options[0].selected=true;
		fillOptions(objId);
	}
}

// setting option's selected status based on default setting or cookie setting for Species, Group, Type and Database select menu in the main search page http://www.genenetwork.org/
function updateChocie(selectObjId){

	if (selectObjId =='species')
	{
		defaultSpecies= getDefaultValue('species'); 
		//setting option's selected status
		setChoice('species',defaultSpecies);
	}else if (selectObjId =='cross')
	{	
		defaultSet= getDefaultValue('cross'); 
		//setting option's selected status
		setChoice('cross',defaultSet);
	}else if (selectObjId =='tissue')
	{
		defaultType= getDefaultValue('tissue'); 
		//setting option's selected status
		setChoice('tissue',defaultType);
	}else if (selectObjId =='database')
	{
		defaultDB= getDefaultValue('database'); 
		//setting option's selected status
		setChoice('database',defaultDB);
	}
}

//get default value;if cookie exists, then use cookie value, otherwise use default value
function getDefaultValue(selectObjId){	
	//define default value
	var defaultSpecies = 'mouse'
	var defaultSet = 'BXD'
	var defaultType = 'Hippocampus'
	var defaultDB = 'HC_M2_0606_P'

	if (selectObjId =='species')
	{
		//if cookie exists, then use cookie value, otherwise use default value
		var cookieSpecies = getCookie('defaultSpecies');
		if(cookieSpecies)
		{
			defaultSpecies= cookieSpecies; 
		}
		return defaultSpecies;
	}else if (selectObjId =='cross'){
		var cookieSet = getCookie('defaultSet');
		if(cookieSet){
			defaultSet= cookieSet; 
		} 
		return defaultSet;
	}else if (selectObjId =='tissue'){
		var cookieType = getCookie('defaultType');
		if(cookieType){
			defaultType= cookieType;
		} 
		return defaultType;
	}else if (selectObjId =='database')
	{
		var cookieDB = getCookie('defaultDB');
		if(cookieDB){
			defaultDB= cookieDB;
		}
		return defaultDB;
	}

}

//setting default value into cookies for the dropdown menus: Species,Group, Type, and Database 
function setDefault(thisform){
	
	setCookie('cookieTest', 'cookieTest', 1);
	var cookieTest = getCookie('cookieTest');
	delCookie('cookieTest');
	if (cookieTest){
		var defaultSpecies = thisform.species.value;
		setCookie('defaultSpecies', defaultSpecies, 10);
		var defaultSet = thisform.cross.value;
		setCookie('defaultSet', defaultSet, 10);
		var defaultType = thisform.tissue.value;
		setCookie('defaultType', defaultType, 10);
		var defaultDB = thisform.database.value;
		setCookie('defaultDB', defaultDB, 10);
		updateChocie('species');
		updateChocie('cross');
		updateChocie('tissue');
		updateChocie('database');		
		alert("The current settings are now your default");
	}
	else{
		alert("You need to enable Cookies in your browser.");
	}
}

