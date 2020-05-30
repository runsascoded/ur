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
"""

import io, os, sys, types, ast
import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

options = {'only_defs': True, 'run_nbinit': True, 'encoding': 'utf-8'}

def find_notebook(fullname, path=None):
    """ Find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    #print(f'nbimporter: find_notebook({fullname=}, {path=})')
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            #print(f'Found notebook: {nb_path}')
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            #print(f'Found notebook: {nb_path}')
            return nb_path

        # py_path = os.path.join(d, name + ".py")
        # if os.path.isfile(py_path):
        #     #print(f'Found notebook: {nb_path}')
        #     return py_path


class NotebookLoader(object):
    """ Module Loader for Jupyter Notebooks. """

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def create_module(self, spec):
        """import a notebook as a module"""
        path = find_notebook(spec.name, self.path)

        with io.open(path, 'r', encoding=options['encoding']) as f:
            # load the notebook object
            nb_version = nbformat.version_info[0]
            nb = nbformat.read(f, nb_version)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(spec.name)
        mod.__file__ = path
        mod.__spec__ = spec
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        mod._nb = nb

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            print("Ignoring '%s': not a python notebook." % path)
            return mod

        #print(f"Creating Jupyter notebook module {spec.name} from {path}: {mod}")
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, mod):
        #print(f'NotebookLoader.exec_module: {mod}')
        from gists import importer
        importer.exec_nb(mod._nb, mod)
        return mod


class NotebookFinder(object):
    """Module finder that locates Jupyter Notebooks"""
    def __init__(self, root=None):
        self.loaders = {}
        self.root = root

    def path(self, path):
      if path: return path
      if self.root: return [self.root]
      return None

    def find_module(self, fullname, path=None):
        path = self.path(path)
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            #print(f'No notebook found: {fullname=}, {path=}, root={self.root}')
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]
