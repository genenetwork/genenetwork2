"""Statistics utilities."""
import math

def lrs_to_lod(lrs_score):
    """Convert Likelihood Ratio Statistic (LRS) score to Logarithm of Odds (LOD)
    score."""
    return lrs_score/(2*math.log(10))


def lod_to_lrs(lod_score):
    """Convert Logarith of Odds (LOD) score into Likelihood Ratio Statistic
    (LRS) score."""
    return lod_score * 2 * math.log(10)
