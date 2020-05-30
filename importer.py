import ast
from importlib._bootstrap import spec_from_loader
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
import nbformat
from os import environ as env
from pathlib import Path
from re import match
import sys
from sys import stderr
from types import ModuleType

from cells import CellDeleter
import opts


class Importer:
    '''Importer providing a synthetic "gists" top-level package that allows importing `.py` and `.ipynb` files from
    GitHub Gists.'''

    DEBUG_ENV_VAR = 'UR_DEBUG'

    def __init__(self, **kw):
        self.shell = InteractiveShell.instance()
        self._print = print

    def print(self, *args, **kwargs):
        if opts.verbose:
            self._print(*args, **kwargs)

    def exec_path(self, path, mod=None):
        import _gist

        # load the notebook
        nb_version = nbformat.version_info[0]
        if isinstance(path, Path):
            with path.open('r', encoding=opts.encoding) as f:
                nb = nbformat.read(f, nb_version)
        elif isinstance(path, str):
            with open(path, 'r', encoding=opts.encoding) as f:
                nb = nbformat.read(f, nb_version)
        elif isinstance(path, _gist.File):
            nb = nbformat.read(path.data_stream, nb_version)
        else:
            raise ValueError(f'Unrecognized file type: {path} ({type(path)})')

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            self.print("Ignoring '%s': not a python notebook." % file)
            return

        if mod is None:
            # create the module and add it to sys.modules
            mod = ModuleType(str(path))
            mod.__file__ = str(path)
            mod.__loader__ = self
            mod.__dict__['get_ipython'] = get_ipython

            sys.modules[path] = mod
            dct = mod.__dict__

            self.exec_nb(nb, mod)
        else:
            self.exec_nb(nb, mod)

        return mod

    def exec_nb(self, nb, mod, only_defs=None):
        if only_defs is None: only_defs = opts.only_defs

        dct = mod.__dict__

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = dct

        try:
            deleter = CellDeleter()
            for cell in filter(lambda c: c.cell_type == 'code', nb.cells):
                # transform the input into executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                if only_defs:
                    self.print(f'defs only')
                    # Remove anything that isn't a def or a class
                    tree = deleter.generic_visit(ast.parse(code))
                else:
                    self.print(f'all symbols!')
                    tree = ast.parse(code)
                # run the code in the module
                codeobj = compile(tree, filename=mod.__file__, mode='exec')
                exec(codeobj, dct)
        finally:
            self.shell.user_ns = save_user_ns

        # Run any initialisation if available, but only once
        if opts.run_nbinit and '__nbinit_done__' not in dct:
            if hasattr(mod, '__nbinit__'):
                mod.__nbinit__()
                mod.__nbinit_done__ = True


    def find_spec(self, fullname, path=None, target=None, commit=None):
        self.print(f'find_spec: {fullname} {path} {target} (commit? {commit})')

        path = fullname.split('.')
        if path[0] not in [ 'gists', 'gist' ]: return

        if len(path) == 1:
            self.print(f'Creating _gist package')
            spec = spec_from_loader(fullname, self, origin=None, is_package=True)
            spec.__license__ = "CC BY-SA 3.0"
            spec._commit = commit
            spec._file = None

            spec.submodule_search_locations = []

            return spec

        id = path[1]
        if id.startswith('_'):
            id = id[1:]

        path = path[2:]
        if len(path) > 1:
            raise Exception(f'Too many path components for gist {id}: {path}')

        from _gist import Commit, Gist

        if isinstance(commit, Commit):
            gist = commit.gist
            url = commit.url
        else:
            self.print(f'Gist {id}: skip_cache={opts.skip_cache}')
            gist = Gist(id, _skip_cache=opts.skip_cache)
            url = gist.url
            if isinstance(commit, str):
                commit = Commit(commit, gist)
            elif commit is None:
                commit = gist.commit
            else:
                raise Exception(f'Invalid Gist commit value: {commit} (gist {gist})')

        self.print(f'Building module/pkg for gist {commit} ({path}; {target})')

        if path:
            [ filename ] = path
            files = commit.file_bases_dict
            if filename not in files:
                raise Exception(f'File {filename} not found in gist {commit} (files: {commit.files})')
            file = files[filename]
            url = file.url
            is_package = False
        else:
            file = None
            is_package = True

        origin = url

        self.print(f'Creating package spec from {url} ({origin})')
        spec = spec_from_loader(fullname, self, origin=origin, is_package=is_package)
        spec.__license__ = "CC BY-SA 3.0"
        spec.__author__ = commit.author
        spec._commit = commit
        spec._file = file

        if is_package:
            spec.submodule_search_locations = [ str(gist.clone_dir) ]

        return spec

    def create_module(self, spec):
        """Create a built-in module"""
        self.print(f'create_module {spec}')
        mod = ModuleType(spec.name)
        mod.__file__ = spec.origin
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        mod.__spec__ = spec

        self.print(f'Installing module {spec.name}: {mod}')
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, mod=None):
        """Exec a module"""
        self.print(f'exec_module {mod}')
        spec = mod.__spec__
        self.exec(
            name=spec.name,
            commit=spec._commit,
            mod=mod,
            file=spec._file,
        )

    def exec(self, name, commit, mod, file=None):
        dct = mod.__dict__
        if not file:
            if commit:
                file_mods = []
                for file in commit.files:
                    module_name = file.module_name
                    fullname = f'{name}.{module_name}'
                    file_spec = self.find_spec(fullname, commit=commit.id)
                    if file_spec:
                        self.print(f'Found spec for child module {module_name} ({fullname})')
                        file_mod = self.create_module(file_spec)
                        file_mods.append(file_mod)
                        dct[module_name] = file_mod

                # Temporarily add a local notebook loader rooted at the Gist's root, so that local imports within the Gist resolve
                from local_importer import NotebookFinder
                finder = NotebookFinder(str(commit.gist.clone_dir))
                prev_meta_path = sys.meta_path.copy()
                try:
                    sys.meta_path += [ finder ]
                    [ self.exec_module(file_mod) for file_mod in file_mods ]
                finally:
                    # Remove this Gist's custom loader, verifying that meta_path looks the way we expect
                    [ pos ] = [ idx for idx, loader in enumerate(sys.meta_path) if loader is finder ]
                    if len(prev_meta_path) + 1 != len(sys.meta_path) or \
                        pos != len(prev_meta_path):
                        stderr.write(f'Unexpected meta_path change while executing module {file_mod}: {len(prev_meta_path)} → {len(sys.meta_path)} entries, new loader at position {pos}\n')
                    sys.meta_path.pop(pos)
        else:
            self.print(f'Attempt to exec module {name}')
            if file.name.endswith('.py'):
                self.print(f'exec py: {file}')
                code = file.read_text()
                try:
                    exec(code, dct)
                except:
                    self.print(f'Error executing module {name} ({file}\n{code}')
            elif file.name.endswith('.ipynb'):
                self.print(f'exec notebook: {file}')
                self.exec_path(file, mod)