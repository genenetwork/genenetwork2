def normalize_values(a_values, b_values):
    """
    Trim two lists of values to contain only the values they both share

    Given two lists of sample values, trim each list so that it contains
    only the samples that contain a value in both lists. Also returns
    the number of such samples.

    >>> normalize_values([2.3, None, None, 3.2, 4.1, 5], [3.4, 7.2, 1.3, None, 6.2, 4.1])
    ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

    """

    min_length = min(len(a_values), len(b_values))
    a_new = []
    b_new = []
    for a, b in zip(a_values, b_values):
        if not (a == None or b == None):
            a_new.append(a)
            b_new.append(b)
    return a_new, b_new, len(a_new)


def common_keys(a_samples, b_samples):
    """
    >>> a = dict(BXD1 = 9.113, BXD2 = 9.825, BXD14 = 8.985, BXD15 = 9.300)
    >>> b = dict(BXD1 = 9.723, BXD3 = 9.825, BXD14 = 9.124, BXD16 = 9.300)
    >>> sorted(common_keys(a, b))
    ['BXD1', 'BXD14']
    """
    return set(a_samples.keys()).intersection(set(b_samples.keys()))


def normalize_values_with_samples(a_samples, b_samples):
    common_samples = common_keys(a_samples, b_samples)
    a_new = {}
    b_new = {}
    for sample in common_samples:
        a_new[sample] = a_samples[sample]
        b_new[sample] = b_samples[sample]

    return a_new, b_new, num_overlap
