import csv
import datetime
import io
import itertools
import re
import xlsxwriter

from pprint import pformat as pf
from zipfile import ZipFile, ZIP_DEFLATED

import simplejson as json

from gn3.computations.gemma import generate_hash_of_string

from gn2.base.trait import create_trait, retrieve_trait_info


def export_traits(targs, export_type="full"):
    if export_type == "collection":
        return export_collection(targs)
    elif export_type == "sample_data":
        return export_sample_data(targs)
    else:
        return export_traitlist(targs)

def export_collection(targs):
    table_data = json.loads(targs['export_data'])
    table_rows = table_data['rows']

    buff = io.StringIO()
    writer = csv.writer(buff)

    now = datetime.datetime.now()
    time_str = now.strftime('%H:%M (UTC) %m/%d/%y')

    metadata_rows = [
        ["# Collection Name: " + targs['collection_name_export']],
        ["# User E-mail: " + targs['user_email_export']],
        ["# Time/Date: " + time_str]
    ]

    for row in metadata_rows:
        writer.writerow(row)

    for trait in table_rows:
        writer.writerow([trait])

    csv_data = buff.getvalue()
    buff.close()

    if 'collection_name_export' in targs:
        file_name = re.sub('\s+', '_', targs['collection_name_export']) # replace whitespace with underscore
    else:
        file_name = generate_hash_of_string("".join(table_rows))

    return [file_name, csv_data]

def export_traitlist(targs):
    table_data = json.loads(targs['export_data'])
    table_rows = table_data['rows']

    metadata = []

    if 'database_name' in targs:
        if targs['database_name'] != "None":
            metadata.append(["Data Set: " + targs['database_name']])
            metadata.append(["Data Set Type: "  + targs['dataset_type']])
    if 'accession_id' in targs:
        if targs['accession_id'] != "None":
            metadata.append(
                ["Metadata Link: http://genenetwork.org/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=" + targs['accession_id']])
    metadata.append(
        ["Export Date: " + datetime.datetime.now().strftime("%B %d, %Y")])
    metadata.append(
        ["Export Time: " + datetime.datetime.now().strftime("%H:%M GMT")])
    if 'search_string' in targs:
        if targs['search_string'] != "None":
            metadata.append(["Search Query: " + targs['search_string']])
    if 'filter_term' in targs:
        if targs['filter_term'] != "None":
            metadata.append(["Search Filter Terms: " + targs['filter_term']])
    metadata.append(["Exported Row Number: " + str(len(table_rows))])
    metadata.append(["Funding for The GeneNetwork: NIGMS (R01 GM123489, 2017-2026), NIDA (P30 DA044223, 2017-2022), NIA (R01AG043930, 2013-2018), NIAAA (U01 AA016662, U01 AA013499, U24 AA013513, U01 AA014425, 2006-2017), NIDA/NIMH/NIAAA (P20-DA 21131, 2001-2012), NCI MMHCC (U01CA105417), NCRR/BIRN (U24 RR021760)"])
    metadata.append([])

    trait_list = []
    for trait in table_rows:
        trait_name, dataset_name, _hash = trait.split(":")
        trait_ob = create_trait(name=trait_name, dataset_name=dataset_name)
        trait_ob = retrieve_trait_info(
            trait_ob, trait_ob.dataset, get_qtl_info=True)
        trait_list.append(trait_ob)

    table_headers = ['Index', 'URL', 'Species', 'Group', 'Dataset', 'Record ID', 'Symbol', 'Description', 'ProbeTarget', 'PubMed_ID', 'Chr', 'Mb', 'Alias', 'Gene_ID', 'Homologene_ID', 'UniGene_ID',
                     'Strand_Probe', 'Probe_set_specificity', 'Probe_set_BLAT_score', 'Probe_set_BLAT_Mb_start', 'Probe_set_BLAT_Mb_end', 'QTL_Chr', 'QTL_Mb', 'Locus_at_Peak', 'Max_LRS', 'P_value_of_MAX', 'Mean_Expression']

    traits_by_group = sort_traits_by_group(trait_list)

    file_list = []
    for group in traits_by_group:
        group_traits = traits_by_group[group]
        samplelist = group_traits[0].dataset.group.all_samples_ordered()
        if not samplelist:
            continue

        buff = io.StringIO()
        writer = csv.writer(buff)
        csv_rows = []

        sample_headers = []
        for sample in samplelist:
            sample_headers.append(sample)
            sample_headers.append(sample + "_SE")

        full_headers = table_headers + sample_headers

        for metadata_row in metadata:
            writer.writerow(metadata_row)

        csv_rows.append(full_headers)

        for i, trait in enumerate(group_traits):
            if getattr(trait, "symbol", None):
                trait_symbol = getattr(trait, "symbol")
            elif getattr(trait, "abbreviation", None):
                trait_symbol = getattr(trait, "abbreviation")
            else:
                trait_symbol = "N/A"
            row_contents = [
                i + 1,
                "https://genenetwork.org/show_trait?trait_id=" + \
                str(trait.name) + "&dataset=" + str(trait.dataset.name),
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

            for sample in samplelist:
                if sample in trait.data:
                    trait_val = trait.data[sample].value if trait.data[sample].value else "x"
                    trait_var = trait.data[sample].variance if trait.data[sample].variance else "x"
                    row_contents += [trait_val,
                                     trait_var]
                else:
                    row_contents += ["x", "x"]

            csv_rows.append(row_contents)

        writer.writerows(csv_rows)
        csv_data = buff.getvalue()
        buff.close()

        file_name = group + "_traits.csv"
        file_list.append([file_name, csv_data])

    return file_list

def export_sample_data(targs):
    table_data = json.loads(targs['export_data'])
    table_rows = table_data['rows']

    trait_list = []
    for trait in table_rows:
        trait_name, dataset_name, _hash = trait.split(":")
        trait_ob = create_trait(name=trait_name, dataset_name=dataset_name)
        trait_ob = retrieve_trait_info(
            trait_ob, trait_ob.dataset, get_qtl_info=True)
        trait_list.append(trait_ob)

    samplelist = trait_list[0].dataset.group.all_samples_ordered()

    buff = io.StringIO()
    writer = csv.writer(buff)
    csv_rows = []

    table_headers = ['Id', 'Symbol']

    sample_headers = []
    for sample in samplelist:
        sample_headers.append(sample)

    full_headers = table_headers + sample_headers
    csv_rows.append(full_headers)

    for trait in trait_list:
        if getattr(trait, "symbol", None):
            trait_symbol = getattr(trait, "symbol")
        elif getattr(trait, "abbreviation", None):
            trait_symbol = getattr(trait, "abbreviation")

        val_row = [trait.name, trait_symbol]
        se_row = ["", "SE"]
        n_row = ["", "N"]

        for sample in samplelist:
            if sample in trait.data:
                trait_val = trait.data[sample].value if trait.data[sample].value else "x"
                trait_var = trait.data[sample].variance if trait.data[sample].variance else "x"
                trait_n = trait.data[sample].num_cases if trait.data[sample].num_cases else "x"
                val_row += [trait_val]
                se_row += [trait_var]
                n_row += [trait_n]
            else:
                val_row += "x"
                se_row += "x"
                n_row += "x"

        csv_rows += [val_row, se_row]
        if trait.dataset.type == "Publish":
            csv_rows += [n_row]

    writer.writerows(csv_rows)
    csv_data = buff.getvalue()
    buff.close()

    file_name = trait_list[0].dataset.group.name + "_sample_data.csv"
    file_list = [[file_name, csv_data]]

    return file_list

def sort_traits_by_group(trait_list=[]):
    traits_by_group = {}
    for trait in trait_list:
        if trait.dataset.group.name not in list(traits_by_group.keys()):
            traits_by_group[trait.dataset.group.name] = []

        traits_by_group[trait.dataset.group.name].append(trait)

    return traits_by_group
