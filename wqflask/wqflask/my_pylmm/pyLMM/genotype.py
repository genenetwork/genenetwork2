# Genotype routines

# Copyright (C) 2013  Nicholas A. Furlotte (nick.furlotte@gmail.com)
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from collections import Counter
import operator

def replace_missing_with_MAF(snp_g):
    """
    Replace the missing genotype with the minor allele frequency (MAF)
    in the snp row. It is rather slow!
    """
    cnt = Counter(snp_g)
    tuples = sorted(cnt.items(), key=operator.itemgetter(1))
    l2 = [t for t in tuples if not np.isnan(t[0])]
    maf = l2[0][0]
    res = np.array([maf if np.isnan(snp) else snp for snp in snp_g])
    return res
    
def normalize(ind_g):
    """
    Run for every SNP list (for one individual) and return
    normalized SNP genotype values with missing data filled in
    """
    g = np.copy(ind_g)              # copy to avoid side effects
    missing = np.isnan(g)
    values = g[True - missing]
    mean = values.mean()            # Global mean value
    stddev = np.sqrt(values.var())  # Global stddev
    g[missing] = mean               # Plug-in mean values for missing data
    if stddev == 0:
        g = g - mean                # Subtract the mean
    else:
        g = (g - mean) / stddev     # Normalize the deviation
    return g

