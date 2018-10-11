from __future__ import absolute_import, print_function, division

from flask import Flask, g

import string

from utility.logger import getLogger
logger = getLogger(__name__ )

from base import species

class SnpBrowser(object):

    MAXSNPRETURN = 5000

    def __init__(self, start_vars):
        self.strain_list = get_browser_sample_list()
        self.initialize_parameters(start_vars)

        if self.first_run == "false":
            if self.limit_strains == "true":
                self.header_fields = get_header_list(self.variant_type, self.chosen_strains)
            else:
                self.header_fields = get_header_list(self.variant_type, self.strain_list)
            self.filtered_results = self.get_table_results()

    def initialize_parameters(self, start_vars):
        self.first_run = "true"
        self.allele_list = []
        if 'variant' in start_vars: #ZS: Check if not first time loaded (if it has form input)
            self.first_run = "false"
            self.variant_type = start_vars['variant']
            self.species_name = start_vars['species']
            if self.species_name.capitalize() == "Mouse":
                self.species_id = 1
            elif self.species_name.capitalize() == "Rat":
                self.species_id = 2
            else:
                self.species_id = 0 #Using this to indicate "All Species"
 
            #ZS: Currently this is just assuming mouse for determining the chromosomes. 
            #    This logic may have to change depending upon what other species are added or how we want to deal with an "All Species" option
            self.chr_list = []
            species_ob = species.TheSpecies(species_name="Mouse")
            for key in species_ob.chromosomes.chromosomes:
                self.chr_list.append(species_ob.chromosomes.chromosomes[key].name)

            if start_vars['gene_name'] != "":
                self.gene_name = start_vars['gene_name']
            else:
                self.gene_name = ""
                self.chr = start_vars['chr']
                try:
                    self.start_mb = float(start_vars['start_mb'])
                    self.end_mb = float(start_vars['end_mb'])
                except:
                    self.start_mb = 0.0
                    self.end_mb = 0.0

            if 'limit_strains' in start_vars:
                self.limit_strains = "true"
            else:
                self.limit_strains = "false"
            self.chosen_strains = start_vars['chosen_strains'].split(",")
            self.domain = start_vars['domain']
            self.function = start_vars['function']
            self.source = start_vars['source']
            self.criteria = start_vars['criteria']
            self.score = start_vars['score']

            self.redundant = "false"
            self.diff_alleles = "false"
            if 'redundant' in start_vars:
                self.redundant = "true"
            if 'diff_alleles' in start_vars:
                self.diff_alleles = "true"

        else: #ZS: Default values
            self.variant_type = "SNP"
            self.species_name = "Mouse"
            species_ob = species.TheSpecies(species_name=self.species_name)
            self.chr_list = []
            for key in species_ob.chromosomes.chromosomes:
                self.chr_list.append(species_ob.chromosomes.chromosomes[key].name)

            self.chr = "19"
            self.start_mb = 30.1
            self.end_mb = 30.12

            self.limit_strains = "true"

            self.chosen_strains = ["C57BL/6J",
                                   "DBA/2J",
                                   "A/J",
                                   "129S1/SvImJ",
                                   "NOD/ShiLtJ",
                                   "NZO/HlLtJ",
                                   "WSB/EiJ",
                                   "PWK/PhJ",
                                   "CAST/EiJ"]
            
            self.domain = "All"
            self.function = "All"
            self.source = "All"
            self.criteria = ">="
            self.score = 0.0

            self.redundant = "false"
            self.diff_alleles = "true"

    def get_table_results(self):
        self.snp_list = None

        if self.gene_name != "":
            query = "SELECT geneSymbol, chromosome, txStart, txEnd FROM GeneList WHERE SpeciesId = %s AND geneSymbol = %s" % (self.species_id, self.gene_name)
            result = g.db.execute(query).fetchone()
            if result:
                self.gene_name, self.chr, self.start_mb, self.end_mb = result
            else:
                result_snp = None
                if self.variant_type == "SNP":
                    if self.gene_name[:2] == "rs":
                        query = "SELECT Id, Chromosome, Position, Position+0.000001 FROM SnpAll WHERE Rs = %s" % self.gene_name
                    else:
                        query = "SELECT Id, Chromosome, Position, Position+0.000001 ForM SnpAll where SpeciesId = %s AND SnpName = %s" % (self.species_id, self.gene_name)
                    result_snp = g.db.execute(query).fetchall()
                    if result_snp:
                        self.snp_list = [item[0] for item in result_snp]
                        self.chr = result_snp[0][1]
                        self.start_mb = result_snp[0][2]
                        self.end_mb = result_snp[0][3]
                    else:
                        return
                elif self.variant_type == "InDel":
                    if self.gene_name[0] == "I":
                        query = "SELECT Id, Chromosome, Mb_start, Mb_end FROM IndelAll WHERE SpeciesId = %s AND Name = %s" % (self.species_id, self.gene_name)
                        result_snp = g.db.execute(query).fetchall()
                    if result_snp:
                        self.snp_list = [item[0] for item in result_snp]
                        self.chr = result_snp[0][1]
                        self.start_mb = result_snp[0][2]
                        self.end_mb = result_snp[0][3]
                    else:
                        return

        if self.variant_type == "SNP":
            query = """
                       SELECT
                               a.*, b.*
                       FROM
                               SnpAll a, SnpPattern b
                       WHERE
                               a.SpeciesId = %s AND a.Chromosome = '%s' AND
                               a.Position >= %.6f AND a.Position < %.6f AND
                               a.Id = b.SnpId
                       ORDER BY a.Position
                    """ % (self.species_id, self.chr, self.start_mb, self.end_mb)
        elif self.variant_type == "InDel":
            query = """
                       SELECT
                               DISTINCT a.Name, a.Chromosome, a.SourceId, a.Mb_start, a.Mb_end, a.Strand, a.Type, a.Size, a.InDelSequence, b.Name
                       FROM
                               IndelAll a, SnpSource b
                       WHERE
                               a.SpeciesId = '%s' AND a.Chromosome = '%s' AND
                               a.Mb_start >= %2.6f AND a.Mb_start < (%2.6f+.0010) AND
                               b.Id = a.SourceId
                       ORDER BY a.Mb_start
                    """ % (self.species_id, self.chr, self.start_mb, self.end_mb)

        results_all = g.db.execute(query).fetchall()

        return self.filter_results(results_all)

    def filter_results(self, results):
        filtered_results = []
        strain_index_list = [] #ZS: List of positions of selected strains in strain list
        last_mb = -1

        if self.limit_strains == "true" and len(self.chosen_strains) > 0:
            for item in self.chosen_strains:
                index = self.strain_list.index(item)
                strain_index_list.append(index)

        for seq, result in enumerate(results):
            result = list(result)

            if self.variant_type == "SNP":
                display_strains = []
                snp_id, species_id, snp_name, rs, chr, mb, mb_2016, alleles, snp_source, conservation_score = result[:10]
                effect_list = result[10:26]
                self.allele_list = result[27:]

                if self.limit_strains == "true" and len(self.chosen_strains) > 0:
                    for index in strain_index_list:
                        display_strains.append(result[27+index])
                    self.allele_list = display_strains

                effect_info_dict = get_effect_info(effect_list)
                coding_domain_list = ['Start Gained', 'Start Lost', 'Stop Gained', 'Stop Lost', 'Nonsynonymous', 'Synonymous']
                intron_domain_list = ['Splice Site', 'Nonsplice Site']

                for key in effect_info_dict:
                    if key in coding_domain_list:
                        domain = ['Exon', 'Coding']
                    elif key in ['3\' UTR', '5\' UTR']:
                        domain = ['Exon', key]
                    elif key == "Unknown Effect In Exon":
                        domain = ['Exon', '']
                    elif key in intron_domain_list:
                        domain = ['Intron', key]
                    else:
                        domain = [key, '']

                    if 'Intergenic' in domain:
                        gene = transcript = exon = function = function_details = ''
                        if self.redundant == "false" or last_mb != mb: # filter redundant
                            if self.include_record(domain, function, snp_source, conservation_score):
                                info_list = [snp_name, rs, chr, mb, alleles, gene, transcript, exon, domain, function, function_details, snp_source, conservation_score, snp_id]
                                info_list.extend(self.allele_list)
                                filtered_results.append(info_list)
                        last_mb = mb
                    else:
                        gene_list, transcript_list, exon_list, function_list, function_details_list = effect_info_dict[key]
                        for index, item in enumerate(gene_list):
                            gene = item
                            transcript = transcript_list[index]
                            if exon_list:
                                exon = exon_list[index]
                            else:
                                exon = ""

                            if function_list:
                                function = function_list[index]
                                if function == "Unknown Effect In Exon":
                                    function = "Unknown"
                            else:
                                function = ""

                            if function_details_list:
                                function_details = "Biotype: " + function_details_list[index]
                            else:
                                function_details = ""

                            if self.redundant == "false" or last_mb != mb:
                                if self.include_record(domain, function, snp_source, conservation_score):
                                    info_list = [snp_name, rs, chr, mb, alleles, gene, transcript, exon, domain, function, function_details, snp_source, conservation_score, snp_id]
                                    info_list.extend(self.allele_list)
                                    filtered_results.append(info_list)
                            last_mb = mb

            elif self.variant == "InDel":
                # The order of variables is important; this applies to anything from the variant table as indel
                indel_name, indel_chr, source_id, indel_mb_start, indel_mb_end, indel_strand, indel_type, indel_size, indel_sequence, source_name = result

                indel_type = indel_type.title()
                if self.redundant == "false" or last_mb != indel_mb_start:
                    gene = "No Gene"
                    domain = conservation_score = snp_id = snp_name = rs = flank_3 = flank_5 = ncbi = function = ""
                    if self.include_record(domain, function, source_name, conservation_score):
                        filtered_results.append([indel_name, indel_chr, indel_mb_start, indel_mb_end, indel_strand, indel_type, indel_size, indel_sequence, source_name])
                last_mb = indel_mb_start

            else:
                filtered_results.append(result)

        return filtered_results

    def include_record(self, domain, function, snp_source, conservation_score):
        """ Decide whether to add this record """

        domain_satisfied = True
        function_satisfied = True
        different_alleles_satisfied = True
        source_satisfied = True

        if domain:
            if len(domain) == 0:
                if self.domain != "All":
                    domain_satisfied = False
            else:
                domain_satisfied = False
                if domain[0].startswith(self.domain) or domain[1].startswith(self.domain) or self.domain == "All":
                    domain_satisfied = True
        else:
            if self.domain != "All":
                domain_satisfied = False

        if snp_source:
            if len(snp_source) == 0:
                if self.source != "All":
                    source_satisfied = False
            else:
                source_satisfied = False
                if snp_source.startswith(self.source) or self.source == "All":
                    source_satisfied = True
        else:
            if self.source != "All":
                source_satisfied = False

        if function:
            if len(function) == 0:
                if self.function != "All":
                    function_satisfied = False
            else:
                function_satisfied = False
                if function.startswith(self.function):
                    function_satisfied = True
        else:
            if self.function != "All":
                function_satisfied = False

        if conservation_score:
            score_as_float = float(conservation_score)
            try:
                input_score_float = float(self.score) # the user-input score
            except:
                input_score_float = 0.0

            if self.criteria == ">=":
                if score_as_float >= input_score_float:
                    score_satisfied = True
                else:
                    score_satisfied = False
            elif self.criteria == "==":
                if score_as_float == input_score_float:
                    score_satisfied = True
                else:
                    score_satisfied = False
            elif self.criteria == "<=":
                if score_as_float <= input_score_float:
                    score_satisfied = True
                else:
                    score_satisfied = False
        else:
            try:
                if float(self.score) > 0:
                    score_satisfied = False
                else:
                    score_satisfied = True
            except:
                score_satisfied = True

        if self.variant_type == "SNP" and self.diff_alleles == "true":
            this_allele_list = []

            for item in self.allele_list:
                if item and (item.lower() not in this_allele_list) and (item != "-"):
                    this_allele_list.append(item.lower())

            total_allele_count = len(this_allele_list)
            if total_allele_count <= 1:
                different_alleles_satisfied = False
            else:
                different_alleles_satisfied = True
        else:
            different_alleles_satisfied = True

        return domain_satisfied and function_satisfied and source_satisfied and score_satisfied and different_alleles_satisfied

def get_browser_sample_list(species_id=1):
    sample_list = []
    query = "SHOW COLUMNS FROM SnpPattern;"
    results = g.db.execute(query).fetchall();
    for result in results[1:]:
        sample_list.append(result[0])

    return sample_list

def get_header_list(variant_type, strain_list):
    if variant_type == "SNP":
        header_fields = ['Index', 'SNP ID', 'Chr', 'Mb', 'Alleles', 'Source', 'ConScore', 'Gene', 'Transcript', 'Exon', 'Domain 1', 'Domain 2', 'Function', 'Details']
        header_fields.extend(strain_list)
    elif variant_type == "InDel":
        header_fields = ['Index', 'ID', 'Type', 'InDel Chr', 'Mb Start', 'Mb End', 'Strand', 'Size', 'Sequence', 'Source']
    else:
        header_fields = []

    return header_fields

def get_effect_details_by_category(effect_name = None, effect_value = None):
    gene_list = []
    transcript_list = []
    exon_list = []
    function_list = []
    function_detail_list = []
    tmp_list = []

    gene_group_list = ['Upstream', 'Downstream', 'Splice Site', 'Nonsplice Site', '3\' UTR']
    biotype_group_list = ['Unknown Effect In Exon', 'Start Gained', 'Start Lost', 'Stop Gained', 'Stop Lost', 'Nonsynonymous', 'Synonymous']
    new_codon_group_list = ['Start Gained']
    codon_effect_group_list = ['Start Lost', 'Stop Gained', 'Stop Lost', 'Nonsynonymous', 'Synonymous']

    effect_detail_list = string.split(string.strip(effect_value), '|')
    effect_detail_list = map(string.strip, effect_detail_list)

    for index, item in enumerate(effect_detail_list):
        item_list = string.split(string.strip(item), ',')
        item_list = map(string.strip, item_list)

        gene_id = item_list[0]
        gene_name = item_list[1]
        gene_list.append([gene_id, gene_name])
        transcript_list.append(item_list[2])

        if effect_name not in gene_group_list:
            exon_id = item_list[3]
            exon_rank = item_list[4]
            exon_list.append([exon_id, exon_rank])

        if effect_name in biotype_group_list:
            biotype = item_list[5]
            function_list.append(effect_name)

            if effect_name in new_codon_group_list:
                new_codon = item_list[6]
                tmp_list = [biotype, new_codon]
                function_detail_list.append(string.join(tmp_list, ", "))
            elif effect_name in codon_effect_group_list:
                old_new_AA = item_list[6]
                old_new_codon = item_list[7]
                codon_num = item_list[8]
                tmp_list = [biotype, old_new_AA, old_new_codon, codon_num]
                function_detail_list.append(string.join(tmp_list, ", "))
            else:
                function_detail_list.append(biotype)

    return [gene_list, transcript_list, exon_list, function_list, function_detail_list]

def get_effect_info(effect_list):
    domain = ""
    effect_detail_list = []
    effect_info_dict = {}

    prime3_utr, prime5_utr, upstream, downstream, intron, nonsplice_site, splice_site, intergenic = effect_list[:8]
    exon, non_synonymous_coding, synonymous_coding, start_gained, start_lost, stop_gained, stop_lost, unknown_effect_in_exon = effect_list[8:]

    if intergenic:
        domain = "Intergenic"
        effect_info_dict[domain] = ""
    else:
        # if not exon, get gene list/transcript list info
        if upstream:
            domain = "Upstream"
            effect_detail_list = get_effect_details_by_category(effect_name='Upstream', effect_value=upstream)
            effect_info_dict[domain] = effect_detail_list
        if downstream:
            domain = "Downstream"
            effect_detail_list = get_effect_details_by_category(effect_name='Downstream', effect_value=downstream)
            effect_info_dict[domain] = effect_detail_list
        if intron:
            if splice_site:
                domain = "Splice Site"
                effect_detail_list = get_effect_details_by_category(effect_name='Splice Site', effect_value=splice_site)
                effect_info_dict[domain] = effect_detail_list
            if nonsplice_site:
                domain = "Downstream"
                effect_detail_list = get_effect_details_by_category(effect_name='Nonsplice Site', effect_value=nonsplice_site)
                effect_info_dict[domain] = effect_detail_list
        # get gene, transcript_list, and exon info
        if prime3_utr:
            domain = "3\' UTR"
            effect_detail_list = get_effect_details_by_category(effect_name='3\' UTR', effect_value=prime3_utr)
            effect_info_dict[domain] = effect_detail_list
        if prime5_utr:
            domain = "5\' UTR"
            effect_detail_list = get_effect_details_by_category(effect_name='5\' UTR', effect_value=prime5_utr)
            effect_info_dict[domain] = effect_detail_list

        if start_gained:
            domain = "Start Gained"
            effect_detail_list = get_effect_details_by_category(effect_name='Start Gained', effect_value=start_gained)
            effect_info_dict[domain] = effect_detail_list
        if unknown_effect_in_exon:
            domain = "Unknown Effect In Exon"
            effect_detail_list = get_effect_details_by_category(effect_name='Unknown Effect In Exon', effect_value=unknown_effect_in_exon)
            effect_info_dict[domain] = effect_detail_list
        if start_lost:
            domain = "Start Lost"
            effect_detail_list = get_effect_details_by_category(effect_name='Start Lost', effect_value=start_lost)
            effect_info_dict[domain] = effect_detail_list
        if stop_gained:
            domain = "Stop Gained"
            effect_detail_list = get_effect_details_by_category(effect_name='Stop Gained', effect_value=stop_gained)
            effect_info_dict[domain] = effect_detail_list
        if stop_lost:
            domain = "Stop Lost"
            effect_detail_list = get_effect_details_by_category(effect_name='Stop Lost', effect_value=stop_lost)
            effect_info_dict[domain] = effect_detail_list

        if non_synonymous_coding:
            domain = "Nonsynonymous"
            effect_detail_list = get_effect_details_by_category(effect_name='Nonsynonymous', effect_value=non_synonymous_coding)
            effect_info_dict[domain] = effect_detail_list
        if synonymous_coding:
            domain = "Synonymous"
            effect_detail_list = get_effect_details_by_category(effect_name='Synonymous', effect_value=synonymous_coding)
            effect_info_dict[domain] = effect_detail_list

    return effect_info_dict
