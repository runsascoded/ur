import sys

# Finder for importing from git repos
from importer import Importer
if not any([ isinstance(importer, Importer) for importer in sys.meta_path ]):
    importer = Importer()
    sys.meta_path = [importer] + sys.meta_path


# Finder for importing local notebooks a la nbimporter
# from local_importer import NotebookFinder
# local_importer = NotebookFinder()
# if not any([ isinstance(importer, NotebookFinder) for importer in sys.meta_path ]):
#     sys.meta_path.append(local_importer)
