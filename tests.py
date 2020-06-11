#!/usr/bin/env bash

out = None  # directory to write executed notebooks to
kernel = '3.8.2'

from pathlib import Path
cwd = Path.cwd()
if out:
    out = Path(out)
else:
    out = cwd / 'out'

from papermill import execute_notebook
for nb in cwd.glob('*-test.ipynb'):
    print(f'Executing nb: {nb}…')
    execute_notebook(str(nb), str(out / nb.name), nest_asyncio=True, kernel_name=kernel)
