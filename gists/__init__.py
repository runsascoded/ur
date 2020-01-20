import ast
from importlib._bootstrap import spec_from_loader
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
import nbformat
import sys
from types import ModuleType

from cells import CellDeleter
from gist import Gist

options = { 'only_defs': True, 'encoding': 'utf-8' }


class Importer:
    '''Importer providing a synthetic "gists" top-level package that allows importing `.py` and `.ipynb` files from
    GitHub Gists.'''

    def __init__(self):
        self.shell = InteractiveShell.instance()

    def find_spec(self, fullname, path=None, target=None):
        print(f'find_spec: {fullname} {path} {target}')
        path = fullname.split('.')
        if path[0] != 'gists':
            return
        id = path[1]
        if id.startswith('_'):
            id = id[1:]
        path = path[2:]
        gist = Gist(id)

        print(f'Building module/pkg for gist {gist} ({path}; {target})')

        if len(path) > 1:
            raise Exception(f'Too many path components for gist {id}: {path}')

        if path:
            [ filename ] = path
            files = gist.file_bases_dict
            if filename not in files:
                raise Exception(f'File {filename} not found in gist {gist} (files: {gist.files})')
            file = files[filename]
            origin = file.path
            url = file.url
            is_package = False
        else:
            origin = gist.cloned_dir
            url = gist.url
            file = None
            is_package = True

        print(f'Creating package spec from {url} ({origin})')
        spec = spec_from_loader(fullname, self, origin=origin, is_package=is_package)
        spec.__license__ = "CC BY-SA 3.0"
        spec.__author__ = gist.author
        spec._gist = gist
        spec._url = url

        if is_package:
            spec.submodule_search_locations = [ str(gist.cloned_dir) ]

        return spec

    def create_module(self, spec):
        """Create a built-in module"""
        print(f'create_module {spec}')
        mod = ModuleType(spec.name)
        mod.__file__ = spec.origin
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        mod.__spec__ = spec

        print(f'Installing module {spec.name}: {mod}')
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, mod=None):
        """Exec a built-in module"""
        print(f'exec_module {mod}')
        spec = mod.__spec__

        if spec.submodule_search_locations:
            gist = spec._gist
            for file in gist.files:
                basename = file.name
                if basename == '.git': continue
                module_name = file.module_name
                fullname = f'{spec.name}.{module_name}'
                file_spec = self.find_spec(fullname)
                if file_spec:
                    print(f'Found spec for child module {module_name} ({fullname})')
                    file_mod = self.create_module(file_spec)
                    self.exec_module(file_mod)
                    mod.__dict__[module_name] = file_mod
        else:
            print(f'Attempt to exec module {spec}')

            path = spec.origin
            if path.name.endswith('.py'):
                print(f'exec py: {path}')
                code = path.read_text()
                try:
                    exec(code, mod.__dict__)
                except:
                    print(f'Error executing module {mod} ({path}\n{code}')
            elif path.name.endswith('.ipynb'):
                print(f'exec notebook: {path}')
                # load the notebook
                nb_version = nbformat.version_info[0]
                with open(path, 'r', encoding=options['encoding']) as f:
                    nb = nbformat.read(f, nb_version)

                # Only do something if it's a python notebook
                if nb.metadata.kernelspec.language != 'python':
                    print("Ignoring '%s': not a python notebook." % path)
                    return mod

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


sys.meta_path.append(Importer())
