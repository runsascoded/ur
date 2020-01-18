from re import match

from regex import maybe
from gist_url import GistURL, chars

class Gist:

    def __init__(self, id, user=None):
        self.id = id
        self.user = user

    @classmethod
    def from_url(cls, url):
        maybe_user = maybe(f'(?P<user>{chars})/')
        id_re = f'(?P<id>{chars})'
        m = match(gist, f'^{maybe_user}{id_re}$')
        if not m:
            raise Exception(f'Unrecognized gist: {gist}')

        user = m.group('user')
        id = m.group('id')

        kwargs_gist_url = GistURL(id=id, user=user)

        gist_url = GistURL.from_url_path(url.path, url.fragment)
        print(f'gist_url: {gist_url}')
        if kwargs_gist_url:
            gist_url = gist_url.merge(kwargs_gist_url)
            print(f'updated gist_url: {gist_url}')

        raw_urls = gist_url.raw_urls()
        print(f'raw_urls: {raw_urls}')
        if not raw_urls:
            raise Exception(f'No raw URLs found for gist {gist_url.url}')

        if len(raw_urls) > 1:
            raise NotImplementedError('Importing gists with multiple notebooks not supported… yet!')

        [ raw_url ] = raw_urls
        # Pass through to the rest of the function
        path = raw_url
        print(f'fwding on {raw_url}: {path}')
