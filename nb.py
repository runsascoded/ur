import nbformat
import opts
from pathlib import Path


def read_nb(node):
  nb_version = nbformat.current_nbformat
  nb = nbformat.reads(node.read_text(), nb_version, encoding=opts.encoding)
  return nb
