from re import match
from tempfile import NamedTemporaryFile
from typing import NamedTuple
from urllib.request import urlretrieve


def maybe(re):
    return f'(?:{re})'


chars = '[A-Za-z\-_0-9]+'
hexs = '[a-f0-9]+'

user_re = maybe(f'(?P<user>{chars})')
id_re = f'(?P<id>{hexs})'
raw_re = f'(?P<raw>raw)'
tree_re = maybe(f'(?P<tree>{hexs})')
file_re = maybe(f'(?P<file>{chars})')
fragment_re = maybe(f'(?P<fragment>{chars})')

full_raw_url_path = f'/{user_re}/{id_re}/{raw_re}/{tree_re}/{file_re}'

regexs = [
    f'/{user_re}/{id_re}',
    f'/{user_re}/{id_re}#{fragment_re}',
    f'/{user_re}/{id_re}/{tree_re}',
    f'/{user_re}/{id_re}/{tree_re}#{fragment_re}',
    f'/{user_re}/{id_re}/{raw_re}',
    f'/{user_re}/{id_re}/{raw_re}/{file_re}',
    f'/{user_re}/{id_re}/{raw_re}/{tree_re}',
    full_raw_url_path,
]

class GistURL(NamedTuple):
    id: str
    user: str = None
    tree: str = None
    file: str = None
    fragment: str = None
    raw: bool = False

    def merge(l, r):
        self = l
        l = l._asdict()
        r = r._asdict()
        for k, rv in r.items():
            if k in l:
                lv = l[k]
                if lv != rv:
                    raise Exception(f"Attempting to overwrite {k} ({lv} -> {rv}; gist {self})")
            else:
                l[k] = rv

        return GistURL(**l)

    @property
    def url(i):
        if i.raw:
            if not i.user:
                raise Exception(f"Can't build raw URL for {i} with no user set")

            url =  f'https://gist.github.com/{i.user}/{i.id}/raw'
            if i.tree: url += f'/{i.tree}'
            if i.file: url += f'/{i.file}'
            return url
        else:
            url =  f'https://gist.github.com'
            if i.user: url += f'/{i.user}'
            url += f'/{i.id}'
            if i.tree: url += f'/{i.tree}'
            if i.fragment: url += f'#{i.fragment}'
            return url

    @classmethod
    def from_full_raw_url_path(cls, path):
        m = match(full_raw_url_path, path)
        if not m:
            raise Exception(f'Unrecognized raw URL: {path}')

        return GistURL(**m.groupdict())

    @classmethod
    def from_url_path(cls, path):
        matches = [ (match(regex, path).groupdict(), regex) for regex in regexs ]
        matches = [ m for m in matches if m ]
        if not matches:
            raise Exception(f'Failed to parse gist.github.com URL: {path}')
        num_matches = len(matches)
        if num_matches > 1:
            raise Exception(
                f'Ambiguous parse of gist.github.com URL {path}:\n%s' % (
                    '\n\t'.join([
                        str(m)
                        for m, _ in matches
                    ])
                )
            )

        [ (m, _) ] = matches
        return GistURL(
            id = m['id'],
            user = m.get('user'),
            tree = m.get('tree'),
            file = m.get('file'),
        )

    def raw_urls(self):
        url = self.url
        if self.raw:
            return [ url ]

        from lxml.etree import fromstring, XMLParser
        parser = XMLParser(recover=True)
        with NamedTemporaryFile() as f:
            urlretrieve(url, f.name)
            root = fromstring(f.read(), parser)

        file_elems = root.cssselect('.file')
        files = {}
        for f in file_elems:
            [ raw_a ] = f.xpath('.//a[contains(., "Raw")]')
            raw_url_path = raw_a.attrib['href']
            gist_url = GistURL.from_full_raw_url_path(raw_url_path)

            [ link ] = f.cssselect('.file-info > .css-truncate')
            fragment = link.attrib['href']

            files[gist_url.file] = dict(gist_url=gist_url, fragment=fragment,)

        if self.file:
            if self.file not in files:
                raise Exception(f'File {self.file} not found in {url}')
            return [ files[self.file]['gist_url'].url ]
        if self.fragment:
            matches = [ v['gist_url'] for _, v in files.items() if v['fragment'] == self.fragment ]
            if not matches:
                raise Exception(f'Fragment {self.fragment} not found in {url}')
            return [ gist_url.url for gist_url in matches ]

        return [ v['gist_url'].url for _, v in files.items() ]
