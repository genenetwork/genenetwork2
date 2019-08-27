from __future__ import absolute_import, print_function, division

from flask import Flask, g, url_for

import string
import piddle as pid

from utility.logger import getLogger
logger = getLogger(__name__ )

from base import species
from base import webqtlConfig

class SnpBrowser(object):

    def __init__(self, start_vars):
        self.strain_lists = get_browser_sample_lists()
        self.initialize_parameters(start_vars)
        self.limit_number = 10000

        if self.first_run == "false":
            self.filtered_results = self.get_browser_results()

            if len(self.filtered_results) <= self.limit_number:
                self.table_rows = self.get_table_rows()
            else:
                self.empty_columns = None
                self.table_rows = []

            if self.limit_strains == "true":
                self.header_fields, self.empty_field_count = get_header_list(variant_type = self.variant_type, strains = self.chosen_strains, empty_columns = self.empty_columns)
            else:
                self.header_fields, self.empty_field_count = get_header_list(variant_type = self.variant_type, strains = self.strain_lists, species = self.species_name, empty_columns = self.empty_columns)

    def initialize_parameters(self, start_vars):
        if 'first_run' in start_vars:
            self.first_run = "false"
        else:
            self.first_run = "true"
        self.allele_list = []

        self.variant_type = "SNP"
        if 'variant' in start_vars:
            self.variant_type = start_vars['variant']

        self.species_name = "Mouse"
        self.species_id = 1
        if 'species' in start_vars:
            self.species_name = start_vars['species']
            if self.species_name.capitalize() == "Rat":
                self.species_id = 2

        self.mouse_chr_list = []
        self.rat_chr_list = []
        mouse_species_ob = species.TheSpecies(species_name="Mouse")
        for key in mouse_species_ob.chromosomes.chromosomes:
            self.mouse_chr_list.append(mouse_species_ob.chromosomes.chromosomes[key].name)
        rat_species_ob = species.TheSpecies(species_name="Rat")
        for key in rat_species_ob.chromosomes.chromosomes:
            self.rat_chr_list.append(rat_species_ob.chromosomes.chromosomes[key].name)

        if self.species_id == 1:
            self.this_chr_list = self.mouse_chr_list
        else:
            self.this_chr_list = self.rat_chr_list

        if self.first_run == "true":
            self.chr = "19"
            self.start_mb = 30.1
            self.end_mb = 30.12
        else:
            if 'gene_name' in start_vars:
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
            else:
                try:
                    self.chr = start_vars['chr']
                    self.start_mb = float(start_vars['start_mb'])
                    self.end_mb = float(start_vars['end_mb'])
                except:
                    self.chr = "1"
                    self.start_mb = 0.0
                    self.end_mb = 0.0

        self.limit_strains = "true"
        if self.first_run == "false":
            if 'limit_strains' not in start_vars:
                self.limit_strains = "false"
            else:
                if start_vars['limit_strains'] == "false":
                    self.limit_strains = "false"

        self.chosen_strains_mouse = ["C57BL/6J",
                                     "DBA/2J",
                                     "A/J",
                                     "129S1/SvImJ",
                                     "NOD/ShiLtJ",
                                     "NZO/HlLtJ",
                                     "WSB/EiJ",
                                     "PWK/PhJ",
                                     "CAST/EiJ"]
        self.chosen_strains_rat = ["BN", "F344", "WLI", "WMI"]
        if 'chosen_strains_mouse' in start_vars:
            self.chosen_strains_mouse = start_vars['chosen_strains_mouse'].split(",")
        if 'chosen_strains_rat' in start_vars:
            self.chosen_strains_rat = start_vars['chosen_strains_rat'].split(",")

        if self.species_id == 1:
            self.chosen_strains = self.chosen_strains_mouse
        else:
            self.chosen_strains = self.chosen_strains_rat

        self.domain = "All"
        if 'domain' in start_vars:
            self.domain = start_vars['domain']
        self.function = "All"
        if 'function' in start_vars:
            self.function = start_vars['function']
        self.source = "All"
        if 'source' in start_vars:
            self.source = start_vars['source']
        self.criteria = ">="
        if 'criteria' in start_vars:
            self.criteria = start_vars['criteria']
        self.score = 0.0
        if 'score' in start_vars:
            self.score = start_vars['score']

        self.redundant = "false"
        if self.first_run == "false" and 'redundant' in start_vars:
            self.redundant = "true"
        self.diff_alleles = "true"
        if self.first_run == "false":
            if 'diff_alleles' not in start_vars:
                self.diff_alleles = "false"
            else:
                if start_vars['diff_alleles'] == "false":
                    self.diff_alleles = "false"

    def get_browser_results(self):
        self.snp_list = None

        if self.gene_name != "":
            if self.species_id != 0:
                query = "SELECT geneSymbol, chromosome, txStart, txEnd FROM GeneList WHERE SpeciesId = %s AND geneSymbol = '%s'" % (self.species_id, self.gene_name)
            else:
                query = "SELECT geneSymbol, chromosome, txStart, txEnd FROM GeneList WHERE geneSymbol = '%s'" % (self.gene_name)
            result = g.db.execute(query).fetchone()
            if result:
                self.gene_name, self.chr, self.start_mb, self.end_mb = result
            else:
                result_snp = None
                if self.variant_type == "SNP":
                    if self.gene_name[:2] == "rs":
                        query = "SELECT Id, Chromosome, Position, Position+0.000001 FROM SnpAll WHERE Rs = '%s'" % self.gene_name
                    else:
                        if self.species_id != 0:
                            query = "SELECT Id, Chromosome, Position, Position+0.000001 FROM SnpAll where SpeciesId = %s AND SnpName = '%s'" % (self.species_id, self.gene_name)
                        else:
                            query = "SELECT Id, Chromosome, Position, Position+0.000001 FROM SnpAll where SnpName = '%s'" % (self.gene_name)
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
                        if self.species_id != 0:
                            query = "SELECT Id, Chromosome, Mb_start, Mb_end FROM IndelAll WHERE SpeciesId = %s AND Name = '%s'" % (self.species_id, self.gene_name)
                        else:
                            query = "SELECT Id, Chromosome, Mb_start, Mb_end FROM IndelAll WHERE Name = '%s'" % (self.gene_name)
                        result_snp = g.db.execute(query).fetchall()
                    if result_snp:
                        self.snp_list = [item[0] for item in result_snp]
                        self.chr = result_snp[0][1]
                        self.start_mb = result_snp[0][2]
                        self.end_mb = result_snp[0][3]
                    else:
                        return

        if self.variant_type == "SNP":
            mouse_query = """
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

            rat_query = """
                       SELECT
                           a.*, b.*
                       FROM
                           SnpAll a, RatSnpPattern b
                       WHERE
                           a.SpeciesId = %s AND a.Chromosome = '%s' AND
                           a.Position >= %.6f AND a.Position < %.6f AND
                           a.Id = b.SnpId
                       ORDER BY a.Position
                    """ % (self.species_id, self.chr, self.start_mb, self.end_mb)
            if self.species_id == 1:
                query = mouse_query
            elif self.species_id == 2:
                query = rat_query

        elif self.variant_type == "InDel":
            if self.species_id != 0:
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
            else:
                query = """
                           SELECT
                               DISTINCT a.Name, a.Chromosome, a.SourceId, a.Mb_start, a.Mb_end, a.Strand, a.Type, a.Size, a.InDelSequence, b.Name
                           FROM
                               IndelAll a, SnpSource b
                           WHERE
                               a.Chromosome = '%s' AND
                               a.Mb_start >= %2.6f AND a.Mb_start < (%2.6f+.0010) AND
                               b.Id = a.SourceId
                           ORDER BY a.Mb_start
                        """ % (self.chr, self.start_mb, self.end_mb)

        results_all = g.db.execute(query).fetchall()

        return self.filter_results(results_all)

    def filter_results(self, results):
        filtered_results = []
        strain_index_list = [] #ZS: List of positions of selected strains in strain list
        last_mb = -1

        if self.limit_strains == "true" and len(self.chosen_strains) > 0:
            for item in self.chosen_strains:
                index = self.strain_lists[self.species_name.lower()].index(item)
                strain_index_list.append(index)

        for seq, result in enumerate(results):
            result = list(result)

            if self.variant_type == "SNP":
                display_strains = []
                snp_id, species_id, snp_name, rs, chr, mb, mb_2016, alleles, snp_source, conservation_score = result[:10]
                effect_list = result[10:28]
                if self.species_id == 1:
                    self.allele_list = result[30:]
                elif self.species_id == 2:
                    self.allele_list = result[31:]

                if self.limit_strains == "true" and len(self.chosen_strains) > 0:
                    for index in strain_index_list:
                        if self.species_id == 1:
                            display_strains.append(result[29+index])
                        elif self.species_id == 2:
                            display_strains.append(result[31+index])
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
                        if self.gene_name != "":
                            gene_id = get_gene_id(self.species_id, self.gene_name)
                            gene = [gene_id, self.gene_name]
                        else:
                            gene = check_if_in_gene(species_id, chr, mb)
                        transcript = exon = function = function_details = ''
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

            elif self.variant_type == "InDel":
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

    def get_table_rows(self):
        """ Take results and put them into the order and format necessary for the tables rows """

        if self.variant_type == "SNP":
            gene_name_list = []
            for item in self.filtered_results:
                if item[5] and item[5] != "":
                    gene_name = item[5][1]
                    # eliminate duplicate gene_name
                    if gene_name and (gene_name not in gene_name_list):
                        gene_name_list.append(gene_name)
            if len(gene_name_list) > 0:
                gene_id_name_dict = get_gene_id_name_dict(self.species_id, gene_name_list)

        #ZS: list of booleans representing which columns are entirely empty, so they aren't displayed on the page; only including ones that are sometimes empty (since there's always a location, etc)
        self.empty_columns = {
                    "snp_source": "false",
                    "conservation_score": "false",
                    "gene_name": "false",
                    "transcript": "false",
                    "exon": "false",
                    "domain_2": "false",
                    "function": "false", 
                    "function_details": "false"
            }

        the_rows = []
        for i, result in enumerate(self.filtered_results):
            this_row = []
            if self.variant_type == "SNP":
                snp_name, rs, chr, mb, alleles, gene, transcript, exon, domain, function, function_details, snp_source, conservation_score, snp_id = result[:14]
                allele_value_list = result[14:]
                if rs:
                    snp_url = webqtlConfig.DBSNP % (rs)
                    snp_name = rs
                else:
                    rs = ""
                    start_bp = int(mb*1000000 - 100)
                    end_bp = int(mb*1000000 + 100)
                    position_info = "chr%s:%d-%d" % (chr, start_bp, end_bp)
                    if self.species_id == 2:
                        snp_url = webqtlConfig.GENOMEBROWSER_URL % ("rn6", position_info)
                    else:
                        snp_url = webqtlConfig.GENOMEBROWSER_URL % ("mm10", position_info)

                mb = float(mb)
                mb_formatted = "%2.6f" % mb

                if snp_source == "Sanger/UCLA":
                    source_url_1 = "http://www.sanger.ac.uk/resources/mouse/genomes/"
                    source_url_2 = "http://mouse.cs.ucla.edu/mousehapmap/beta/wellcome.html"
                    source_urls = [source_url_1, source_url_2]
                    self.empty_columns['snp_source'] = "true"
                else:
                    source_urls = []

                if not conservation_score:
                    conservation_score = ""
                else:
                    self.empty_columns['conservation_score'] = "true"

                if gene:
                    gene_name = gene[1]
                    # if gene_name has related gene_id, use gene_id for NCBI search
                    if (gene_name in gene_id_name_dict) and (gene_id_name_dict[gene_name] != None and gene_id_name_dict[gene_name] != ""):
                        gene_id = gene_id_name_dict[gene[1]]
                        gene_link = webqtlConfig.NCBI_LOCUSID % gene_id
                    else:
                        gene_link = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % gene_name

                    self.empty_columns['gene_name'] = "true"
                else:
                    gene_name = ""
                    gene_link = ""

                if transcript:
                    transcript_link = webqtlConfig.ENSEMBLETRANSCRIPT_URL % (transcript)
                    self.empty_columns['transcript'] = "true"
                else:
                    transcript_link = ""

                if exon:
                    exon = exon[1] # exon[0] is exon_id, exon[1] is exon_rank
                    self.empty_columns['exon'] = "true"
                else:
                    exon = ""

                if domain:
                    domain_1 = domain[0]
                    domain_2 = domain[1]
                    if domain_1 == "Intergenic" and gene != "":
                        domain_1 = gene_name
                    else:
                        if domain_1 == "Exon":
                            domain_1 = domain_1 + " " + exon

                    if domain_2 != "":
                        self.empty_columns['domain_2'] = "true"

                if function:
                    self.empty_columns['function'] = "true"

                function_list = []
                if function_details:
                    function_list = string.split(string.strip(function_details), ",")
                    function_list = map(string.strip, function_list)
                    function_list[0] = function_list[0].title()
                    function_details = ", ".join(item for item in function_list)
                    function_details = function_details.replace("_", " ")
                    function_details = function_details.replace("/", " -> ")
                    if function_details == "Biotype: Protein Coding":
                        function_details = function_details + ", Coding Region Unknown"

                    self.empty_columns['function_details'] = "true"
                    
                #[snp_href, chr, mb_formatted, alleles, snp_source_cell, conservation_score, gene_name_cell, transcript_href, exon, domain_1, domain_2, function, function_details]

                base_color_dict = {"A": "#C33232", "C": "#1569C7", "T": "#CFCF32", "G": "#32C332", 
                                   "t": "#FF6", "c": "#5CB3FF", "a": "#F66", "g": "#CF9", ":": "#FFFFFF", "-": "#FFFFFF", "?": "#FFFFFF"}


                the_bases = []
                for j, item in enumerate(allele_value_list):
                    if item and isinstance(item, basestring):
                        this_base = [str(item), base_color_dict[item]]
                    else:
                        this_base = ""

                    the_bases.append(this_base)

                this_row = {
                    "index": i + 1,
                    "rs": str(rs),
                    "snp_url": str(snp_url),
                    "snp_name": str(snp_name),
                    "chr": str(chr),
                    "mb_formatted": mb_formatted,
                    "alleles": str(alleles),
                    "snp_source": str(snp_source),
                    "source_urls": source_urls,
                    "conservation_score": str(conservation_score),
                    "gene_name": str(gene_name),
                    "gene_link": str(gene_link),
                    "transcript": str(transcript),
                    "transcript_link": str(transcript_link),
                    "exon": str(exon),
                    "domain_1": str(domain_1),
                    "domain_2": str(domain_2),
                    "function": str(function),
                    "function_details": str(function_details),
                    "allele_value_list": the_bases
                }

            elif self.variant_type == "InDel":
                indel_name, indel_chr, indel_mb_s, indel_mb_e, indel_strand, indel_type, indel_size, indel_sequence, source_name = result
                this_row = {
                    "index": i,
                    "indel_name": str(indel_name),
                    "indel_chr": str(indel_chr),
                    "indel_mb_s": str(indel_mb_s),
                    "indel_mb_e": str(indel_mb_e),
                    "indel_strand": str(indel_strand),
                    "indel_type": str(indel_type),
                    "indel_size": str(indel_size),
                    "indel_sequence": str(indel_sequence),
                    "source_name": str(source_name)
                }
                #this_row = [indel_name, indel_chr, indel_mb_s, indel_mb_e, indel_strand, indel_type, indel_size, indel_sequence, source_name]
            else:
                this_row = {}

            the_rows.append(this_row)

        return the_rows
                

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
                if self.function != "All":
                    if function.startswith(self.function):
                        function_satisfied = True
                else:
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
                if item and isinstance(item, basestring) and (item.lower() not in this_allele_list) and (item != "-"):
                    this_allele_list.append(item.lower())

            total_allele_count = len(this_allele_list)
            if total_allele_count <= 1:
                different_alleles_satisfied = False
            else:
                different_alleles_satisfied = True
        else:
            different_alleles_satisfied = True

        return domain_satisfied and function_satisfied and source_satisfied and score_satisfied and different_alleles_satisfied

    def snp_density_map(self, query, results):

        canvas_width = 900
        canvas_height = 200
        snp_canvas = pid.PILCanvas(size=(canvas_width, canvas_height))
        left_offset, right_offset, top_offset, bottom_offset = (30, 30, 40, 50)
        plot_width = canvas_width - left_offset - right_offset
        plot_height = canvas_height - top_offset - bottom_offset
        y_zero = top_offset + plot_height/2

        x_scale = plot_width/(self.end_mb - self.start_mb)

        #draw clickable image map at some point

        n_click = 80.0
        click_step = plot_width/n_click
        click_mb_step = (self.end_mb - self.start_mb)/n_click

        #for i in range(n_click):
        #    href = url_for('snp_browser', first_run="false", chosen_strains_mouse=self.chosen_strains_mouse, chosen_strains_rat=self.chosen_strains_rat, variant=self.variant_type, species=self.species_name, gene_name=self.gene_name, chr=self.chr, start_mb=self.start_mb, end_mb=self.end_mb, limit_strains=self.limit_strains, domain=self.domain, function=self.function, criteria=self.criteria, score=self.score, diff_alleles=self.diff_alleles)

def get_browser_sample_lists(species_id=1):
    strain_lists = {}
    mouse_strain_list = []
    query = "SHOW COLUMNS FROM SnpPattern;"
    results = g.db.execute(query).fetchall();
    for result in results[1:]:
        mouse_strain_list.append(result[0])

    rat_strain_list = []
    query = "SHOW COLUMNS FROM RatSnpPattern;"
    results = g.db.execute(query).fetchall();
    for result in results[2:]:
        rat_strain_list.append(result[0])

    strain_lists['mouse'] = mouse_strain_list
    strain_lists['rat'] = rat_strain_list

    return strain_lists

def get_header_list(variant_type, strains, species = None, empty_columns = None):
    if species == "Mouse":
        strain_list = strains['mouse']
    elif species == "Rat":
        strain_list = strains['rat']
    else:
        strain_list = strains

    empty_field_count = 0 #ZS: This is an awkward way of letting the javascript know the index where the allele value columns start; there's probably a better way of doing this

    header_fields = []
    if variant_type == "SNP":
        header_fields.append(['Index', 'SNP ID', 'Chr', 'Mb', 'Alleles', 'Source', 'ConScore', 'Gene', 'Transcript', 'Exon', 'Domain 1', 'Domain 2', 'Function', 'Details'])
        header_fields.append(strain_list)

        if empty_columns != None:
            if empty_columns['snp_source'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Source')
            if empty_columns['conservation_score'] == "false":
                empty_field_count += 1
                header_fields[0].remove('ConScore')
            if empty_columns['gene_name'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Gene')
            if empty_columns['transcript'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Transcript')
            if empty_columns['exon'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Exon')
            if empty_columns['domain_2'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Domain 2')
            if empty_columns['function'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Function')
            if empty_columns['function_details'] == "false":
                empty_field_count += 1
                header_fields[0].remove('Details')

    elif variant_type == "InDel":
        header_fields = ['Index', 'ID', 'Type', 'InDel Chr', 'Mb Start', 'Mb End', 'Strand', 'Size', 'Sequence', 'Source']

    return header_fields, empty_field_count

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
    exon, non_synonymous_coding, synonymous_coding, start_gained, start_lost, stop_gained, stop_lost, unknown_effect_in_exon = effect_list[8:16]

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
                domain = "Nonsplice Site"
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

def get_gene_id(species_id, gene_name):
    query = """
                SELECT
                        geneId
                FROM
                        GeneList
                WHERE
                        SpeciesId = %s AND geneSymbol = '%s'
            """ % (species_id, gene_name)

    result = g.db.execute(query).fetchone()

    if len(result) > 0:
        return result
    else:
        return ""

def get_gene_id_name_dict(species_id, gene_name_list):
    gene_id_name_dict = {}
    if len(gene_name_list) == 0:
        return ""
    gene_name_str_list = ["'" + gene_name + "'" for gene_name in gene_name_list]
    gene_name_str = string.join(gene_name_str_list, ",")

    query = """
                SELECT
                        geneId, geneSymbol
                FROM
                        GeneList
                WHERE
                        SpeciesId = %s AND geneSymbol in (%s)
            """ % (species_id, gene_name_str)

    results = g.db.execute(query).fetchall()

    if len(results) > 0:
        for item in results:
            gene_id_name_dict[item[1]] = item[0]
    else:
        pass

    return gene_id_name_dict

def check_if_in_gene(species_id, chr, mb):
    if species_id != 0: #ZS: Check if this is necessary
        query = """SELECT geneId, geneSymbol
                   FROM GeneList
                   WHERE SpeciesId = {0} AND chromosome = '{1}' AND
                        (txStart < {2} AND txEnd > {2}); """.format(species_id, chr, mb)
    else:
        query = """SELECT geneId,geneSymbol
                   FROM GeneList
                   WHERE chromosome = '{0}' AND
                        (txStart < {1} AND txEnd > {1}); """.format(species_id, chr, mb)

    result = g.db.execute(query).fetchone()

    if result:
        return [result[0], result[1]]
    else:
        return ""

