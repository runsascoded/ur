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

import io, os, sys, types, ast
from inspect import stack
import nbformat
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from urllib.request import urlretrieve
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

import sys
from types import ModuleType

print('ur top: %s' % ' '.join(globals().keys()))
# print(
#     '\n'.join([
#         '%s:\n%s\n' % (name, globals()[name])
#         for name in [
#             '__name__', '__package__', '__loader__', '__spec__', '__file__', '__cached__', '__builtins__'
#         ]
#     ])
# )

class CallableModule(ModuleType):

    def __init__(self, wrapped):
        super(CallableModule, self).__init__(wrapped.__name__)
        self._wrapped = wrapped

    def __call__(self, *args, **kwargs):
        return self._wrapped.main(*args, **kwargs)

    def __getattr__(self, attr):
        return object.__getattribute__(self._wrapped, attr)


sys.modules[__name__] = CallableModule(sys.modules[__name__])

options = {'only_defs': True, 'run_nbinit': True, 'encoding': 'utf-8'}

def find_notebook(fullname, path=None):
    """ Find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    name = fullname.rsplit('.', 1)[-1]
    print(f'find_notebook: fullname {fullname}, path {path}, name {name}')
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            print(f'Found {nb_path}')
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            print(f'Found {nb_path}')
            return nb_path


class CellDeleter(ast.NodeTransformer):
    """ Removes all nodes from an AST which are not suitable
    for exporting out of a notebook. """
    def visit(self, node):
        """ Visit a node. """
        if node.__class__.__name__ in ['Module', 'FunctionDef', 'ClassDef',
                                       'Import', 'ImportFrom']:
            return node
        return None


class URLLoader:

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def main(self, path, *names, _globals=None):
        url = urlparse(path)
        print(f'load_module: {path} -> {url}')

        # load the notebook object
        nb_version = nbformat.version_info[0]

        if url.scheme:
            with NamedTemporaryFile() as f:
                print(f'Fetching {path} to {f.name}')
                urlretrieve(path, f.name)
                with io.open(f.name, 'r', encoding=options['encoding']) as f:
                    nb = nbformat.read(f, nb_version)
        else:
            with io.open(path, 'r', encoding=options['encoding']) as f:
                nb = nbformat.read(f, nb_version)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(path)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            print("Ignoring '%s': not a python notebook." % path)
            return

        # print("Importing Jupyter notebook from %s" % path)
        sys.modules[path] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            deleter = CellDeleter()
            for cell in filter(lambda c: c.cell_type == 'code', nb.cells):
                # transform the input into executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                print(f'cell code:\n{code}')
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

        if names:
            mod_dict = mod.__dict__
            if hasattr(mod, '__all__'):
                members = mod.__all__
            else:
                members = [ name for name in mod_dict if not name.startswith('_') ]

            import_all = '*' in names
            if import_all:
                names = [ name for name in names if not name == '*' ]

            not_found = list(set(names).difference(members))
            if not_found:
                raise Exception('Names not found: %s' % ','.join(not_found))

            if not import_all:
                members = names

            update = { name: mod_dict[name] for name in members }
            # print('importing: %s' % update)
            stk = stack()
            cur_file = stk[0].filename
            frame_info = next(frame for frame in stk if frame.filename != cur_file)
            # _globals = parent.f_globals
            # if _globals:
            #     _globals.update(update)
            frame_info.frame.f_globals.update(update)
            if _globals:
                _globals['stk'] = stk
                _globals['frame_info'] = frame_info
            #globals().update(update)
            return mod
            # print('globals: %s' % globals()['foo'])
        else:
            return mod


_loader = URLLoader()
def main(path, *names, _globals=None):

    print('main 1: %s' % ' '.join(globals().keys()))
    ret = _loader.main(path, *names, _globals=_globals)
    print('main 2: %s' % ' '.join(globals().keys()))
    return ret


class URLFinder(object):
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
            self.loaders[key] = URLLoader(path)
        return self.loaders[key]


sys.meta_path.append(URLFinder())

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
        mod = types.ModuleType(fullname)
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
    
    
#sys.meta_path.append(NotebookFinder())
