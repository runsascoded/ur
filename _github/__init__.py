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


class Commit(metaclass=Meta):
    def __init__(self, github):
        self.github = github

    @property
    def www_url(self): return f'{self.github.www_url}/tree/{self.id}'

    @property
    def author(self): return self.commit.author.email

    @property
    def commit(self): return self.github.clone.commit(self.id)

    @property
    def tree(self): return self.commit.tree

    @property
    def blobs(self): return self.tree.blobs

    @property
    def trees(self): return self.tree.trees

    @property
    def files_dict(self): return { file.name: file for file in self.files }

    @property
    def file_bases_dict(self): return { file.module_name: file for file in self.files }

    @property
    def clone_dir(self): return self.github.clone_dir


class Github(metaclass=Meta):

    WWW_URL_PATH_TREE_REGEX = f'^/{org_re}/{repo_re}{maybe(f"/tree/{commit_id_re}")}{maybe(path_re)}$'
    WWW_URL_PATH_BLOB_REGEX = f'^/{org_re}/{repo_re}{maybe(f"/blob/{commit_id_re}")}{path_re}$'
    RAW_URL_PATH_BLOB_REGEX = f'^/{org_re}/{repo_re}/{commit_id_re}{path_re}$'
    URL_PATH_REGEXS = [
      WWW_URL_PATH_TREE_REGEX,
      WWW_URL_PATH_BLOB_REGEX,
      RAW_URL_PATH_BLOB_REGEX,
    ]

    def __init__(self):
        [ self.org, self.repo ] = self.id.split('/')

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
        if domain == 'github.com':
            raw = None
        elif domain == 'raw.githubusercontent.com':
            raw = True
        elif throw:
            raise Exception(f'Unrecognized GitHub URL domain: {domain} ({url})')
        else:
            return None

        return cls.parse_url_path(
            u.path,
            raw=raw,
            throw=throw
        )

    @classmethod
    def parse_url_path(cls, path, raw=None, throw=True):
        if raw is None:
            regexs = cls.URL_PATH_REGEXS
        elif raw is False:
            regexs = [ cls.WWW_URL_PATH_TREE_REGEX, cls.WWW_URL_PATH_BLOB_REGEX ]
        elif raw is True:
            regexs = [ cls.RAW_URL_PATH_BLOB_REGEX ]
        else:
            raise Exception(f'Unrecognized "raw" value: {raw}')

        return one(regexs, path, throw=throw)

    @classmethod
    def from_url_path(cls, path, throw=True):
        m = cls.parse_url_path(path, throw)
        return cls.from_dict(**m)

    @classmethod
    def from_dict(
        cls,
        org,
        repo,
        commit=None,  # TODO: support refs
        path=None,
        skip_cache=False,
    ):
        github = Github(org, repo, _skip_cache=skip_cache)

        if commit:
            commit = Commit(commit, github)
        else:
            commit = github.commit

        if path:
            path = commit.files_dict[path]
        else:
            path = None

        if path:
            return path
        else:
            return commit

    @property
    def git_url(self): return f'https://github.com/{self.id}.git'

    @property
    def www_url(self): return f'https://github.com/{self.id}'

    @property
    def ssh_url(self): return f'git@github.com:{self.id}.git'

    @property
    def module_name(self):
        org = self.org.replace('-','_')
        if match('\d', org[0]):
            org = f'_{org}'

        repo = self.repo.replace('-','_')
        if match('\d', repo[0]):
            repo = f'_{repo}'

        return f'github.{org}.{repo}'

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
