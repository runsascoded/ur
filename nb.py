import nbformat
import opts
from pathlib import Path


def read_nb(path):
  import _gist

  # load the notebook
  nb_version = nbformat.version_info[0]
  if isinstance(path, Path):
      with path.open('r', encoding=opts.encoding) as f:
          nb = nbformat.read(f, nb_version)
  elif isinstance(path, str):
      with open(path, 'r', encoding=opts.encoding) as f:
          nb = nbformat.read(f, nb_version)
  elif isinstance(path, _gist.File):
      nb = nbformat.read(path.data_stream, nb_version)
  else:
      raise ValueError(f'Unrecognized file type: {path} ({type(path)})')

  return nb