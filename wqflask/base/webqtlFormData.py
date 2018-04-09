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

from __future__ import print_function
from pprint import pformat as pf

import string
import os

import reaper

import webqtlConfig
from webqtlCaseData import webqtlCaseData
from utility import webqtlUtil

class webqtlFormData(object):
    'Represents data from a WebQTL form page, needed to generate the next page'

    attrs = ('formID','group','genotype','samplelist','allsamplelist', 'display_variance'
                'suggestive','significance','submitID','identification', 'enablevariance',
                'nperm','nboot','email','incparentsf1','genotype_1','genotype_2','traitInfo')

    #XZ: Attention! All attribute values must be picklable!

    def __init__(self,
                 start_vars = None,
                 req = None):
        # Todo: rework this whole thing
        for item in webqtlFormData.attrs:
            self.__dict__[item] = None

        for item in start_vars:
            self.__dict__[item] = start_vars[item]

        #Todo: This can't be good below...rework
        try:
            self.remote_ip = req.connection.remote_ip
        except:
            self.remote_ip = '1.2.3.4'

        self.ppolar = None
        self.mpolar = None

        if self.group:
            _f1, _f12, self.mpolar, self.ppolar = webqtlUtil.ParInfo[self.group]

        def set_number(stringy):
            return int(stringy) if stringy else 2000 # Rob asked to change the default value to 2000

        self.nperm = set_number(self.nperm)
        self.nboot = set_number(self.nboot)

        if self.allsamplelist:
            self.allsamplelist = self.allsamplelist.split()

        if self.group == 'BXD300':
            self.group = 'BXD'

    def __getitem__(self, key):
        return self.__dict__[key]

    def get(self, key, default=None):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            return default

    def __str__(self):
        rstr = ''
        for item in self.attrs:
            if item != 'genotype':
                rstr += '%s:%s\n' % (item,str(getattr(self,item)))
        return rstr


    def readGenotype(self):
        '''read genotype from .geno file'''
        if self.group == 'BXD300':
            self.group = 'BXD'

        assert self.group, "self.group needs to be set"

        #genotype_1 is Dataset Object without parents and f1
        #genotype_2 is Dataset Object with parents and f1 (not for intercross)

        self.genotype_1 = reaper.Dataset()

        full_filename = locate(self.group + '.geno','genotype')

        # reaper barfs on unicode filenames, so here we ensure it's a string
        full_filename = str(full_filename)
        self.genotype_1.read(full_filename)

        print("Got to after read")

        try:
            # NL, 07/27/2010. ParInfo has been moved from webqtlForm.py to webqtlUtil.py;
            _f1, _f12, _mat, _pat = webqtlUtil.ParInfo[self.group]
        except KeyError:
            _f1 = _f12 = _mat = _pat = None

        self.genotype_2 = self.genotype_1
        if self.genotype_1.type == "group" and _mat and _pat:
            self.genotype_2 = self.genotype_1.add(Mat=_mat, Pat=_pat)       #, F1=_f1)

        #determine default genotype object
        if self.incparentsf1 and self.genotype_1.type != "intercross":
            self.genotype = self.genotype_2
        else:
            self.incparentsf1 = 0
            self.genotype = self.genotype_1

        self.samplelist = list(self.genotype.prgy)
        self.f1list = []
        self.parlist = []

        if _f1 and _f12:
            self.f1list = [_f1, _f12]
        if _mat and _pat:
            self.parlist = [_mat, _pat]


    def readData(self, samplelist, incf1=None):
        '''read user input data or from trait data and analysis form'''

        if incf1 == None:
            incf1 = []

        if not self.genotype:
            self.readGenotype()
        if not samplelist:
            if incf1:
                samplelist = self.f1list + self.samplelist
            else:
                samplelist = self.samplelist

        traitfiledata = getattr(self, "traitfile", None)
        traitpastedata = getattr(self, "traitpaste", None)
        variancefiledata = getattr(self, "variancefile", None)
        variancepastedata = getattr(self, "variancepaste", None)
        Nfiledata = getattr(self, "Nfile", None)

        #### Todo: Rewrite below when we get to someone submitting their own trait #####

        def to_float(item):
            try:
                return float(item)
            except ValueError:
                return None

        print("bottle samplelist is:", samplelist)
        if traitfiledata:
            tt = traitfiledata.split()
            values = map(webqtlUtil.StringAsFloat, tt)
        elif traitpastedata:
            tt = traitpastedata.split()
            values = map(webqtlUtil.StringAsFloat, tt)
        else:
            print("mapping formdataasfloat")
            #values = map(self.FormDataAsFloat, samplelist)
            values = [to_float(getattr(self, key)) for key in samplelist]


        if len(values) < len(samplelist):
            values += [None] * (len(samplelist) - len(values))
        elif len(values) > len(samplelist):
            values = values[:len(samplelist)]

        if variancefiledata:
            tt = variancefiledata.split()
            variances = map(webqtlUtil.StringAsFloat, tt)
        elif variancepastedata:
            tt = variancepastedata.split()
            variances = map(webqtlUtil.StringAsFloat, tt)
        else:
            variances = map(self.FormVarianceAsFloat, samplelist)

        if len(variances) < len(samplelist):
            variances += [None]*(len(samplelist) - len(variances))
        elif len(variances) > len(samplelist):
            variances = variances[:len(samplelist)]

        if Nfiledata:
            tt = string.split(Nfiledata)
            nsamples = map(webqtlUtil.IntAsFloat, tt)
            if len(nsamples) < len(samplelist):
                nsamples += [None]*(len(samplelist) - len(nsamples))
        else:
            nsamples = map(self.FormNAsFloat, samplelist)

        ##values, variances, nsamples is obsolete
        self.allTraitData = {}
        for i, _sample in enumerate(samplelist):
            if values[i] != None:
                self.allTraitData[_sample] = webqtlCaseData(
                    _sample, values[i], variances[i], nsamples[i])

    def informativeStrains(self, samplelist=None, include_variances = None):
        '''if readData was called, use this to output informative samples (sample with values)'''

        if not samplelist:
            samplelist = self.samplelist

        samples = []
        values = []
        variances = []

        for sample in samplelist:
            if sample in self.allTraitData:
                _val, _var = self.allTraitData[sample].value, self.allTraitData[sample].variance
                if _val != None:
                    if include_variances:
                        if _var != None:
                            samples.append(sample)
                            values.append(_val)
                            variances.append(_var)
                    else:
                        samples.append(sample)
                        values.append(_val)
                        variances.append(None)

        return samples, values, variances, len(samples)

    def FormVarianceAsFloat(self, key):
        try:
            return float(self.formdata.getfirst('V' + key))
        except:
            return None

    def FormNAsFloat(self, key):
        try:
            return int(self.formdata.getfirst('N' + key))
        except:
            return None