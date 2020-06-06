# Simple module for holding global options for the `ur` module
# Kept as its own module to avoid dependency cycles, as these are referenced by the `ur` module as well as modules it depends on (e.g. `gist`)
skip_cache = False
cache_root = None  # defaults to ``.objs/`` in the current directory
only_defs = True
run_nbinit = True
encoding = 'utf-8'
verbose = False
gist_pkgs = ['gist','gists']  # top-level packages to parse as importing from GitHub Gists
github_pkgs = ['github','gh']
gitlab_pkgs = ['gitlab','gl']
