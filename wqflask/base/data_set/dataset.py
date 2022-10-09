"Base Dataset class ..."

import math
import collections
import itertools

from redis import Redis

from MySQLdb.cursors import DictCursor
from base import species
from utility import chunks
from gn3.monads import MonadicDict, query_sql
from pymonad.maybe import Maybe, Nothing
from .datasetgroup import DatasetGroup
from wqflask.database import database_connection
from utility.db_tools import escape, mescape, create_in_clause
from .utils import fetch_cached_results, cache_dataset_results

class DataSet:
    """
    DataSet class defines a dataset in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input dataset(temp)

    """

    def __init__(self, name, get_samplelist=True, group_name=None, redis_conn=Redis()):

        assert name, "Need a name"
        self.name = name
        self.id = None
        self.shortname = None
        self.fullname = None
        self.type = None
        self.data_scale = None  # ZS: For example log2
        self.accession_id = Nothing

        self.setup()

        if self.type == "Temp":  # Need to supply group name as input if temp trait
            # sets self.group and self.group_id and gets genotype
            self.group = DatasetGroup(self, name=group_name)
        else:
            self.check_confidentiality()
            self.retrieve_other_names()
            # sets self.group and self.group_id and gets genotype
            self.group = DatasetGroup(self)
            self.accession_id = self.get_accession_id()
        if get_samplelist == True:
            self.group.get_samplelist(redis_conn)
        self.species = species.TheSpecies(dataset=self)

    def as_monadic_dict(self):
        _result = MonadicDict({
            'name': self.name,
            'shortname': self.shortname,
            'fullname': self.fullname,
            'type': self.type,
            'data_scale': self.data_scale,
            'group': self.group.name
        })
        _result["accession_id"] = self.accession_id
        return _result

    def get_accession_id(self) -> Maybe[str]:
        """Get the accession_id of this dataset depending on the
        dataset type."""
        __accession_id_dict = MonadicDict()
        with database_connection() as conn:
            if self.type == "Publish":
                __accession_id_dict, = itertools.islice(
                    query_sql(conn,
                        ("SELECT InfoFiles.GN_AccesionId AS accession_id FROM "
                        "InfoFiles, PublishFreeze, InbredSet "
                        f"WHERE InbredSet.Name = '{conn.escape_string(self.group.name).decode()}' "
                        "AND PublishFreeze.InbredSetId = InbredSet.Id "
                        "AND InfoFiles.InfoPageName = PublishFreeze.Name "
                        "AND PublishFreeze.public > 0 AND "
                        "PublishFreeze.confidentiality < 1 "
                        "ORDER BY PublishFreeze.CreateTime DESC")
                    ), 1)
            elif self.type == "Geno":
                __accession_id_dict, = itertools.islice(
                    query_sql(conn,
                        ("SELECT InfoFiles.GN_AccesionId AS accession_id FROM "
                        "InfoFiles, GenoFreeze, InbredSet "
                        f"WHERE InbredSet.Name = '{conn.escape_string(self.group.name).decode()}' AND "
                        "GenoFreeze.InbredSetId = InbredSet.Id "
                        "AND InfoFiles.InfoPageName = GenoFreeze.ShortName "
                        "AND GenoFreeze.public > 0 AND "
                        "GenoFreeze.confidentiality < 1 "
                        "ORDER BY GenoFreeze.CreateTime DESC")
                    ), 1)
            elif self.type == "ProbeSet":
                __accession_id_dict, = itertools.islice(
                    query_sql(conn,
                        ("SELECT InfoFiles.GN_AccesionId AS accession_id "
                        f"FROM InfoFiles WHERE InfoFiles.InfoPageName = '{conn.escape_string(self.name).decode()}' "
                        f"AND InfoFiles.DB_Name = '{conn.escape_string(self.fullname).decode()}' "
                        f"OR InfoFiles.DB_Name = '{conn.escape_string(self.shortname).decode()}'")
                    ), 1)
            else:  # The Value passed is not present
                raise LookupError
        return __accession_id_dict["accession_id"]

    def retrieve_other_names(self):
        """This method fetches the the dataset names in search_result.

        If the data set name parameter is not found in the 'Name' field of
        the data set table, check if it is actually the FullName or
        ShortName instead.

        This is not meant to retrieve the data set info if no name at
        all is passed.

        """
        with database_connection() as conn, conn.cursor() as cursor:
            try:
                if self.type == "ProbeSet":
                    cursor.execute(
                        "SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, "
                        "ProbeSetFreeze.FullName, ProbeSetFreeze.ShortName, "
                        "ProbeSetFreeze.DataScale, Tissue.Name "
                        "FROM ProbeSetFreeze, ProbeFreeze, Tissue "
                        "WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                        "AND ProbeFreeze.TissueId = Tissue.Id "
                        "AND (ProbeSetFreeze.Name = %s OR "
                        "ProbeSetFreeze.FullName = %s "
                        "OR ProbeSetFreeze.ShortName = %s)",
                        (self.name,)*3)
                    (self.id, self.name, self.fullname, self.shortname,
                    self.data_scale, self.tissue) = cursor.fetchone()
                else:
                    self.tissue = "N/A"
                    cursor.execute(
                        "SELECT Id, Name, FullName, ShortName "
                        f"FROM {self.type}Freeze "
                        "WHERE (Name = %s OR FullName = "
                        "%s OR ShortName = %s)",
                        (self.name,)*3)
                    (self.id, self.name, self.fullname,
                    self.shortname) = cursor.fetchone()
            except TypeError:
                pass

    def chunk_dataset(self, dataset, n):

        results = {}
        traits_name_dict = ()
        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT ProbeSetXRef.DataId,ProbeSet.Name "
                "FROM ProbeSet, ProbeSetXRef, ProbeSetFreeze "
                "WHERE ProbeSetFreeze.Name = %s AND "
                "ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
                "AND ProbeSetXRef.ProbeSetId = ProbeSet.Id",
                (self.name,))
            # should cache this
            traits_name_dict = dict(cursor.fetchall())

        for i in range(0, len(dataset), n):
            matrix = list(dataset[i:i + n])
            trait_name = traits_name_dict[matrix[0][0]]

            my_values = [value for (trait_name, strain, value) in matrix]
            results[trait_name] = my_values
        return results

    def get_probeset_data(self, sample_list=None, trait_ids=None):

        # improvement of get trait data--->>>
        if sample_list:
            self.samplelist = sample_list

        else:
            self.samplelist = self.group.samplelist

        if self.group.parlist != None and self.group.f1list != None:
            if (self.group.parlist + self.group.f1list) in self.samplelist:
                self.samplelist += self.group.parlist + self.group.f1list
        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT Strain.Name, Strain.Id FROM "
                "Strain, Species WHERE Strain.Name IN "
                f"{create_in_clause(self.samplelist)} "
                "AND Strain.SpeciesId=Species.Id AND "
                "Species.name = %s", (self.group.species,)
            )
            results = dict(cursor.fetchall())
            sample_ids = [results[item] for item in self.samplelist]

            sorted_samplelist = [strain_name for strain_name, strain_id in sorted(
                results.items(), key=lambda item: item[1])]

            cursor.execute(
                "SELECT * from ProbeSetData WHERE StrainID IN "
                f"{create_in_clause(sample_ids)} AND id IN "
                "(SELECT ProbeSetXRef.DataId FROM "
                "(ProbeSet, ProbeSetXRef, ProbeSetFreeze) "
                "WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id "
                "AND ProbeSetFreeze.Name = %s AND "
                "ProbeSet.Id = ProbeSetXRef.ProbeSetId)",
                (self.name,)
            )

            query_results = list(cursor.fetchall())
            data_results = self.chunk_dataset(query_results, len(sample_ids))
            self.samplelist = sorted_samplelist
            self.trait_data = data_results

    def get_trait_data(self, sample_list=None):
        if sample_list:
            self.samplelist = sample_list
        else:
            self.samplelist = self.group.samplelist

        if self.group.parlist != None and self.group.f1list != None:
            if (self.group.parlist + self.group.f1list) in self.samplelist:
                self.samplelist += self.group.parlist + self.group.f1list

        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT Strain.Name, Strain.Id FROM Strain, Species "
                f"WHERE Strain.Name IN {create_in_clause(self.samplelist)} "
                "AND Strain.SpeciesId=Species.Id "
                "AND Species.name = %s",
                (self.group.species,)
            )
            results = dict(cursor.fetchall())
            sample_ids = [
                sample_id for sample_id in
                (results.get(item) for item in self.samplelist
                 if item is not None)
                if sample_id is not None
            ]

            # MySQL limits the number of tables that can be used in a join to 61,
            # so we break the sample ids into smaller chunks
            # Postgres doesn't have that limit, so we can get rid of this after we transition
            chunk_size = 50
            number_chunks = int(math.ceil(len(sample_ids) / chunk_size))

            cached_results = fetch_cached_results(self.name, self.type, self.samplelist)

            if cached_results is None:
                trait_sample_data = []
                for sample_ids_step in chunks.divide_into_chunks(sample_ids, number_chunks):
                    if self.type == "Publish":
                        dataset_type = "Phenotype"
                    else:
                        dataset_type = self.type
                    temp = ['T%s.value' % item for item in sample_ids_step]
                    if self.type == "Publish":
                        query = "SELECT {}XRef.Id".format(escape(self.type))
                    else:
                        query = "SELECT {}.Name".format(escape(dataset_type))
                    data_start_pos = 1
                    if len(temp) > 0:
                        query = query + ", " + ', '.join(temp)
                    query += ' FROM ({}, {}XRef, {}Freeze) '.format(*mescape(dataset_type,
                                                                             self.type,
                                                                             self.type))

                    for item in sample_ids_step:
                        query += """
                                left join {}Data as T{} on T{}.Id = {}XRef.DataId
                                and T{}.StrainId={}\n
                                """.format(*mescape(self.type, item, item, self.type, item, item))

                    if self.type == "Publish":
                        query += """
                                WHERE {}XRef.InbredSetId = {}Freeze.InbredSetId
                                and {}Freeze.Name = '{}'
                                and {}.Id = {}XRef.{}Id
                                order by {}.Id
                                """.format(*mescape(self.type, self.type, self.type, self.name,
                                                    dataset_type, self.type, dataset_type, dataset_type))
                    else:
                        query += """
                                WHERE {}XRef.{}FreezeId = {}Freeze.Id
                                and {}Freeze.Name = '{}'
                                and {}.Id = {}XRef.{}Id
                                order by {}.Id
                                """.format(*mescape(self.type, self.type, self.type, self.type,
                                                    self.name, dataset_type, self.type, self.type, dataset_type))
                    cursor.execute(query)
                    results = cursor.fetchall()
                    trait_sample_data.append([list(result) for result in results])

                trait_count = len(trait_sample_data[0])
                self.trait_data = collections.defaultdict(list)

                data_start_pos = 1
                for trait_counter in range(trait_count):
                    trait_name = trait_sample_data[0][trait_counter][0]
                    for chunk_counter in range(int(number_chunks)):
                        self.trait_data[trait_name] += (
                            trait_sample_data[chunk_counter][trait_counter][data_start_pos:])

                cache_dataset_results(
                    self.name, self.type, self.samplelist, self.trait_data)
            else:
                self.trait_data = cached_results
