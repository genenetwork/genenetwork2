"Dataset Group class ..."

import os
import json


from base import webqtlConfig
from utility import webqtlUtil
from utility import gen_geno_ob
from db import webqtlDatabaseFunction
from maintenance import get_group_samplelists
from wqflask.database import database_connection
from utility.tools import (
    locate,
    USE_REDIS,
    flat_files,
    flat_file_exists,
    locate_ignore_error)

class DatasetGroup:
    """
    Each group has multiple datasets; each species has multiple groups.

    For example, Mouse has multiple groups (BXD, BXA, etc), and each group
    has multiple datasets associated with it.

    """

    def __init__(self, dataset, name=None):
        """This sets self.group and self.group_id"""
        with database_connection() as conn, conn.cursor() as cursor:
            if not name:
                cursor.execute(dataset.query_for_group,
                               (dataset.name,))
            else:
                cursor.execute(
                    "SELECT InbredSet.Name, "
                    "InbredSet.Id, "
                    "InbredSet.GeneticType, "
                    "InbredSet.InbredSetCode "
                    "FROM InbredSet WHERE Name = %s",
                    (dataset.name,))
            results = cursor.fetchone()
            if results:
                (self.name, self.id, self.genetic_type, self.code) = results
            else:
                self.name = name or dataset.name
        if self.name == 'BXD300':
            self.name = "BXD"

        self.f1list = None
        self.parlist = None
        self.get_f1_parent_strains()

        self.mapping_id, self.mapping_names = self.get_mapping_methods()

        self.species = webqtlDatabaseFunction.retrieve_species(self.name)

        self.incparentsf1 = False
        self.allsamples = None
        self._datasets = None
        self.genofile = None

    def get_mapping_methods(self):
        mapping_id = ()
        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT MappingMethodId FROM "
                "InbredSet WHERE Name= %s",
                (self.name,))
            results = cursor.fetchone()
            if results and results[0]:
                mapping_id = results[0]
        if mapping_id == "1":
            mapping_names = ["GEMMA", "QTLReaper", "R/qtl"]
        elif mapping_id == "2":
            mapping_names = ["GEMMA"]
        elif mapping_id == "3":
            mapping_names = ["R/qtl"]
        elif mapping_id == "4":
            mapping_names = ["GEMMA", "PLINK"]
        else:
            mapping_names = []

        return mapping_id, mapping_names

    def get_markers(self):
        def check_plink_gemma():
            if flat_file_exists("mapping"):
                MAPPING_PATH = flat_files("mapping") + "/"
                if os.path.isfile(MAPPING_PATH + self.name + ".bed"):
                    return True
            return False

        if check_plink_gemma():
            marker_class = HumanMarkers
        else:
            marker_class = Markers

        if self.genofile:
            self.markers = marker_class(self.genofile[:-5])
        else:
            self.markers = marker_class(self.name)

    def get_f1_parent_strains(self):
        try:
            # NL, 07/27/2010. ParInfo has been moved from webqtlForm.py to webqtlUtil.py;
            f1, f12, maternal, paternal = webqtlUtil.ParInfo[self.name]
        except KeyError:
            f1 = f12 = maternal = paternal = None

        if f1 and f12:
            self.f1list = [f1, f12]
        if maternal and paternal:
            self.parlist = [maternal, paternal]

    def get_study_samplelists(self):
        study_sample_file = locate_ignore_error(
            self.name + ".json", 'study_sample_lists')
        try:
            f = open(study_sample_file)
        except:
            return []
        study_samples = json.load(f)
        return study_samples

    def get_genofiles(self):
        jsonfile = "%s/%s.json" % (webqtlConfig.GENODIR, self.name)
        try:
            f = open(jsonfile)
        except:
            return None
        jsondata = json.load(f)
        return jsondata['genofile']

    def get_samplelist(self, redis_conn):
        result = None
        key = "samplelist:v3:" + self.name
        if USE_REDIS:
            result = redis_conn.get(key)

        if result is not None:
            self.samplelist = json.loads(result)
        else:
            genotype_fn = locate_ignore_error(self.name + ".geno", 'genotype')
            if genotype_fn:
                self.samplelist = get_group_samplelists.get_samplelist(
                    "geno", genotype_fn)
            else:
                self.samplelist = None

            if USE_REDIS:
                redis_conn.set(key, json.dumps(self.samplelist))
                redis_conn.expire(key, 60 * 5)

    def all_samples_ordered(self):
        result = []
        lists = (self.parlist, self.f1list, self.samplelist)
        [result.extend(l) for l in lists if l]
        return result

    def read_genotype_file(self, use_reaper=False):
        '''Read genotype from .geno file instead of database'''
        # genotype_1 is Dataset Object without parents and f1
        # genotype_2 is Dataset Object with parents and f1 (not for intercross)

        # reaper barfs on unicode filenames, so here we ensure it's a string
        if self.genofile:
            if "RData" in self.genofile:  # ZS: This is a temporary fix; I need to change the way the JSON files that point to multiple genotype files are structured to point to other file types like RData
                full_filename = str(
                    locate(self.genofile.split(".")[0] + ".geno", 'genotype'))
            else:
                full_filename = str(locate(self.genofile, 'genotype'))
        else:
            full_filename = str(locate(self.name + '.geno', 'genotype'))
        genotype_1 = gen_geno_ob.genotype(full_filename)

        if genotype_1.type == "group" and self.parlist:
            genotype_2 = genotype_1.add(
                Mat=self.parlist[0], Pat=self.parlist[1])  # , F1=_f1)
        else:
            genotype_2 = genotype_1

        # determine default genotype object
        if self.incparentsf1 and genotype_1.type != "intercross":
            genotype = genotype_2
        else:
            self.incparentsf1 = 0
            genotype = genotype_1

        self.samplelist = list(genotype.prgy)

        return genotype
