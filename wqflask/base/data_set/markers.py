"Base Class: Markers - "

import math

from flask import current_app as app

from utility.configuration import locate, flat_files

class Markers:
    """Todo: Build in cacheing so it saves us reading the same file more than once"""

    def __init__(self, name):
        json_data_fh = open(locate(app, name + ".json", 'genotype/json'))

        markers = []
        with open("%s/%s_snps.txt" % (flat_files(app, 'genotype/bimbam'), name), 'r') as bimbam_fh:
            if len(bimbam_fh.readline().split(", ")) > 2:
                delimiter = ", "
            elif len(bimbam_fh.readline().split(",")) > 2:
                delimiter = ","
            elif len(bimbam_fh.readline().split("\t")) > 2:
                delimiter = "\t"
            else:
                delimiter = " "
            for line in bimbam_fh:
                marker = {}
                marker['name'] = line.split(delimiter)[0].rstrip()
                marker['Mb'] = float(line.split(delimiter)[
                                     1].rstrip()) / 1000000
                marker['chr'] = line.split(delimiter)[2].rstrip()
                markers.append(marker)

        for marker in markers:
            if (marker['chr'] != "X") and (marker['chr'] != "Y") and (marker['chr'] != "M"):
                marker['chr'] = int(marker['chr'])
            marker['Mb'] = float(marker['Mb'])

        self.markers = markers

    def add_pvalues(self, p_values):
        if isinstance(p_values, list):
            # THIS IS only needed for the case when we are limiting the number of p-values calculated
            # if len(self.markers) > len(p_values):
            #    self.markers = self.markers[:len(p_values)]

            for marker, p_value in zip(self.markers, p_values):
                if not p_value:
                    continue
                marker['p_value'] = float(p_value)
                if math.isnan(marker['p_value']) or marker['p_value'] <= 0:
                    marker['lod_score'] = 0
                    marker['lrs_value'] = 0
                else:
                    marker['lod_score'] = -math.log10(marker['p_value'])
                    # Using -log(p) for the LRS; need to ask Rob how he wants to get LRS from p-values
                    marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
        elif isinstance(p_values, dict):
            filtered_markers = []
            for marker in self.markers:
                if marker['name'] in p_values:
                    marker['p_value'] = p_values[marker['name']]
                    if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                        marker['lod_score'] = 0
                        marker['lrs_value'] = 0
                    else:
                        marker['lod_score'] = -math.log10(marker['p_value'])
                        # Using -log(p) for the LRS; need to ask Rob how he wants to get LRS from p-values
                        marker['lrs_value'] = - \
                            math.log10(marker['p_value']) * 4.61
                    filtered_markers.append(marker)
            self.markers = filtered_markers


class HumanMarkers(Markers):
    "Markers for humans ..."

    def __init__(self, name, specified_markers=[]):
        marker_data_fh = open(flat_files(app, 'mapping') + '/' + name + '.bim')
        self.markers = []
        for line in marker_data_fh:
            splat = line.strip().split()
            if len(specified_markers) > 0:
                if splat[1] in specified_markers:
                    marker = {}
                    marker['chr'] = int(splat[0])
                    marker['name'] = splat[1]
                    marker['Mb'] = float(splat[3]) / 1000000
                else:
                    continue
            else:
                marker = {}
                marker['chr'] = int(splat[0])
                marker['name'] = splat[1]
                marker['Mb'] = float(splat[3]) / 1000000
            self.markers.append(marker)

    def add_pvalues(self, p_values):
        super(HumanMarkers, self).add_pvalues(p_values)
