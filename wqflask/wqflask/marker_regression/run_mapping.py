from base.trait import GeneralTrait
from base import data_set  # import create_dataset

from pprint import pformat as pf

import string
import math
from decimal import Decimal
import random
import sys
import datetime
import os
import collections
import uuid

import numpy as np

import pickle as pickle
import itertools

import simplejson as json

from redis import Redis
Redis = Redis()

from flask import Flask, g

from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from utility import webqtlUtil
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data
from utility.benchmark import Bench
from wqflask.marker_regression import gemma_mapping, rqtl_mapping, qtlreaper_mapping, plink_mapping
from wqflask.show_trait.SampleList import SampleList

from utility.tools import locate, locate_ignore_error, GEMMA_COMMAND, PLINK_COMMAND, TEMPDIR
from utility.external import shell
from base.webqtlConfig import TMPDIR, GENERATED_TEXT_DIR

import utility.logger
logger = utility.logger.getLogger(__name__)


class RunMapping:

    def __init__(self, start_vars, temp_uuid):
        helper_functions.get_species_dataset_trait(self, start_vars)

        # needed to pass temp_uuid to gn1 mapping code (marker_regression_gn1.py)
        self.temp_uuid = temp_uuid

        # ZS: Needed to zoom in or remap temp traits like PCA traits
        if "temp_trait" in start_vars and start_vars['temp_trait'] != "False":
            self.temp_trait = "True"
            self.group = self.dataset.group.name

        self.json_data = {}
        self.json_data['lodnames'] = ['lod.hk']

        # ZS: Sometimes a group may have a genofile that only includes a subset of samples
        genofile_samplelist = []
        if 'genofile' in start_vars:
            if start_vars['genofile'] != "":
                self.genofile_string = start_vars['genofile']
                self.dataset.group.genofile = self.genofile_string.split(":")[
                    0]
                genofile_samplelist = get_genofile_samplelist(self.dataset)

        all_samples_ordered = self.dataset.group.all_samples_ordered()

        self.vals = []
        self.samples = []
        self.sample_vals = start_vars['sample_vals']
        sample_val_dict = json.loads(self.sample_vals)
        samples = sample_val_dict.keys()
        if (len(genofile_samplelist) != 0):
            for sample in genofile_samplelist:
                self.samples.append(sample)
                if sample in samples:
                    self.vals.append(sample_val_dict[sample])
                else:
                    self.vals.append("x")
        else:
            for sample in self.dataset.group.samplelist:
                if sample in samples:
                    self.vals.append(sample_val_dict[sample])
                    self.samples.append(sample)

        if 'n_samples' in start_vars:
            self.n_samples = start_vars['n_samples']
        else:
            self.n_samples = len([val for val in self.vals if val != "x"])

        # ZS: Check if genotypes exist in the DB in order to create links for markers

        self.geno_db_exists = geno_db_exists(self.dataset)

        self.mapping_method = start_vars['method']
        if "results_path" in start_vars:
            self.mapping_results_path = start_vars['results_path']
        else:
            mapping_results_filename = self.dataset.group.name + "_" + \
                ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(6))
            self.mapping_results_path = "{}{}.csv".format(
                webqtlConfig.GENERATED_IMAGE_DIR, mapping_results_filename)

        self.manhattan_plot = False
        if 'manhattan_plot' in start_vars:
            if start_vars['manhattan_plot'].lower() != "false":
                self.color_scheme = "alternating"
                if "color_scheme" in start_vars:
                    self.color_scheme = start_vars['color_scheme']
                    if self.color_scheme == "single":
                        self.manhattan_single_color = start_vars['manhattan_single_color']
                self.manhattan_plot = True

        self.maf = start_vars['maf']  # Minor allele frequency
        if "use_loco" in start_vars:
            self.use_loco = start_vars['use_loco']
        else:
            self.use_loco = None
        self.suggestive = ""
        self.significant = ""
        # Initializing this since it is checked in views to determine which template to use
        self.pair_scan = False
        if 'transform' in start_vars:
            self.transform = start_vars['transform']
        else:
            self.transform = ""
        self.score_type = "LRS"  # ZS: LRS or LOD
        self.mapping_scale = "physic"
        if "mapping_scale" in start_vars:
            self.mapping_scale = start_vars['mapping_scale']
        self.num_perm = 0
        self.perm_output = []
        self.bootstrap_results = []
        self.covariates = start_vars['covariates'] if "covariates" in start_vars else ""
        self.categorical_vars = []

        # ZS: This is passed to GN1 code for single chr mapping
        self.selected_chr = -1
        if "selected_chr" in start_vars:
            # ZS: Needs to be -1 if showing full map; there's probably a better way to fix this
            if int(start_vars['selected_chr']) != -1:
                self.selected_chr = int(start_vars['selected_chr']) + 1
            else:
                self.selected_chr = int(start_vars['selected_chr'])
        if "startMb" in start_vars:
            self.startMb = start_vars['startMb']
        if "endMb" in start_vars:
            self.endMb = start_vars['endMb']
        if "graphWidth" in start_vars:
            self.graphWidth = start_vars['graphWidth']
        if "lrsMax" in start_vars:
            self.lrsMax = start_vars['lrsMax']
        if "haplotypeAnalystCheck" in start_vars:
            self.haplotypeAnalystCheck = start_vars['haplotypeAnalystCheck']
        if "startMb" in start_vars:  # ZS: This is to ensure showGenes, Legend, etc are checked the first time you open the mapping page, since startMb will only not be set during the first load
            if "permCheck" in start_vars:
                self.permCheck = "ON"
            else:
                self.permCheck = False
            self.num_perm = int(start_vars['num_perm'])

            self.LRSCheck = start_vars['LRSCheck']

            if "showSNP" in start_vars:
                self.showSNP = start_vars['showSNP']
            else:
                self.showSNP = False

            if "showGenes" in start_vars:
                self.showGenes = start_vars['showGenes']
            else:
                self.showGenes = False

            if "viewLegend" in start_vars:
                self.viewLegend = start_vars['viewLegend']
            else:
                self.viewLegend = False
        else:
            try:
                if int(start_vars['num_perm']) > 0:
                    self.num_perm = int(start_vars['num_perm'])
            except:
                self.num_perm = 0

            if self.num_perm > 0:
                self.permCheck = "ON"
            else:
                self.permCheck = False
            self.showSNP = "ON"
            self.showGenes = "ON"
            self.viewLegend = "ON"

        # self.dataset.group.get_markers()
        if self.mapping_method == "gemma":
            self.first_run = True
            self.output_files = None
            if 'output_files' in start_vars:
                self.output_files = start_vars['output_files']
            # ZS: check if first run so existing result files can be used if it isn't (for example zooming on a chromosome, etc)
            if 'first_run' in start_vars:
                self.first_run = False
            self.score_type = "-logP"
            self.manhattan_plot = True
            with Bench("Running GEMMA"):
                if self.use_loco == "True":
                    marker_obs, self.output_files = gemma_mapping.run_gemma(
                        self.this_trait, self.dataset, self.samples, self.vals, self.covariates, self.use_loco, self.maf, self.first_run, self.output_files)
                else:
                    marker_obs, self.output_files = gemma_mapping.run_gemma(
                        self.this_trait, self.dataset, self.samples, self.vals, self.covariates, self.use_loco, self.maf, self.first_run, self.output_files)
            results = marker_obs
        elif self.mapping_method == "rqtl_plink":
            results = self.run_rqtl_plink()
        elif self.mapping_method == "rqtl_geno":
            perm_strata = []
            if "perm_strata" in start_vars and "categorical_vars" in start_vars:
                self.categorical_vars = start_vars["categorical_vars"].split(
                    ",")
                if len(self.categorical_vars) and start_vars["perm_strata"] == "True":
                    primary_samples = SampleList(dataset=self.dataset,
                                                 sample_names=self.samples,
                                                 this_trait=self.this_trait)

                    perm_strata = get_perm_strata(
                        self.this_trait, primary_samples, self.categorical_vars, self.samples)
            self.score_type = "LOD"
            self.control_marker = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            if 'mapmethod_rqtl_geno' in start_vars:
                self.method = start_vars['mapmethod_rqtl_geno']
            else:
                self.method = "em"
            self.model = start_vars['mapmodel_rqtl_geno']
            # if start_vars['pair_scan'] == "true":
            #    self.pair_scan = True
            if self.permCheck and self.num_perm > 0:
                self.perm_output, self.suggestive, self.significant, results = rqtl_mapping.run_rqtl(
                    self.this_trait.name, self.vals, self.samples, self.dataset, self.mapping_scale, self.model, self.method, self.num_perm, perm_strata, self.do_control, self.control_marker, self.manhattan_plot, self.covariates)
            else:
                results = rqtl_mapping.run_rqtl(self.this_trait.name, self.vals, self.samples, self.dataset, self.mapping_scale, self.model, self.method,
                                                     self.num_perm, perm_strata, self.do_control, self.control_marker, self.manhattan_plot, self.covariates)
        elif self.mapping_method == "reaper":
            if "startMb" in start_vars:  # ZS: Check if first time page loaded, so it can default to ON
                if "additiveCheck" in start_vars:
                    self.additiveCheck = start_vars['additiveCheck']
                else:
                    self.additiveCheck = False

                if "bootCheck" in start_vars:
                    self.bootCheck = "ON"
                else:
                    self.bootCheck = False
                self.num_bootstrap = int(start_vars['num_bootstrap'])
            else:
                self.additiveCheck = "ON"
                try:
                    if int(start_vars['num_bootstrap']) > 0:
                        self.bootCheck = "ON"
                        self.num_bootstrap = int(start_vars['num_bootstrap'])
                    else:
                        self.bootCheck = False
                        self.num_bootstrap = 0
                except:
                    self.bootCheck = False
                    self.num_bootstrap = 0

            self.reaper_version = start_vars['reaper_version']

            self.control_marker = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            logger.info("Running qtlreaper")

            if self.reaper_version == "new":
                self.first_run = True
                self.output_files = None
                # ZS: check if first run so existing result files can be used if it isn't (for example zooming on a chromosome, etc)
                if 'first_run' in start_vars:
                    self.first_run = False
                    if 'output_files' in start_vars:
                        self.output_files = start_vars['output_files'].split(
                            ",")

                results, self.perm_output, self.suggestive, self.significant, self.bootstrap_results, self.output_files = qtlreaper_mapping.run_reaper(self.this_trait,
                                                                                                                                                       self.dataset,
                                                                                                                                                       self.samples,
                                                                                                                                                       self.vals,
                                                                                                                                                       self.json_data,
                                                                                                                                                       self.num_perm,
                                                                                                                                                       self.bootCheck,
                                                                                                                                                       self.num_bootstrap,
                                                                                                                                                       self.do_control,
                                                                                                                                                       self.control_marker,
                                                                                                                                                       self.manhattan_plot,
                                                                                                                                                       self.first_run,
                                                                                                                                                       self.output_files)
            else:
                results, self.json_data, self.perm_output, self.suggestive, self.significant, self.bootstrap_results = qtlreaper_mapping.run_original_reaper(self.this_trait,
                                                                                                                                                             self.dataset,
                                                                                                                                                             self.samples,
                                                                                                                                                             self.vals,
                                                                                                                                                             self.json_data,
                                                                                                                                                             self.num_perm,
                                                                                                                                                             self.bootCheck,
                                                                                                                                                             self.num_bootstrap,
                                                                                                                                                             self.do_control,
                                                                                                                                                             self.control_marker,
                                                                                                                                                             self.manhattan_plot)
        elif self.mapping_method == "plink":
            self.score_type = "-logP"
            self.manhattan_plot = True
            results = plink_mapping.run_plink(
                self.this_trait, self.dataset, self.species, self.vals, self.maf)
            #results = self.run_plink()
        else:
            logger.debug("RUNNING NOTHING")

        self.no_results = False
        if len(results) == 0:
            self.no_results = True
        else:
            if self.pair_scan == True:
                self.qtl_results = []
                highest_chr = 1  # This is needed in order to convert the highest chr to X/Y
                for marker in results:
                    if marker['chr1'] > 0 or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                        if marker['chr1'] > highest_chr or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                            highest_chr = marker['chr1']
                        if 'lod_score' in list(marker.keys()):
                            self.qtl_results.append(marker)

                self.trimmed_markers = results

                for qtl in enumerate(self.qtl_results):
                    self.json_data['chr1'].append(str(qtl['chr1']))
                    self.json_data['chr2'].append(str(qtl['chr2']))
                    self.json_data['Mb'].append(qtl['Mb'])
                    self.json_data['markernames'].append(qtl['name'])

                self.js_data = dict(
                    json_data=self.json_data,
                    this_trait=self.this_trait.name,
                    data_set=self.dataset.name,
                    maf=self.maf,
                    manhattan_plot=self.manhattan_plot,
                    mapping_scale=self.mapping_scale,
                    qtl_results=self.qtl_results
                )

            else:
                self.qtl_results = []
                self.results_for_browser = []
                self.annotations_for_browser = []
                highest_chr = 1  # This is needed in order to convert the highest chr to X/Y
                for marker in results:
                    if 'Mb' in marker:
                        this_ps = marker['Mb'] * 1000000
                    else:
                        this_ps = marker['cM'] * 1000000

                    browser_marker = dict(
                        chr=str(marker['chr']),
                        rs=marker['name'],
                        ps=this_ps,
                        url="/show_trait?trait_id=" + \
                            marker['name'] + "&dataset=" + \
                        self.dataset.group.name + "Geno"
                    )

                    if self.geno_db_exists == "True":
                        annot_marker = dict(
                            name=str(marker['name']),
                            chr=str(marker['chr']),
                            rs=marker['name'],
                            pos=this_ps,
                            url="/show_trait?trait_id=" + \
                                marker['name'] + "&dataset=" + \
                            self.dataset.group.name + "Geno"
                        )
                    else:
                        annot_marker = dict(
                            name=str(marker['name']),
                            chr=str(marker['chr']),
                            rs=marker['name'],
                            pos=this_ps
                        )

                    if 'lrs_value' in marker and marker['lrs_value'] > 0:
                        browser_marker['p_wald'] = 10**- \
                            (marker['lrs_value'] / 4.61)
                    elif 'lod_score' in marker and marker['lod_score'] > 0:
                        browser_marker['p_wald'] = 10**-(marker['lod_score'])
                    else:
                        browser_marker['p_wald'] = 0

                    self.results_for_browser.append(browser_marker)
                    self.annotations_for_browser.append(annot_marker)
                    if str(marker['chr']) > '0' or str(marker['chr']) == "X" or str(marker['chr']) == "X/Y":
                        if str(marker['chr']) > str(highest_chr) or str(marker['chr']) == "X" or str(marker['chr']) == "X/Y":
                            highest_chr = marker['chr']
                        if ('lod_score' in marker.keys()) or ('lrs_value' in marker.keys()):
                            if 'Mb' in marker.keys():
                                marker['display_pos'] = "Chr" + \
                                    str(marker['chr']) + ": " + \
                                    "{:.6f}".format(marker['Mb'])
                            elif 'cM' in marker.keys():
                                marker['display_pos'] = "Chr" + \
                                    str(marker['chr']) + ": " + \
                                    "{:.3f}".format(marker['cM'])
                            else:
                                marker['display_pos'] = "N/A"
                            self.qtl_results.append(marker)

                total_markers = len(self.qtl_results)

                with Bench("Exporting Results"):
                    export_mapping_results(self.dataset, self.this_trait, self.qtl_results, self.mapping_results_path,
                                           self.mapping_scale, self.score_type, self.transform, self.covariates, self.n_samples)

                with Bench("Trimming Markers for Figure"):
                    if len(self.qtl_results) > 30000:
                        self.qtl_results = trim_markers_for_figure(
                            self.qtl_results)
                        self.results_for_browser = trim_markers_for_figure(
                            self.results_for_browser)
                        filtered_annotations = []
                        for marker in self.results_for_browser:
                            for annot_marker in self.annotations_for_browser:
                                if annot_marker['rs'] == marker['rs']:
                                    filtered_annotations.append(annot_marker)
                                    break
                        self.annotations_for_browser = filtered_annotations
                        browser_files = write_input_for_browser(
                            self.dataset, self.results_for_browser, self.annotations_for_browser)
                    else:
                        browser_files = write_input_for_browser(
                            self.dataset, self.results_for_browser, self.annotations_for_browser)

                with Bench("Trimming Markers for Table"):
                    self.trimmed_markers = trim_markers_for_table(results)

                chr_lengths = get_chr_lengths(
                    self.mapping_scale, self.mapping_method, self.dataset, self.qtl_results)

                # ZS: For zooming into genome browser, need to pass chromosome name instead of number
                if self.dataset.group.species == "mouse":
                    if self.selected_chr == 20:
                        this_chr = "X"
                    else:
                        this_chr = str(self.selected_chr)
                elif self.dataset.group.species == "rat":
                    if self.selected_chr == 21:
                        this_chr = "X"
                    else:
                        this_chr = str(self.selected_chr)
                else:
                    if self.selected_chr == 22:
                        this_chr = "X"
                    elif self.selected_chr == 23:
                        this_chr = "Y"
                    else:
                        this_chr = str(self.selected_chr)

                if self.mapping_method != "gemma":
                    if self.score_type == "LRS":
                        significant_for_browser = self.significant / 4.61
                    else:
                        significant_for_browser = self.significant

                    self.js_data = dict(
                        #result_score_type = self.score_type,
                        #this_trait = self.this_trait.name,
                        #data_set = self.dataset.name,
                        #maf = self.maf,
                        #manhattan_plot = self.manhattan_plot,
                        #mapping_scale = self.mapping_scale,
                        #chromosomes = chromosome_mb_lengths,
                        #qtl_results = self.qtl_results,
                        categorical_vars=self.categorical_vars,
                        chr_lengths=chr_lengths,
                        num_perm=self.num_perm,
                        perm_results=self.perm_output,
                        significant=significant_for_browser,
                        browser_files=browser_files,
                        selected_chr=this_chr,
                        total_markers=total_markers
                    )
                else:
                    self.js_data = dict(
                        chr_lengths=chr_lengths,
                        browser_files=browser_files,
                        selected_chr=this_chr,
                        total_markers=total_markers
                    )

    def run_rqtl_plink(self):
        # os.chdir("") never do this inside a webserver!!

        output_filename = webqtlUtil.genRandStr("%s_%s_" % (
            self.dataset.group.name, self.this_trait.name))

        plink_mapping.gen_pheno_txt_file_plink(
            self.this_trait, self.dataset, self.vals, pheno_filename=output_filename)

        rqtl_command = './plink --noweb --ped %s.ped --no-fid --no-parents --no-sex --no-pheno --map %s.map --pheno %s/%s.txt --pheno-name %s --maf %s --missing-phenotype -9999 --out %s%s --assoc ' % (
            self.dataset.group.name, self.dataset.group.name, TMPDIR, plink_output_filename, self.this_trait.name, self.maf, TMPDIR, plink_output_filename)

        os.system(rqtl_command)

        count, p_values = self.parse_rqtl_output(plink_output_filename)

    def identify_empty_samples(self):
        no_val_samples = []
        for sample_count, val in enumerate(self.vals):
            if val == "x":
                no_val_samples.append(sample_count)
        return no_val_samples

    def trim_genotypes(self, genotype_data, no_value_samples):
        trimmed_genotype_data = []
        for marker in genotype_data:
            new_genotypes = []
            for item_count, genotype in enumerate(marker):
                if item_count in no_value_samples:
                    continue
                try:
                    genotype = float(genotype)
                except ValueError:
                    genotype = np.nan
                    pass
                new_genotypes.append(genotype)
            trimmed_genotype_data.append(new_genotypes)
        return trimmed_genotype_data


def export_mapping_results(dataset, trait, markers, results_path, mapping_scale, score_type, transform, covariates, n_samples):
    with open(results_path, "w+") as output_file:
        output_file.write(
            "Time/Date: " + datetime.datetime.now().strftime("%x / %X") + "\n")
        output_file.write(
            "Population: " + dataset.group.species.title() + " " + dataset.group.name + "\n")
        output_file.write("Data Set: " + dataset.fullname + "\n")
        output_file.write("N Samples: " + str(n_samples) + "\n")
        if len(transform) > 0:
            transform_text = "Transform - "
            if transform == "qnorm":
                transform_text += "Quantile Normalized"
            elif transform == "log2" or transform == "log10":
                transform_text += transform.capitalize()
            elif transform == "sqrt":
                transform_text += "Square Root"
            elif transform == "zscore":
                transform_text += "Z-Score"
            elif transform == "invert":
                transform_text += "Invert +/-"
            else:
                transform_text = ""
            output_file.write(transform_text + "\n")
        if dataset.type == "ProbeSet":
            output_file.write("Gene Symbol: " + trait.symbol + "\n")
            output_file.write("Location: " + str(trait.chr) + \
                              " @ " + str(trait.mb) + " Mb\n")
        if len(covariates) > 0:
            output_file.write("Cofactors (dataset - trait):\n")
            for covariate in covariates.split(","):
                trait_name = covariate.split(":")[0]
                dataset_name = covariate.split(":")[1]
                output_file.write(dataset_name + " - " + trait_name + "\n")
        output_file.write("\n")
        output_file.write("Name,Chr,")
        if score_type.lower() == "-logP":
            score_type = "-logP"
        if 'Mb' in markers[0]:
            output_file.write("Mb," + score_type)
        if 'cM' in markers[0]:
            output_file.write("Cm," + score_type)
        if "additive" in list(markers[0].keys()):
            output_file.write(",Additive")
        if "dominance" in list(markers[0].keys()):
            output_file.write(",Dominance")
        output_file.write("\n")
        for i, marker in enumerate(markers):
            output_file.write(marker['name'] + "," + str(marker['chr']) + ",")
            if 'Mb' in marker:
                output_file.write(str(marker['Mb']) + ",")
            if 'cM' in marker:
                output_file.write(str(marker['cM']) + ",")
            if "lod_score" in marker.keys():
                output_file.write(str(marker['lod_score']))
            else:
                output_file.write(str(marker['lrs_value']))
            if "additive" in list(marker.keys()):
                output_file.write("," + str(marker['additive']))
            if "dominance" in list(marker.keys()):
                output_file.write("," + str(marker['dominance']))
            if i < (len(markers) - 1):
                output_file.write("\n")


def trim_markers_for_figure(markers):
    if 'p_wald' in list(markers[0].keys()):
        score_type = 'p_wald'
    elif 'lod_score' in list(markers[0].keys()):
        score_type = 'lod_score'
    else:
        score_type = 'lrs_value'

    filtered_markers = []
    low_counter = 0
    med_counter = 0
    high_counter = 0
    for marker in markers:
        if score_type == 'p_wald':
            if marker[score_type] > 0.1:
                if low_counter % 20 == 0:
                    filtered_markers.append(marker)
                low_counter += 1
            elif 0.1 >= marker[score_type] > 0.01:
                if med_counter % 10 == 0:
                    filtered_markers.append(marker)
                med_counter += 1
            elif 0.01 >= marker[score_type] > 0.001:
                if high_counter % 2 == 0:
                    filtered_markers.append(marker)
                high_counter += 1
            else:
                filtered_markers.append(marker)
        elif score_type == 'lod_score':
            if marker[score_type] < 1:
                if low_counter % 20 == 0:
                    filtered_markers.append(marker)
                low_counter += 1
            elif 1 <= marker[score_type] < 2:
                if med_counter % 10 == 0:
                    filtered_markers.append(marker)
                med_counter += 1
            elif 2 <= marker[score_type] <= 3:
                if high_counter % 2 == 0:
                    filtered_markers.append(marker)
                high_counter += 1
            else:
                filtered_markers.append(marker)
        else:
            if marker[score_type] < 4.61:
                if low_counter % 20 == 0:
                    filtered_markers.append(marker)
                low_counter += 1
            elif 4.61 <= marker[score_type] < (2 * 4.61):
                if med_counter % 10 == 0:
                    filtered_markers.append(marker)
                med_counter += 1
            elif (2 * 4.61) <= marker[score_type] <= (3 * 4.61):
                if high_counter % 2 == 0:
                    filtered_markers.append(marker)
                high_counter += 1
            else:
                filtered_markers.append(marker)
    return filtered_markers


def trim_markers_for_table(markers):
    if 'lod_score' in list(markers[0].keys()):
        sorted_markers = sorted(
            markers, key=lambda k: k['lod_score'], reverse=True)
    else:
        sorted_markers = sorted(
            markers, key=lambda k: k['lrs_value'], reverse=True)

    # ZS: So we end up with a list of just 2000 markers
    if len(sorted_markers) >= 2000:
        trimmed_sorted_markers = sorted_markers[:2000]
        return trimmed_sorted_markers
    else:
        return sorted_markers


def write_input_for_browser(this_dataset, gwas_results, annotations):
    file_base = this_dataset.group.name + "_" + \
        ''.join(random.choice(string.ascii_uppercase + string.digits)
                for _ in range(6))
    gwas_filename = file_base + "_GWAS"
    annot_filename = file_base + "_ANNOT"
    gwas_path = "{}/gn2/".format(TEMPDIR) + gwas_filename
    annot_path = "{}/gn2/".format(TEMPDIR) + annot_filename

    with open(gwas_path + ".json", "w") as gwas_file, open(annot_path + ".json", "w") as annot_file:
        gwas_file.write(json.dumps(gwas_results))
        annot_file.write(json.dumps(annotations))

    return [gwas_filename, annot_filename]


def geno_db_exists(this_dataset):
    geno_db_name = this_dataset.group.name + "Geno"
    try:
        geno_db = data_set.create_dataset(
            dataset_name=geno_db_name, get_samplelist=False)
        return "True"
    except:
        return "False"


def get_chr_lengths(mapping_scale, mapping_method, dataset, qtl_results):
    chr_lengths = []
    if mapping_scale == "physic":
        for i, the_chr in enumerate(dataset.species.chromosomes.chromosomes):
            this_chr = {
                "chr": dataset.species.chromosomes.chromosomes[the_chr].name,
                "size": str(dataset.species.chromosomes.chromosomes[the_chr].length)
            }
            chr_lengths.append(this_chr)
    else:
        this_chr = 1
        highest_pos = 0
        for i, result in enumerate(qtl_results):
            chr_as_num = 0
            try:
                chr_as_num = int(result['chr'])
            except:
                chr_as_num = 20
            if chr_as_num > this_chr or i == (len(qtl_results) - 1):
                if i == (len(qtl_results) - 1):
                    if mapping_method == "reaper":
                        highest_pos = float(result['cM']) * 1000000
                    else:
                        highest_pos = float(result['Mb']) * 1000000
                    chr_lengths.append(
                        {"chr": str(this_chr), "size": str(highest_pos)})
                else:
                    chr_lengths.append(
                        {"chr": str(this_chr), "size": str(highest_pos)})
                    this_chr = chr_as_num
            else:
                if mapping_method == "reaper":
                    if float(result['cM']) > highest_pos:
                        highest_pos = float(result['cM']) * 1000000
                else:
                    if float(result['Mb']) > highest_pos:
                        highest_pos = float(result['Mb']) * 1000000

    return chr_lengths


def get_genofile_samplelist(dataset):
    genofile_samplelist = []

    genofile_json = dataset.group.get_genofiles()
    for genofile in genofile_json:
        if genofile['location'] == dataset.group.genofile and 'sample_list' in genofile:
            genofile_samplelist = genofile['sample_list']

    return genofile_samplelist


def get_perm_strata(this_trait, sample_list, categorical_vars, used_samples):
    perm_strata_strings = []
    for sample in used_samples:
        if sample in list(sample_list.sample_attribute_values.keys()):
            combined_string = ""
            for var in categorical_vars:
                if var.lower() in sample_list.sample_attribute_values[sample]:
                    combined_string += str(
                        sample_list.sample_attribute_values[sample][var.lower()])
                else:
                    combined_string += "NA"
        else:
            combined_string = "NA"

        perm_strata_strings.append(combined_string)

    d = dict([(y, x + 1)
              for x, y in enumerate(sorted(set(perm_strata_strings)))])
    list_to_numbers = [d[x] for x in perm_strata_strings]
    perm_strata = list_to_numbers

    return perm_strata
