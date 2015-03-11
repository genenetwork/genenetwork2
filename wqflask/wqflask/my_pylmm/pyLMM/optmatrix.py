import sys
import time
import numpy as np
from numpy.distutils.system_info import get_info;
from scipy import linalg
from scipy import optimize
from scipy import stats

useNumpy = None
hasBLAS = None

def matrix_initialize(useBLAS):
    global useNumpy  # module based variable
    if useBLAS and useNumpy == None:
        print get_info('blas_opt')
        try:
            linalg.fblas
            sys.stderr.write("INFO: using linalg.fblas\n")
            useNumpy = False
            hasBLAS  = True
        except AttributeError:
            sys.stderr.write("WARNING: linalg.fblas not found, using numpy.dot instead!\n")
            useNumpy = True
    else:
        sys.stderr.write("INFO: using numpy.dot\n")
        useNumpy=True
        
def matrixMult(A,B):
   global useNumpy  # module based variable

   if useNumpy:
       return np.dot(A,B)

   # If the matrices are in Fortran order then the computations will be faster
   # when using dgemm.  Otherwise, the function will copy the matrix and that takes time.
   if not A.flags['F_CONTIGUOUS']:
      AA = A.T
      transA = True
   else:
      AA = A
      transA = False

   if not B.flags['F_CONTIGUOUS']:
      BB = B.T
      transB = True
   else:
      BB = B
      transB = False

   return linalg.fblas.dgemm(alpha=1.,a=AA,b=BB,trans_a=transA,trans_b=transB)

def matrixMultT(M):
    # res = np.dot(W,W.T)
    # return linalg.fblas.dgemm(alpha=1.,a=M.T,b=M.T,trans_a=True,trans_b=False)
    return matrixMult(M,M.T)
