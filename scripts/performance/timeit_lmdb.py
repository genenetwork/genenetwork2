import sys
import timeit

print(timeit.timeit(
"""
PATH = "/home/munyoki/tmp/dataset/HLCPublish/10001/"
env = lmdb.open(PATH)

BLOB_HASH_DIGEST = 32

# def index_matrix(row_pointers):

with env.begin(write=False) as txn:
    current_hash = txn.get(b"current")
    matrix_hash = txn.get(current_hash + b":matrix")
    row_pointers = txn.get(matrix_hash +
                           b":row-pointers")
    nrows, = struct.unpack("<Q",
                           txn.get(matrix_hash + b":nrows"))
    metadata = txn.get(matrix_hash + b":metadata")
    sample_data = []
    for i in range(0, (nrows-1)*32, 32):
        sample_data.append(
            json.loads(txn.get(row_pointers[i:i+32]).decode())
        )
    print(sample_data)
    print(metadata.decode())
""",
    setup="""
import struct
import array
import json
import lmdb
""",
    number=int(sys.argv[1])
))
