import ast
import io
import os
import sys
from tempfile import NamedTemporaryFile
from types import ModuleType
from urllib.parse import urlparse
from urllib.request import urlretrieve

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from cells import CellDeleter


options = {'only_defs': True, 'run_nbinit': True, 'encoding': 'utf-8'}


def find_notebook(fullname, path=None):
    """ Find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path


class NotebookLoader(object):
    """ Module Loader for Jupyter Notebooks. """

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        url = urlparse(fullname)
        print(f'load_module: {fullname} -> {url}')

        # load the notebook object
        nb_version = nbformat.version_info[0]

        if url.scheme:
            with NamedTemporaryFile() as f:
                print(f'Fetching {fullname} to {f.name}')
                urlretrieve(fullname, f.name)
                path = f.name
                with io.open(path, 'r', encoding=options['encoding']) as f:
                    nb = nbformat.read(f, nb_version)
                path = fullname
        else:
            path = find_notebook(fullname, self.path)
            with io.open(path, 'r', encoding=options['encoding']) as f:
                nb = nbformat.read(f, nb_version)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            print("Ignoring '%s': not a python notebook." % path)
            return mod

        print("Importing Jupyter notebook from %s" % path)
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            deleter = CellDeleter()
            for cell in filter(lambda c: c.cell_type == 'code', nb.cells):
                # transform the input into executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                if options['only_defs']:
                    # Remove anything that isn't a def or a class
                    tree = deleter.generic_visit(ast.parse(code))
                else:
                    tree = ast.parse(code)
                # run the code in the module
                codeobj = compile(tree, filename=path, mode='exec')
                exec(codeobj, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns

        # Run any initialisation if available, but only once
        if options['run_nbinit'] and '__nbinit_done__' not in mod.__dict__:
            try:
                mod.__nbinit__()
                mod.__nbinit_done__ = True
            except (KeyError, AttributeError) as _:
                pass

        return mod


class NotebookFinder(object):
    """Module finder that locates Jupyter Notebooks"""
    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        print(f'find_module: ${fullname}, ${path}')
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]


sys.meta_path.append(NotebookFinder())
