import ast
from importlib._bootstrap import spec_from_loader
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
import nbformat
from os import environ as env
import sys
from types import ModuleType

from cells import CellDeleter
from gist import Commit, Gist

options = { 'only_defs': True, 'encoding': 'utf-8' }


class Importer:
    '''Importer providing a synthetic "gists" top-level package that allows importing `.py` and `.ipynb` files from
    GitHub Gists.'''

    DEBUG_ENV_VAR = 'UR_DEBUG'

    def __init__(self, **kw):
        self.shell = InteractiveShell.instance()

        if 'debug' in kw:
            self._print = kw['debug']
        elif self.DEBUG_ENV_VAR in env and env[self.DEBUG_ENV_VAR]:
            self._print = print
        else:
            self._print = None

    def print(self, *args, **kwargs):
        if self._print:
            self._print(*args, **kwargs)

    def find_spec(self, fullname, path=None, target=None, commit=None):
        self.print(f'find_spec: {fullname} {path} {target} (commit? {commit})')

        path = fullname.split('.')
        if path[0] != 'gists': return

        id = path[1]
        if id.startswith('_'):
            id = id[1:]

        path = path[2:]
        if len(path) > 1:
            raise Exception(f'Too many path components for gist {id}: {path}')

        if isinstance(commit, Commit):
            gist = commit.gist
            url = commit.url
        else:
            gist = Gist(id)
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
            dct=mod.__dict__ ,
            file=spec._file,
        )

    def exec(self, name, commit, dct, file=None):
        if not file:
            for file in commit.files:
                module_name = file.module_name
                fullname = f'{name}.{module_name}'
                file_spec = self.find_spec(fullname, commit=commit.id)
                if file_spec:
                    self.print(f'Found spec for child module {module_name} ({fullname})')
                    file_mod = self.create_module(file_spec)
                    self.exec_module(file_mod)
                    dct[module_name] = file_mod
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
                # load the notebook
                nb_version = nbformat.version_info[0]
                nb = nbformat.read(file.data_stream, nb_version)

                # Only do something if it's a python notebook
                if nb.metadata.kernelspec.language != 'python':
                    self.print("Ignoring '%s': not a python notebook." % file)
                    return

                # extra work to ensure that magics that would affect the user_ns
                # actually affect the notebook module's ns
                save_user_ns = self.shell.user_ns
                self.shell.user_ns = dct

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
                        codeobj = compile(tree, filename=file.url, mode='exec')
                        exec(codeobj, dct)
                finally:
                    self.shell.user_ns = save_user_ns


importer = Importer()


if not any([ isinstance(importer, Importer) for importer in sys.meta_path ]):
    sys.meta_path.append(importer)
