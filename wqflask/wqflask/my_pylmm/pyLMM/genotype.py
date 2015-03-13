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

def normalizeGenotype(g):
    """
    Run for every SNP list (for one individual) and return
    normalized SNP genotype values with missing data filled in
    """
    g1 = np.copy(g)          # avoid side effects
    x = True - np.isnan(g)   # Matrix of True/False
    m = g[x].mean()          # Global mean value
    s = np.sqrt(g[x].var())  # Global stddev
    g1[np.isnan(g)] = m      # Plug-in mean values for missing data
    if s == 0:
        g1 = g1 - m          # Subtract the mean
    else:
        g1 = (g1 - m) / s    # Normalize the deviation
    return g1

