import ast
import sys
from importlib.machinery import ModuleSpec
from inspect import stack
from pathlib import Path
from re import match
from types import ModuleType
from urllib.parse import urlparse

import nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

from cells import CellDeleter
from node import PathNode

# Injects an `Importer`!
from gists import importer

import opts
from rgxs import maybe


def merge(l, r, *keys):
    l = l or {}
    n = l.copy()
    if not keys:
        keys = r.keys()
    for k in keys:
        if not k in r:
            continue
        rv = r[k]
        if k in l:
            lv = l[k]
            if lv != rv:
                raise Exception(f'Conflicting elem: {k} -> ({lv}, {rv})')
        else:
            n[k] = rv
    return n


class URLLoader:

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path
        self._print = print

    def print(self, *args, **kwargs):
        if opts.verbose:
            self._print(*args, **kwargs)

    def url_mod(self, url, path):
        node = PathNode(path)
        self.print(f'Forwarding URL {url} to path {path}')
        spec = importer.spec(str(url), node, origin=str(path), pkg=False)
        mod = importer.create_module(spec, install=False)
        mod = importer.exec_path(node, mod)
        return mod

    def main(
        self,
        path=None,
        *names,
        run_nbinit=True,
        all=False,
        **kwargs,
    ):
        log = self.print
        log(f'URLLoader.main({self}, path={path}, names={names}, all={all}, **{kwargs}')
        gist = kwargs.get('gist')
        github = kwargs.get('github')
        gitlab = kwargs.get('gitlab')
        pkg = kwargs.get('pkg')

        url = urlparse(path)
        if url.scheme or gist or github or gitlab:
            domain = url.netloc

            from _gist import Commit, File, Gist, chars

            gist_attrs = Gist.parse_url(path, throw=False)
            if gist_attrs or gist:
                assert not github
                assert not gitlab
                assert not pkg

                gist_attrs = merge(gist_attrs, kwargs, 'user', 'commit', 'file')
                if gist:
                    maybe_user = maybe(f'(?P<user>{chars})/')
                    id_re = f'(?P<id>{chars})'
                    m = match(f'^{maybe_user}{id_re}$', gist)
                    if not m: raise Exception(f'Unrecognized gist: {gist}')

                    user = m.group('user')
                    id = m.group('id')

                    gist_attrs = merge(gist_attrs, dict(id=id, user=user))

                log(f'gist_attrs: {gist_attrs}')
                obj = Gist.from_dict(skip_cache=opts.skip_cache, **gist_attrs)
                if isinstance(obj, Commit):
                    commit = obj
                    log(f'Parsed commit: {commit}')
                    gist = commit.gist
                    name = gist.module_name
                elif isinstance(obj, File):
                    file = obj
                    commit = file.commit
                    log(f'Parsed commit: {commit} (file {file})')
                    name = file.module_fullname
                else:
                    raise Exception(f'Unrecognized gist object: {obj}')

                if name in sys.modules:
                    mod = sys.modules[name]
                    log(f'Found loaded gist module: {mod}')
                else:
                    log(f'Loading gist module {name} (commit {commit})')
                    spec = importer.find_spec(name, commit=commit)
                    if not spec:
                        raise Exception(f'Failed to find spec for {name} (commit {commit})')

                    mod = importer.create_module(spec)
                    importer.exec_module(mod)

            elif domain == 'github.com':
                raise NotImplementedError
            elif domain == 'gitlab.com':
                raise NotImplementedError
            elif match(r'https?', url.scheme):
                from url import URL
                url = URL(path)
                # Force materialization of the URL's content to the on-disk cache
                url.content
                path = url._dir / 'content'
                mod = self.url_mod(url, path)
        else:
            mod = self.url_mod(url, path)

        if not names and not all: return mod

        dct = mod.__dict__

        if hasattr(mod, '__all__'):
            members = mod.__all__
        else:
            members = [ name for name in dct if not name.startswith('_') ]

        import_all = '*' in names or all is True or all == '*'
        if import_all:
            names = [ name for name in names if not name == '*' ]

        not_found = list(set(names).difference(members))
        if not_found:
            raise Exception('Names not found: %s' % ','.join(not_found))

        if not import_all:
            members = names

        log(f'Bubbling up {members}')
        update = { name: dct[name] for name in members }
        stk = stack()
        cur_file = stk[0].filename
        cur_dir = Path(cur_file).parent
        frame_info = next(frame for frame in stk if Path(frame.filename).parent != cur_dir)
        log(f'Frame: {frame_info}, {frame_info.filename}')
        frame_info.frame.f_globals.update(update)
        return mod
