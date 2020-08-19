from __future__ import print_function, division

import csv
import xlsxwriter
import StringIO 
import datetime
import itertools

from zipfile import ZipFile, ZIP_DEFLATED

import simplejson as json

from base.trait import create_trait, retrieve_trait_info

from pprint import pformat as pf

from utility.logger import getLogger
logger = getLogger(__name__ )

def export_search_results_csv(targs):

    table_data = json.loads(targs['export_data'])
    table_rows = table_data['rows']
    
    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M_%d%B%Y')
    if 'file_name' in targs:
        zip_file_name = targs['file_name'] + "_export_" + time_str
    else:
        zip_file_name = "export_" + time_str

    metadata = []

    if 'database_name' in targs:
        if targs['database_name'] != "None":
            metadata.append(["Data Set: " + targs['database_name']])
    if 'accession_id' in targs:
        if targs['accession_id'] != "None":
            metadata.append(["Metadata Link: http://genenetwork.org/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=" + targs['accession_id']])
    metadata.append(["Export Date: " + datetime.datetime.now().strftime("%B %d, %Y")])
    metadata.append(["Export Time: " + datetime.datetime.now().strftime("%H:%M GMT")])
    if 'search_string' in targs:
        if targs['search_string'] != "None":
            metadata.append(["Search Query: " + targs['search_string']])
    if 'filter_term' in targs:
        if targs['filter_term'] != "None":
            metadata.append(["Search Filter Terms: " + targs['filter_term']])
    metadata.append(["Exported Row Number: " + str(len(table_rows))])
    metadata.append(["Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA21131), NCI MMHCC (U01CA105417), and NCRR (U01NR 105417)"])
    metadata.append([])

    trait_list = []
    for trait in table_rows:
        trait_name, dataset_name, _hash = trait.split(":")
        trait_ob = create_trait(name=trait_name, dataset_name=dataset_name)
        trait_ob = retrieve_trait_info(trait_ob, trait_ob.dataset, get_qtl_info=True)
        trait_list.append(trait_ob)

    table_headers = ['Species', 'Group', 'Dataset', 'Record ID', 'Symbol', 'Description', 'ProbeTarget', 'PubMed_ID', 'Chr', 'Mb', 'Alias', 'Gene_ID', 'Homologene_ID', 'UniGene_ID', 'Strand_Probe', 'Probe_set_specificity', 'Probe_set_BLAT_score', 'Probe_set_BLAT_Mb_start', 'Probe_set_BLAT_Mb_end', 'QTL_Chr', 'QTL_Mb', 'Locus_at_Peak', 'Max_LRS', 'P_value_of_MAX', 'Mean_Expression']

    traits_by_group = sort_traits_by_group(trait_list)

    file_list = []
    for group in list(traits_by_group.keys()):
        group_traits = traits_by_group[group]
        buff = StringIO.StringIO()
        writer = csv.writer(buff)
        csv_rows = []

        sample_headers = []
        for sample in group_traits[0].dataset.group.samplelist:
            sample_headers.append(sample)
            sample_headers.append(sample + "_SE")

        full_headers = table_headers + sample_headers

        for metadata_row in metadata:
            writer.writerow(metadata_row)

        csv_rows.append(full_headers)

        for trait in group_traits:
            if getattr(trait, "symbol", None):
                trait_symbol = getattr(trait, "symbol")
            elif getattr(trait, "abbreviation", None):
                trait_symbol = getattr(trait, "abbreviation")
            else:
                trait_symbol = "N/A"
            row_contents = [
                trait.dataset.group.species,
                trait.dataset.group.name,
                trait.dataset.name,
                trait.name,
                trait_symbol,
                getattr(trait, "description_display", "N/A"),
                getattr(trait, "probe_target_description", "N/A"),
                getattr(trait, "pubmed_id", "N/A"),
                getattr(trait, "chr", "N/A"),
                getattr(trait, "mb", "N/A"),
                trait.alias_fmt,
                getattr(trait, "geneid", "N/A"),
                getattr(trait, "homologeneid", "N/A"),
                getattr(trait, "unigeneid", "N/A"),
                getattr(trait, "strand_probe", "N/A"),
                getattr(trait, "probe_set_specificity", "N/A"),
                getattr(trait, "probe_set_blat_score", "N/A"),
                getattr(trait, "probe_set_blat_mb_start", "N/A"),
                getattr(trait, "probe_set_blat_mb_end", "N/A"),
                getattr(trait, "locus_chr", "N/A"),
                getattr(trait, "locus_mb", "N/A"),
                getattr(trait, "locus", "N/A"),
                getattr(trait, "lrs", "N/A"),
                getattr(trait, "pvalue", "N/A"),
                getattr(trait, "mean", "N/A")
            ]

            for sample in trait.dataset.group.samplelist:
                if sample in trait.data:
                    row_contents += [trait.data[sample].value, trait.data[sample].variance]
                else:
                    row_contents += ["x", "x"]

            csv_rows.append(row_contents)

        csv_rows = list(map(list, itertools.zip_longest(*[row for row in csv_rows])))
        writer.writerows(csv_rows)
        csv_data = buff.getvalue()
        buff.close()

        file_name = group + "_traits.csv"
        file_list.append([file_name, csv_data])

    return file_list

def sort_traits_by_group(trait_list=[]):
    traits_by_group = {}
    for trait in trait_list:
        if trait.dataset.group.name not in list(traits_by_group.keys()):
            traits_by_group[trait.dataset.group.name] = []

        traits_by_group[trait.dataset.group.name].append(trait)

    return traits_by_group