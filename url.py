from functools import cached_property
from io import BytesIO
import json
from pathlib import Path
from pclass.dircache import Meta
from pclass.field import directfield
from urllib.request import urlretrieve


class URL(metaclass=Meta):
  @directfield
  def content(self, path):
    url = self.id
    print(f'Fetching URL: {url} to {path}')
    urlretrieve(url, path)

  @content.load
  def load_content(self, path):
    if isinstance(path, Path):
      return path.open('rb')
    return open(path, 'rb')

  @property
  def json(self):
    with self.content as f:
      return json.load(f)

  @property
  def text(self):
    with self.content as f:
      return f.read().decode()

  def __str__(self):
    return f'URL(id={self.id})'