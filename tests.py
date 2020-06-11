#!/usr/bin/env python
# coding: utf-8

# # Run `ur` notebook tests

# In[16]:


from sys import executable as python
get_ipython().system('{python} -m pip install -q -e .')


# Papermill input params:

# In[8]:


out = None  # directory to write executed notebooks to
kernel = '3.8.2'


# Default output dir to `out/`:

# In[3]:


from pathlib import Path
cwd = Path.cwd()
if out:
    out = Path(out)
else:
    out = cwd / 'out'


# Execute notebooks:

# In[7]:


from papermill import execute_notebook
for nb in cwd.glob('*-test.ipynb'):
    print(f'Executing nb: {nb}…')
    execute_notebook(str(nb), str(out / nb.name), nest_asyncio=True, kernel_name=kernel)

