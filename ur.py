"""
Allow for importing of IPython Notebooks as modules from Jupyter v4.

Updated from module collated here:
https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb

Importing from a notebook is different from a module: because one
typically keeps many computations and tests besides exportable defs,
here we only run code which either defines a function or a class, or
imports code from other modules and notebooks. This behaviour can be
disabled by setting nbimporter.options['only_defs'] = False.

Furthermore, in order to provide per-notebook initialisation, if a
special function __nbinit__() is defined in the notebook, it will be
executed the first time an import statement is. This behaviour can be
disabled by setting nbimporter.options['run_nbinit'] = False.

Finally, you can set the encoding of the notebooks with
nbimporter.options['encoding']. The default is 'utf-8'.

Related reading:
- https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Importing%20Notebooks.html: example nb importer from jupyter docs
- https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb: original source for jupyter example? (2014)

- https://github.com/grst/nbimporter: (this repo's base) wraps jupyter example, add cell-type filtering

- https://github.com/marella/nbimport: load from URL via %import magic

- https://github.com/rileyedmunds/import-ipynb: pip module from jupyter example code (2017)
- https://vispud.blogspot.com/2019/02/ipynb-import-another-ipynb-file.html mentions %run magic, which runs but doesn't import

- https://github.com/jupyter/notebook/issues/1588: jupyter discussing problem, points to example code, and ipython/ipynb repo
- https://github.com/ipython/ipynb: jupyter importer, supports cell-type restriction; obsolete? clumsy "ipynb.fs.full." import syntax

- https://github.com/jupyter/notebook/issues/3479: issue analyzing problem; recommends importnb
- https://github.com/deathbeds/importnb: jupyter importer / module-runner; similar to papermill?
"""

import sys
from types import ModuleType

from url_loader import URLLoader


class UrModule(ModuleType):

    def __init__(self, wrapped):
        super(UrModule, self).__init__(wrapped.__name__)
        self._wrapped = wrapped

    def __mul__(self, *args, **kwargs):
        return self(*(args + ('*',)), **kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, attr):
        return object.__getattribute__(self._wrapped, attr)


sys.modules[__name__] = UrModule(sys.modules[__name__])


_loader = URLLoader()
def main(*args, **kwargs):
    ret = _loader.main(*args, **kwargs)
    return ret
