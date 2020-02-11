from pathlib import Path
from re import match
from subprocess import check_call
from urllib.parse import urlparse
from urllib.request import urlretrieve

from pclass.dircache import Meta
from pclass.field import field, directfield
from git import Repo

from regex import maybe, one


file_chars = '[A-Za-z0-9_\-\.]+'
chars = '[A-Za-z0-9_\-]+'
hexs = '[a-f0-9]+'

user_re = f'/(?P<user>{chars})'
id_re = f'(?P<id>{hexs})'
raw_re = f'(?P<raw>raw)'
commit_re = maybe(f'/(?P<commit>{hexs})')
file_re = maybe(f'/(?P<file>{file_chars})')
fragment_re = maybe(f'#(?P<fragment>{chars})')


class File:
    def __init__(self, commit, path, fragment=None):
        self.commit = commit
        self.gist = commit.gist
        self.name = path.name
        self.path = path
        self._fragment = fragment

    def __str__(self): return self.name

    def __repr__(self): return self.name

    @property
    def module_name(self): return self.name.rpartition('.')[0]

    @property
    def module_fullname(self): return f'{self.gist.module_name}.{self.module_name}'

    @property
    def fragment(self):
        if not self._fragment:
            [ self._fragment ] = [
                fragment
                for fragment, name
                in self.commit.fragments
                if name == self.name
            ]
        return self._fragment

    @property
    def url(self): return f'https://gist.githubusercontent.com/{self.gist.user}/{self.gist.id}/raw/{self.commit.id}/{self.name}'

    @property
    def web_url(self): return f'https://gist.github.com/{self.gist.user}/{self.gist.id}/{self.commit.id}#{self.fragment}'

    @property
    def blob(self):
         [ blob ] = [ blob for blob in self.commit.blobs if blob.name == self.name ]
         return blob

    @property
    def data_stream(self): return self.blob.data_stream

    def read_text(self): return self.data_stream.read().decode()


class Commit(metaclass=Meta):
    def __init__(self, gist):
        self.gist = gist

    @property
    def url(self): return f'https://gist.github.com/{self.gist.id}/{self.id}'

    @property
    def user(self): return self.gist.user

    @property
    def author(self): return self.commit.author.email

    @property
    def commit(self): return self.gist.clone.commit(self.id)

    @property
    def tree(self): return self.commit.tree

    @property
    def blobs(self): return self.tree.blobs

    @property
    def files(self):
        return [
            File(
                self,
                self.gist.clone_dir / blob.name
            )
            for blob in self.blobs
        ]

    @property
    def files_dict(self): return { file.name: file for file in self.files }

    @property
    def file_bases_dict(self): return { file.module_name: file for file in self.files }

    ### Cached fields ###

    @directfield
    def xml(self, path): urlretrieve(self.url, path)

    @xml.load
    def load_xml(self, path):
        from lxml.etree import fromstring, XMLParser
        parser = XMLParser(recover=True)
        return fromstring(path.read_text(), parser)

    @field
    def fragments(self):
        root = self.xml
        file_elems = root.cssselect('.file')
        fragments = {}
        for f in file_elems:
            [ raw_a ] = f.xpath('.//a[contains(., "Raw")]')
            raw_url_path = raw_a.attrib['href']
            file = Gist.from_url_path(raw_url_path, raw=True)
            if not isinstance(file, File):
                raise Exception(f'Unrecognized raw file URL {raw_url_path}')

            [ link ] = f.cssselect('.file-info > .css-truncate')
            fragment = link.attrib['href']
            if not fragment.startswith('#'):
                raise Exception(f'Expected file header for {file.name} to be an intra-page fragment link; found {fragment}')
            fragment = fragment[1:]

            fragments[fragment] = file.name

        return fragments


class Gist(metaclass=Meta):

    WWW_URL_PATH_REGEX = f'^{maybe(user_re)}/{id_re}{commit_re}{fragment_re}$'
    RAW_URL_PATH_REGEX = f'^{user_re}/{id_re}/{raw_re}{commit_re}{file_re}$'
    URL_PATH_REGEXS = [
        WWW_URL_PATH_REGEX,
        RAW_URL_PATH_REGEX,
    ]

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
        if domain == 'gist.github.com':
            raw = None
        elif domain == 'gist.githubusercontent.com':
            raw = True
        elif throw:
            raise Exception(f'Unrecognized Gist URL domain: {domain} ({url})')
        else:
            return None

        return cls.parse_url_path(
            u.path,
            raw=raw,
            fragment=u.fragment,
            throw=throw
        )

    @classmethod
    def parse_url_path(cls, path, raw=None, fragment=None, throw=True):
        if raw is None:
            regexs = cls.URL_PATH_REGEXS
        elif raw is False:
            regexs = [ cls.WWW_URL_PATH_REGEX ]
        elif raw is True:
            regexs = [ cls.RAW_URL_PATH_REGEX ]
        else:
            raise Exception(f'Unrecognized "raw" value: {raw}')

        m = one(regexs, path, throw=throw)
        if not m: return None

        if fragment: m['fragment'] = fragment
        return m

    @classmethod
    def from_url_path(cls, path, raw=None, fragment=None, throw=True):
        m = cls.parse_url_path(path, raw, fragment, throw)

        if fragment: m['fragment'] = fragment

        return cls.from_dict(**m)

    @classmethod
    def from_dict(cls, **m):

        id = m['id']
        gist = Gist(id)

        user = m.get('user')
        if user: assert user == gist.user

        _commit = m.get('commit')
        if _commit:
            commit = Commit(_commit, gist)
        else:
            commit = gist.commit

        _file = m.get('file')
        fragment = m.get('fragment')
        if _file:
            file = commit.files_dict[_file]
        elif fragment:
            name = commit.fragments[fragment]
            file = commit.files_dict[name]
        else:
            raw = 'raw' in m
            if raw:
                files = commit.files
                if len(files) != 1:
                    raise Exception(
                    f'File-less "raw" URL pattern disallowed unless gist contains exactly one file; {gist.url} contains {len(files)}%s' % (
                        ' (%s)' % ', '.join(files) if files else ''
                    ))
                [ file ] = files
            else:
                file = None

        if file:
            return file
        else:
            return commit

    @property
    def git_url(self): return f'https://gist.github.com/{self.id}'

    @property
    def url(self): return f'https://gist.github.com/{self.id}'

    @property
    def module_name(self):
        id = self.id
        if match('\d', id[0]):
            id = f'_{id}'

        return f'gists.{id}'

    @field
    def user(self):
        root = self.xml
        [ author_link ] = root.cssselect('.author > a')
        return author_link.text

    @property
    def xml(self): return self.commit.xml

    @directfield(parse=Repo)
    def clone(self, path):
        url = self.git_url
        print(f'Cloning {url} into {path}')
        check_call([ 'git', 'clone', url, str(path) ])

    @property
    def commit(self): return Commit(self.clone.commit().hexsha, self)

    @property
    def clone_dir(self): return Path(self.clone.git_dir).parent

    # @field
    # def fragments(self):
    #     root = self.xml
    #     file_elems = root.cssselect('.file')
    #     fragments = {}
    #     for f in file_elems:
    #         [ raw_a ] = f.xpath('.//a[contains(., "Raw")]')
    #         raw_url_path = raw_a.attrib['href']
    #         gist_url = GistURL.from_full_raw_url_path(raw_url_path)
    #
    #         [ link ] = f.cssselect('.file-info > .css-truncate')
    #         fragment = link.attrib['href']
    #         if not fragment.startswith('#'):
    #             raise Exception(f'Expected file header for {gist_url.file} to be an intra-page fragment link; found {fragment}')
    #         fragment = fragment[1:]
    #
    #         fragments[gist_url.file] = fragment
    #
    #     return fragments
