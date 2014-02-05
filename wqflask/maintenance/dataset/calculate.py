import scipy.stats

def correlation(a1, a2):
    re = []
    re.append(scipy.stats.pearsonr(a1, a2))
    re.append(scipy.stats.spearmanr(a1, a2))
    return re
