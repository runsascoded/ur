# Simple module for holding global options for the `ur` module
# Kept as its own module to avoid dependency cycles, as these are referenced by the `ur` module as well as modules it depends on (e.g. `gist`)
skip = False