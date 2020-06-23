import ast
from collections.abc import Iterable
from contextlib import contextmanager, nullcontext
from importlib._bootstrap import spec_from_loader
from importlib.machinery import ModuleSpec
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
import nbformat
from os import environ as env
from pathlib import Path
from re import match
from requests import head as HEAD
import sys
from sys import stderr
from types import ModuleType
from urllib.parse import quote_plus

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

    def load_gist_spec(self, fullname, top, mod_path, commit=None):
        if not mod_path:
            # TODO: dedupe multiple top-level aliases
            self.print(f'Creating top-level "{top}" package')
            return self.spec(fullname, node=None)

        [ id, *mod_path ] = mod_path
        if id.startswith('_'):
            id = id[1:]

        from _gist import Gist

        if commit:
            self.print(f'Gist {id} (specified commit {commit}): skip_cache={opts.skip_cache}')
        else:
            gist = Gist(id, _skip_cache=opts.skip_cache)
            commit = gist.commit
            self.print(f'Gist {id} (default commit {commit}): skip_cache={opts.skip_cache}')

        node = GitNode(commit)
        url = node.url

        if not mod_path:
            self.print(f'Building spec for gist {id}')
            return self.spec(fullname, node, origin=url)

        return self.node_spec(fullname, node, mod_path)

    def load_github_spec(self, fullname, top, mod_path):
        self.print(f'load_github_spec: fullname={fullname}')
        if not mod_path:
            self.print(f'Creating top-level "{top}" package')
            return self.spec(fullname, None)

        [ org, *mod_path ] = mod_path
        if org.startswith('_'): org = org[1:]
        org = org.replace('_','-')

        if not mod_path:
            self.print(f'Creating GitHub org/user "{top}.{org}" package')
            return self.spec(fullname, None)

        [ repo, *mod_path ] = mod_path
        if repo.startswith('_'): repo = repo[1:]
        repo = repo.replace('_','-')

        from _github import Github

        id = f'{org}/{repo}'
        self.print(f'GitHub repo {id}: skip_cache={opts.skip_cache}')
        github = Github(id, _skip_cache=opts.skip_cache)
        commit = github.commit
        node = GitNode(commit)

        if not mod_path:
            self.print(f'Building module/pkg for github repo {id}, mod_path {mod_path})')
            return self.spec(fullname, node, origin=commit.www_url)

        return self.node_spec(fullname, node, mod_path)

    def load_gitlab_spec(self, fullname, top, mod_path):
        self.print(f'load_gitlab_spec: fullname={fullname}')
        if not mod_path:
            self.print(f'Creating top-level "{top}" package')
            return self.spec(fullname, None)

        from sys import modules
        mod = modules[top]
        groups = []
        project = None
        while mod_path:
            [ group, *mod_path ] = mod_path
            if group.startswith('_'): org = org[1:]
            groups.append(group)
            groups_str = quote_plus('/'.join(groups))
            url = f'https://gitlab.com/api/v4/groups/{groups_str}'
            resp = HEAD(url)
            if not resp.ok:
                url = f'https://gitlab.com/api/v4/projects/{groups_str}'
                resp = HEAD(url)
                if not resp.ok:
                    raise ValueError(f"Request failed for {groups_str} ({groups}) as group and project")

                project = groups[-1]
                groups = groups[:-1]
                break

        if not project:
            assert not mod_path
            self.print(f'Creating GitLab group "{top}.{".".join(groups)}" package')
            return self.spec(fullname, None)

        id = '/'.join(groups + [project])
        from _gitlab import Gitlab
        self.print(f'GitLab repo {id}: skip_cache={opts.skip_cache}')
        gitlab = Gitlab(id, _skip_cache=opts.skip_cache)
        commit = gitlab.commit
        node = GitNode(commit)

        if not mod_path:
            self.print(f'Building module/pkg for gitlab repo {id}, mod_path {mod_path})')
            return self.spec(fullname, node, origin=commit.www_url)

        return self.node_spec(fullname, node, mod_path)

    def spec(self, fullname, node, origin=None, pkg=True):
        spec = ModuleSpec(fullname, self, origin=str(origin), is_package=pkg)
        spec._node = node
        if pkg: spec.submodule_search_locations = []
        return spec

    def node_spec(self, fullname, node, mod_path, throw=True):
        self.print(f'node_spec: node={node}, mod_path={mod_path}')
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
            origin = str(node.url)
        elif isinstance(node, PathNode):
            origin = str(node.path)
        else:
            raise ValueError(node)

        self.print(f'Creating package spec {fullname} from {node} (origin={origin})')
        return self.spec(fullname, node, origin=origin, pkg=node.is_dir)

    def find_spec(self, fullname, path=None, target=None, mod_path=None):
        self.print(f'Importer.find_spec: fullname={fullname} path={path} target={target} mod_path={mod_path}')
        assert not target

        mod_path = mod_path or fullname.split('.')
        top = mod_path[0]
        if top in opts.gist_pkgs:
            if path and len(path) == 1 and isinstance(path[0], GitNode):
                commit = path[0]
            else:
                commit = None
            return self.load_gist_spec(fullname, top, mod_path[1:], commit=commit)
        elif top in opts.github_pkgs:
            return self.load_github_spec(fullname, top, mod_path[1:])
        elif top in opts.gitlab_pkgs:
            return self.load_gitlab_spec(fullname, top, mod_path[1:])
        else:
            if path:
                self.print(f'find_spec received path: {path}')
                path = [ PathNode(p) for p in path ]
            else:
                path = []

            if self.path:
                self.print(f'find_spec adding self.path: {self.path}')
                path = path + self.path

            path += [ PathNode(Path.cwd()) ]

            try:
                from git import Repo
                repo = Repo(search_parent_directories=True)
                path += [ PathNode(repo.working_dir) ]
            except Exception as e:
                stderr.write(f'No repo found from {Path.cwd()}\n')

            for node in path:
                node_spec = self.node_spec(fullname, node, mod_path, throw=False)
                if node_spec:
                    return node_spec

            self.print(f'Returning without finding spec: fullname={fullname} mod_path={mod_path} path={path}')

    def create_module(self, spec, install=True):
        """Create a built-in module"""
        self.print(f'create_module {spec}')
        mod = ModuleType(spec.name)
        mod.__file__ = spec.origin
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        mod.__spec__ = spec

        if install:
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
            self.print(f'Prepending Importer tmp_path: {path}')
            self.path = path + self.path
            yield
        finally:
            if self.path[:len(path)] != path:
                raise AssertionError(f'Prepended {path} to {prev_path}, but finally found {self.path}')
            self.print(f'Popping Importer tmp_path: {path[0]}')
            self.path = self.path[1:]

    @staticmethod
    def mod_basename(name):
        basename = name.rsplit('.', 1)[0]
        if name.endswith('.ipynb'):
            return basename.replace(r'[ -]','_')
        if name.endswith('.py'):
            return basename

    def exec(self, name, mod, node, root_path=None):
        self.print(f'exec: name={name} mod={mod} node={node} root_path={root_path}')
        dct = mod.__dict__
        if not node: return
        if node.is_dir:
            if not root_path: root_path = [node]
            mod_name = name
            children = node.children
            if '__init__.py' in children:
                self.print(f'{mod}: executing __init__.py')
                self.exec(name, mod, children['__init__.py'], root_path=root_path)

            if '__all__' in mod.__dict__:
                all = mod.__dict__['__all__']
                children = { k: children[k] for k in children if self.mod_basename(k) in all }
                self.print(f'{mod}: restricting children based on __all__: {list(children.keys())}')

            for name, child in children.items():
                mod_basename = self.mod_basename(name)
                if not mod_basename: continue
                if mod_basename == '__init__': continue
                fullname = f'{mod_name}.{mod_basename}'
                mod_path = [mod_basename]
                file_spec = self.find_spec(fullname, path=root_path, mod_path=mod_path)
                if file_spec:
                    self.print(f'Found spec for child module {name} ({mod_name})')
                    file_mod = self.create_module(file_spec)
                    dct[mod_basename] = file_mod
                    self.exec_module(file_mod, root_path)
                else:
                    raise ValueError(f'Failed to find spec for {name} ({child})')
        else:
            self.print(f'Attempt to exec module {name} (root_path={root_path})')
            if root_path:
                ctx = self.tmp_path(root_path)
            else:
                ctx = nullcontext()
            with ctx:
                if node.name.endswith('.py'):
                    self.print(f'exec .py file: {node}')
                    code = node.read_text()
                    try:
                        pyc = compile(code, node.url, 'exec')
                        exec(pyc, dct)
                    except Exception as e:
                        stderr.write(f'Error executing module {name} ({node}):\n{code[:1000]}\n')
                        raise e
                elif node.name.endswith('.ipynb'):
                    self.print(f'exec .ipynb file: {node}')
                    self.exec_path(node, mod)
