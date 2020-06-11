#!/usr/bin/env python

import ur
ur.verbose = 1

from examples.abcd_gist import *

print(nb_abs_nb.nb_abs_nb())
print(nb_abs_py.nb_abs_py())
print(py_abs_nb.py_abs_nb())
print(py_abs_py.py_abs_py())
