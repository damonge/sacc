#!/usr/bin/env python
#
# This takes an input sacc files, replaces measurements with CCL theory predictions + scatter and
# resaves
#

import sacc
import sys
import numpy as np
import scipy.linalg as la
try:
    import pyccl as ccl
except:
    print ("Need CCL!")
    sys.exit(1)

p = ccl.Parameters(Omega_c=0.27, Omega_b=0.045, h=0.67, A_s=1e-10, n_s=0.96)
ccl_cosmo = ccl.Cosmology(p)
s=sacc.SACC.loadFromHDF("test.sacc")
#
# first, let's convert sacc tracers to CCL tracers
#
def sacc2ccl_tracer(t):
    if t.type=="point":
        toret=ccl.ClTracerNumberCounts(ccl_cosmo,has_rsd=False,
                                    has_magnification=False
                                    ,z_n=t.z,n=t.Nz,z_b=t.z
                                    ,b=t.extraColumn('b'),z_s=t.z,
                                    s=np.zeros(len(t.z)))
    else:
        toret=None
    return toret

ctracers=[sacc2ccl_tracer(t) for t in s.tracers]


#
# next, caclulate theory predictions
#
for t1i,t2i,ells,ndx in s.sortTracers():
    if (ctracers[t1i] is not None) and (ctracers[t2i] is not None):
        cl_model = ccl.angular_cl(ccl_cosmo,ctracers[t1i],ctracers[t2i],ells)
        s.mean.vector[ndx]=cl_model
    else:
        s.mean.vector[ndx]=0.0 ## we don't yet know how to deal with CMB

## now get covariance and sample from it:
cov=la.inv(s.precision.matrix)
chol=la.cholesky(cov)
# (perhaps need chol.T below ? double check)
noise=np.dot(chol, np.random.normal(0.,1.,len(s.mean.vector)))
## Add noise
s.mean.vector['value']+=noise
## Save file new file
s.saveToHDF("test_ccl.sacc")

    
    

