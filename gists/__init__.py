import ast
import nbformat
from types import ModuleType
from IPython.core.interactiveshell import InteractiveShell

from IPython import get_ipython

options = {'only_defs': True, 'run_nbinit': True, 'encoding': 'utf-8'}

from nbimporter.nbimporter import CellDeleter

import sys
from importlib._bootstrap import spec_from_loader

from gist_cache import Gist

class GistImporter:
    """
    `from stackoverflow import quick_sort` will go through the search results
    of `[python] quick sort` looking for the largest code block that doesn't
    syntax error in the highest voted answer from the highest voted question
    and return it as a module, or raise ImportError if there's no code at all.
    """

    def __init__(self, path=None):
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
        url = gist.url

        print(f'Building module/pkg for gist {gist} ({path}; {target})')

        if len(path) > 1:
            raise Exception(f'Too many path components for gist {id}: {path}')

        file = None
        if path:
            [ file ] = path

        if file:
            print(f'Creating module spec from file {file}')
            spec = spec_from_loader(fullname, self, origin=file, is_package=False)
            spec.__license__ = "CC BY-SA 3.0"
            spec._url = url
            files = gist.file_bases_dict
            if file not in files:
                raise Exception(f'File {file} not found in gist {gist} (files: {gist.files})')
            path = files[file].path
            spec.__author__ = gist.author
            spec._path = path
            spec._gist = gist
            return spec
        else:
            print(f'Creating package spec from url {url} ({gist.cloned_dir})')
            spec = spec_from_loader(fullname, self, origin=url, is_package=True)
            spec.submodule_search_locations = [ str(gist.cloned_dir) ]
            spec.__license__ = "CC BY-SA 3.0"
            spec._url = url
            spec.__author__ = gist.author
            spec._gist = gist
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
                if basename == '.git':
                    continue
                name = basename.rpartition('.')[0]
                fullname = f'{mod.__name__}.{name}'
                file_spec = self.find_spec(fullname)
                if file_spec:
                    print(f'Found spec for child module {name} ({fullname})')
                    file_mod = self.create_module(file_spec)
                    file_spec.loader.exec_module(file_mod)
                    # if self.exec_module(file_mod):
                    mod.__dict__[name] = file_mod
        else:
            print(f'Attempt to exec module {spec}')

            path = spec._path
            if path.name.endswith('.py'):
                print(f'exec py: {path}')
                code = path.read_text()
                try:
                    exec(code, mod.__dict__)
                    return True
                except:
                    print(f'Error executing module {mod} ({path}\n{code}')
            elif path.name.endswith('.ipynb'):
                print(f'exec notebook: {path}')
                # load the notebook object
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

                # Run any initialisation if available, but only once
                # if options['run_nbinit'] and '__nbinit_done__' not in mod.__dict__:
                #     try:
                #         mod.__nbinit__()
                #         mod.__nbinit_done__ = True
                #     except (KeyError, AttributeError) as _:
                #         pass

                # return mod

sys.meta_path.append(GistImporter())
