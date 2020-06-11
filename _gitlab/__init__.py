import pathlib
from re import match
from subprocess import check_call
from urllib.parse import urlparse
from urllib.request import urlretrieve

from pclass.dircache import Meta
from pclass.field import field, directfield
from git import Repo
import opts

from rgxs import maybe, one

file_chars = '[A-Za-z0-9_\-\./]+'
chars = '[A-Za-z0-9_\-]+'
hexs = '[a-f0-9]+'

org_re = f'/(?P<org>{chars})'
repo_re = f'/(?P<repo>{chars})'
raw_re = f'(?P<raw>raw)'

commit_id_re = f'(?P<commit>{hexs})'
commit_re = maybe(f'/tree/{commit_id_re}')
path_re = f'(?P<path>/{file_chars})'


import _github

# TODO: dedupe with _github module
class Commit(_github.Commit, metaclass=Meta):
    def __init__(self, github):
        self.github = github

    @property
    def www_url(self): return f'{self.github.www_url}/tree/{self.id}'

    # @property
    # def author(self): return self.commit.author.email

    # @property
    # def commit(self): return self.gitlab.clone.commit(self.id)

    # @property
    # def tree(self): return self.commit.tree

    # @property
    # def blobs(self): return self.tree.blobs

    # @property
    # def trees(self): return self.tree.trees

    # @property
    # def files_dict(self): return { file.name: file for file in self.files }

    # @property
    # def file_bases_dict(self): return { file.module_name: file for file in self.files }

    # @property
    # def clone_dir(self): return self.gitlab.clone_dir


class Gitlab(metaclass=Meta):

    # WWW_URL_PATH_REPO_REGEX = f'^/{org_re}/{repo_re}$'
    # WWW_URL_PATH_TREE_REGEX = f'^/{org_re}/{repo_re}/-/tree/{commit_id_re}{maybe(path_re)}$'
    # WWW_URL_PATH_BLOB_REGEX = f'^/{org_re}/{repo_re}/-/blob/{commit_id_re}{path_re}$'
    # RAW_URL_PATH_BLOB_REGEX = f'^/{org_re}/{repo_re}/-/raw/{commit_id_re}{path_re}$'
    # URL_PATH_REGEXS = [
    #   WWW_URL_PATH_REPO_REGEX,
    #   WWW_URL_PATH_TREE_REGEX,
    #   WWW_URL_PATH_BLOB_REGEX,
    #   RAW_URL_PATH_BLOB_REGEX,
    # ]

    def __init__(self):
        [ *self.groups, self.repo ] = self.id.split('/')

    @classmethod
    def from_url(cls, url, throw=True):
        return cls.from_dict(
            **cls.parse_url(url, throw=throw)
        )

    @classmethod
    def parse_url(cls, url, throw=True):
        u = urlparse(url)

        if u.scheme != 'https':
            if throw:
                raise Exception(f'Invalid URL scheme: {u.scheme}')
            return None

        domain = u.netloc
        if domain == 'gitlab.com':
          pass
        elif throw:
            raise Exception(f'Unrecognized Gitlab URL domain: {domain} ({url})')
        else:
            return None

        return cls.parse_url_path(
            u.path,
            throw=throw
        )

    @classmethod
    def parse_url_path(cls, path, throw=True):
        pieces = path.split('/')[1:]
        if '-' in pieces:
            [idx] = [ idx for idx, piece in enumerate(pieces) if piece == '-' ]
            tpe = pieces[idx+1]
            if tpe not in ['blob','tree','raw']:
                raise ValueError(f'Unexpected object type: {tpe} (URL path: {path})')
            raw = tpe == 'raw'
            if raw: tpe = 'blob'
            commit = pieces[idx+2]
            repo_path = pieces[idx+3:]
        else:
            idx = len(pieces)
            raw = False
            tpe = 'tree'
            commit = None
            repo_path = []

        groups = pieces[:(idx-1)]
        project = pieces[idx-1]

        return dict(
            groups=groups,
            project=project,
            commit=commit,
            tpe=tpe,
            raw=raw,
            repo_path=repo_path,
        )

    @classmethod
    def from_url_path(cls, path, throw=True):
        m = cls.parse_url_path(path, throw)
        return cls.from_dict(**m)

    @classmethod
    def from_dict(
        cls,
        groups,
        project,
        commit,  # TODO: support refs
        tpe,
        raw,
        repo_path,
        skip_cache=False,
    ):
        github = Gitlab(groups, project, _skip_cache=skip_cache)

        if commit:
            commit = Commit(commit, gitlab)
        else:
            commit = gitlab.commit

        if path:
            path = commit.files_dict[path]
        else:
            path = None

        if path:
            return path
        else:
            return commit

    @property
    def git_url(self): return f'https://gitlab.com/{self.id}.git'

    @property
    def www_url(self): return f'https://gitlab.com/{self.id}'

    @property
    def ssh_url(self): return f'git@gitlab.com:{self.id}.git'

    @property
    def module_name(self):
        def fix(name):  # TODO: factor this out, reuse in GitHub, elsewhere
            name = name.replace('-','_')
            if match('\d', name):
                name = f'_{name}'
            return name

        return '.'.join(
            ['gitlab'] + \
            [
                fix(name)
                for name in (self.groups + [self.project])
            ]
        )

    @directfield(parse=Repo)
    def clone(self, path):
        url = self.git_url
        if path.exists():
            print(f'{path} exists; attempting to pull')
            from git import Repo
            repo = Repo(path)
            repo.remotes.origin.pull()
        else:
            print(f'Cloning {url} into {path}')
            check_call([ 'git', 'clone', url, str(path) ])

    @property
    def commit(self): return Commit(self.clone.commit().hexsha, self)

    @property
    def clone_dir(self): return pathlib.Path(self.clone.git_dir).parent


from gists import importer
