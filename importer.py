import ast
from collections.abc import Iterable
from contextlib import contextmanager
from importlib._bootstrap import spec_from_loader
from importlib.machinery import ModuleSpec
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
from nb import read_nb
from node import Node, GitNode, PathNode
import opts


class Importer:
    '''Importer providing a synthetic "gists" top-level package that allows importing `.py` and `.ipynb` files from
    GitHub Gists.'''

    DEBUG_ENV_VAR = 'UR_DEBUG'

    def __init__(self, **kw):
        self.shell = InteractiveShell.instance()
        self._print = print
        self.path = []

    def print(self, *args, **kwargs):
        if opts.verbose:
            self._print(*args, **kwargs)

    def exec_path(self, node, mod):
        nb = read_nb(node)

        # Only do something if it's a python notebook
        if nb.metadata.kernelspec.language != 'python':
            self.print("Ignoring '%s': not a python notebook." % file)
            return

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

    def load_gist_spec(self, fullname, top, mod_path):
        if not mod_path:
            # TODO: dedupe multiple top-level aliases
            self.print(f'Creating top-level "{top}" package')
            return self.spec(fullname, path=None)

        [ id, *mod_path ] = mod_path
        if id.startswith('_'):
            id = id[1:]

        from _gist import Commit, Gist

        self.print(f'Gist {id}: skip_cache={opts.skip_cache}')
        gist = Gist(id, _skip_cache=opts.skip_cache)
        commit = gist.commit
        node = GitNode(commit)
        url = gist.www_url

        if not mod_path:
            self.print(f'Building spec for gist {id}')
            return self.spec(fullname, node, origin=commit.www_url)

        return self.node_spec(fullname, node, path)

    def load_github_spec(self, fullname, top, mod_path):
        self.print(f'load_github_spec: {fullname=}')
        if not mod_path:
            self.print(f'Creating top-level "{top}" package')
            return self.spec(fullname)

        [ org, *mod_path ] = mod_path
        if org.startswith('_'): org = org[1:]
        org = org.replace('_','-')

        if not mod_path:
            self.print(f'Creating GitHub org/user "{top}.{org}" package')
            return self.spec(fullname)

        [ repo, *mod_path ] = mod_path
        if repo.startswith('_'): repo = repo[1:]
        repo = repo.replace('_','-')

        from _github import Commit, Github, Path

        id = f'{org}/{repo}'
        self.print(f'GitHub repo {id}: skip_cache={opts.skip_cache}')
        github = Github(id, _skip_cache=opts.skip_cache)
        commit = github.commit
        node = GitPath(commit)

        if not mod_path:
            self.print(f'Building module/pkg for github repo {id}, mod_path {mod_path})')
            return self.spec(fullname, node, origin=commit.www_url)

        return self.node_spec(fullname, node, mod_path)

    def spec(self, fullname, node, origin=None, pkg=True):
        spec = ModuleSpec(fullname, self, origin=origin, is_package=pkg)
        spec._node = node
        if pkg: spec.submodule_search_locations = []
        return spec

    def node_spec(self, fullname, node, mod_path, throw=True):
        self.print(f'node_spec: {node=}, {mod_path=}')
        full_path = mod_path
        while mod_path:
            [ name, *mod_path ] = mod_path
            nodes = node.children
            if name in nodes:
                node = nodes[name]
            elif not mod_path:
                    nb_path = name + '.ipynb'
                    if nb_path in nodes:
                        node = nodes[nb_path]
                    else:
                        py_path = name + '.py'
                        if py_path in nodes:
                            node = nodes[py_path]
                        elif throw:
                            raise ImportError(f'{fullname}: {name} not found in {list(nodes.keys())}')
                        else:
                            return None
            elif throw:
                raise ImportError(f'{full_path}: {name} not found in {node}: {list(nodes.keys())}')
            else:
                return None

        if isinstance(node, GitNode):
            origin = node.obj.www_url
        elif isinstance(node, PathNode):
            origin = str(node.path)
        else:
            raise ValueError(node)

        self.print(f'Creating package spec {fullname} from {node} ({origin=})')
        return self.spec(fullname, node, origin=origin, pkg=node.is_dir)

    def find_spec(self, fullname, path=None, target=None, mod_path=None):
        self.print(f'Importer.find_spec: {fullname=} {path=} {target=} {mod_path=}')
        assert not target
        # if path and not isinstance(path, Node):
        #     raise AssertionError(f'path not a Node: {path}')

        mod_path = mod_path or fullname.split('.')
        top = mod_path[0]
        if top in opts.gist_pkgs:
            return self.load_gist_spec(fullname, top, mod_path[1:])
        elif top in opts.github_pkgs:
            return self.load_github_spec(fullname, top, mod_path[1:])
        else:
            if path:
                self.print(f'find_spec received path: {path}')
                path = [ PathNode(p) for p in path ]
            elif self.path:
                self.print(f'find_spec using self.path: {self.path}')
                path = self.path
            else:
                self.print(f'find_spec using cwd')
                path = [ PathNode(Path.cwd()) ]

            for node in path:
                node_spec = self.node_spec(fullname, node, mod_path)
                if node_spec:
                    return node_spec

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

    def exec_module(self, mod, root_path=None):
        """Exec a module"""
        self.print(f'exec_module {mod}')
        spec = mod.__spec__
        node = spec._node
        self.exec(
            name=spec.name,
            mod=mod,
            node=node,
            root_path=root_path,
        )

    @contextmanager
    def tmp_path(self, path):
        try:
            prev_path = self.path.copy()
            if not isinstance(path, Iterable): path = [path]
            self.path = path + self.path
            yield
        finally:
            if self.path[:len(path)] != path:
                raise AssertionError(f'Prepended {path} to {prev_path}, but finally found {self.path}')
            self.path = self.path[1:]

    @staticmethod
    def mod_basename(name):
        basename = name.rsplit('.', 1)[0]
        if name.endswith('.ipynb'):
            return basename.replace(r'[ -]','_')
        if name.endswith('.py'):
            return basename

    def exec(self, name, mod, node, root_path=None):
        self.print(f'exec: {name=} {mod=} {node=} {root_path=}')
        dct = mod.__dict__
        if node.is_dir:
            if not root_path: root_path = [node]
            mod_name = name
            file_mods = []
            for name, child in node.children.items():
                mod_basename = self.mod_basename(name)
                if not mod_basename: continue
                fullname = f'{mod_name}.{mod_basename}'
                mod_path = [mod_basename]
                file_spec = self.find_spec(fullname, path=root_path, mod_path=mod_path)
                if file_spec:
                    self.print(f'Found spec for child module {name} ({mod_name})')
                    file_mod = self.create_module(file_spec)
                    file_mods.append(file_mod)
                    dct[name] = file_mod
                else:
                    raise ValueError(f'Failed to find spec for {name} ({child})')

            [
                self.exec_module(file_mod, root_path)
                for file_mod in file_mods
            ]
        else:
            self.print(f'Attempt to exec module {name} ({root_path=})')
            #assert root_path
            with self.tmp_path(root_path):
                if node.name.endswith('.py'):
                    self.print(f'exec .py file: {node}')
                    code = node.read_text()
                    try:
                        exec(code, dct)
                    except Exception as e:
                        stderr.write(f'Error executing module {name} ({node}):\n{code}\n')
                        raise e
                elif node.name.endswith('.ipynb'):
                    self.print(f'exec .ipynb file: {node}')
                    self.exec_path(node, mod)
