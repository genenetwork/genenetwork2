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
    for counter in range(min_length):
        if a_values[counter] and b_values[counter]:
            a_new.append(a_values[counter])
            b_new.append(b_values[counter])
        
    num_overlap = len(a_new)
    assert num_overlap == len(b_new), "Lengths should be the same"
    
    return a_new, b_new, num_overlap


if __name__ == '__main__':
    import doctest
    doctest.testmod()