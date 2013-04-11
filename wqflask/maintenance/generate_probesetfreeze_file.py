#!/usr/bin/python

from __future__ import absolute_import, print_function, division

import sys

sys.path.insert(0, "..")

import os
import collections
import csv

import MySQLdb

from base import webqtlConfig

from pprint import pformat as pf


def get_cursor():
    con = MySQLdb.Connect(db=webqtlConfig.DB_UPDNAME,
                          host=webqtlConfig.MYSQL_UPDSERVER,
                          user=webqtlConfig.DB_UPDUSER,
                          passwd=webqtlConfig.DB_UPDPASSWD)
    cursor = con.cursor()
    return cursor

def show_progress(process, counter):
    if counter % 1000 == 0:
        print("{}: {}".format(process, counter))

def get_strains(cursor):
    cursor.execute("""select Strain.Name
                      from Strain, StrainXRef, InbredSet
                      where Strain.Id = StrainXRef.StrainId and
                            StrainXRef.InbredSetId = InbredSet.Id
                            and InbredSet.Name=%s;
                """, "BXD")

    strains = [strain[0] for strain in cursor.fetchall()]
    print("strains:", pf(strains))
    for strain in strains:
        print(" -", strain)

    return strains

def get_probeset_vals(cursor, dataset_name):
    cursor.execute(""" select ProbeSet.Id, ProbeSet.Name
                from ProbeSetXRef,
                     ProbeSetFreeze,
                     ProbeSet
                where ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id and
                      ProbeSetFreeze.Name = %s and
                      ProbeSetXRef.ProbeSetId = ProbeSet.Id;
            """, dataset_name)

    probesets = cursor.fetchall()

    print("Fetched probesets")

    probeset_vals = collections.OrderedDict()

    for counter, probeset in enumerate(probesets):
        cursor.execute(""" select Strain.Name, ProbeSetData.value
                       from ProbeSetData, ProbeSetXRef, ProbeSetFreeze, Strain
                       where ProbeSetData.Id = ProbeSetXRef.DataId
                       and ProbeSetData.StrainId = Strain.Id
                       and ProbeSetXRef.ProbeSetId = %s
                       and ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId
                       and ProbeSetFreeze.Name = %s;
                """, (probeset[0], dataset_name))
        val_dic = collections.OrderedDict()
        vals = cursor.fetchall()
        for val in vals:
            val_dic[val[0]] = val[1]

        probeset_vals[probeset[1]] = val_dic
        show_progress("Querying DB", counter)

    return probeset_vals

def trim_strains(strains, probeset_vals):
    trimmed_strains = []
    #print("probeset_vals is:", pf(probeset_vals))
    first_probeset = list(probeset_vals.itervalues())[0]
    print("\n**** first_probeset is:", pf(first_probeset))
    for strain in strains:
        print("\n**** strain is:", pf(strain))
        if strain in first_probeset:
            trimmed_strains.append(strain)
    print("trimmed_strains:", pf(trimmed_strains))
    return trimmed_strains

def write_data_matrix_file(strains, probeset_vals, filename):
    with open(filename, "wb") as fh:
        csv_writer = csv.writer(fh, delimiter=",", quoting=csv.QUOTE_ALL)
        #print("strains is:", pf(strains))
        csv_writer.writerow(['ID'] + strains)
        for counter, probeset in enumerate(probeset_vals):
            row_data = [probeset]
            for strain in strains:
                #print("probeset is: ", pf(probeset_vals[probeset]))
                row_data.append(probeset_vals[probeset][strain])
            #print("row_data is: ", pf(row_data))
            csv_writer.writerow(row_data)
            show_progress("Writing", counter)

def main():
    filename = os.path.expanduser("~/gene/wqflask/maintenance/" +
                "ProbeSetFreezeId_210_FullName_Eye_AXBXA_Illumina_V6.2" + 
                "(Oct08)_RankInv_Beta.txt")
    dataset_name = "Eye_AXBXA_1008_RankInv"

    cursor = get_cursor()
    strains = get_strains(cursor)
    print("Getting probset_vals")
    probeset_vals = get_probeset_vals(cursor, dataset_name)
    print("Finished getting probeset_vals")
    trimmed_strains = trim_strains(strains, probeset_vals)
    write_data_matrix_file(trimmed_strains, probeset_vals, filename)

if __name__ == '__main__':
    main()
