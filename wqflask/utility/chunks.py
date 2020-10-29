import math
import time


def divide_into_chunks(the_list, number_chunks):
    """Divides a list into approximately number_chunks smaller lists

    >>> divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 3)
    [[1, 2, 7], [3, 22, 8], [5, 22, 333]]
    >>> divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 4)
    [[1, 2, 7], [3, 22, 8], [5, 22, 333]]
    >>> divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 5)
    [[1, 2], [7, 3], [22, 8], [5, 22], [333]]
    >>>

    """
    length = len(the_list)

    if length == 0:
        return [[]]

    if length <= number_chunks:
        number_chunks = length

    chunksize = int(math.ceil(length / number_chunks))

    chunks = []
    for counter in range(0, length, chunksize):
        chunks.append(the_list[counter:counter+chunksize])

    return chunks
