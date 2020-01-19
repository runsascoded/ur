from subprocess import check_call
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve

from nbimporter import nbimporter
from cached_objs import Meta, field
from git import Repo

from gist_url import GistURL


class File:
    def __init__(self, gist, path):
        self.gist = gist
        self.name = path.name
        self.path = path
        self._contents = None

    @property
    def contents(self):
        if not self._contents:
            self._contents = self.path.read_text()
        return self._contents

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def url(self):
        return f'https://gist.githubusercontent.com/{self.gist.user}/{self.gist.id}/raw/{self.name}'

    def web_url(self):
        return f'https://gist.github.com/{self.gist.user}/{self.gist.id}#file-a_b-ipynb'


class Gist(metaclass=Meta):

    @property
    def git_url(self):
        return f'git@gist.github.com:{self.id}.git'

    @field
    def url(self):
        return f'https://gist.github.com/{self.id}'

    @field
    def user(self):
        root = self.xml
        [ author_link ] = root.cssselect('.author > a')
        return author_link.text

    @field
    def xml(self):
        from lxml.etree import fromstring, XMLParser
        parser = XMLParser(recover=True)
        with NamedTemporaryFile() as f:
            urlretrieve(self.url, f.name)
            return fromstring(f.read(), parser)

    @field
    def author(self):
        return self.clone.active_branch.commit.author.email

    @field(
        load=lambda path, **_: Repo(path),
        save=lambda path, repo, **_: None
    )
    def clone(self):
        url = self.git_url
        dest = self.cloned_dir
        print(f'Cloning {url} into {dest}')
        check_call([ 'git', 'clone', url, str(dest) ])
        return Repo(dest)

    @property
    def cloned_dir(self):
        return self._dir / 'clone'

    @property
    def files(self):
        return [ File(self, file) for file in self.cloned_dir.iterdir() ]

    @property
    def files_dict(self):
        return { file.name: file for file in self.files }

    @property
    def file_bases_dict(self):
        return { k.rpartition('.')[0]: v for k, v in self.files_dict.items() }

    @field
    def fragments(self):
        root = self.xml
        file_elems = root.cssselect('.file')
        fragments = {}
        for f in file_elems:
            [ raw_a ] = f.xpath('.//a[contains(., "Raw")]')
            raw_url_path = raw_a.attrib['href']
            gist_url = GistURL.from_full_raw_url_path(raw_url_path)

            [ link ] = f.cssselect('.file-info > .css-truncate')
            fragment = link.attrib['href']
            if not fragment.startswith('#'):
                raise Exception(f'Expected file header for {gist_url.file} to be an intra-page fragment link; found {fragment}')
            fragment = fragment[1:]

            fragments[gist_url.file] = fragment

        return fragments
