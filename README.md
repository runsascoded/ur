# ur

> *ur- (combining form): primitive, original, or earliest*
 
*Universal Resources*: import remote Python files and Jupyter notebooks, from GitHub Gists, the local filesystem, or arbitrary URLs.

<table>
  <tr>
    <th colspan="2" rowspan="2"></th>
    <th colspan="5" align="center" style="text-align:center">
      <b>Import From</b>
    </th>
  </tr>
  <tr>
    <th>
      <b>Gists</b>
    </th>
    <th>
      <b>URLs</b>
    </th>
    <th>
      <b>Local files</b>
    </th>
    <th>
      <b>GitHub</b>
    </th>
    <th>
      <b>GitLab</b>
    </th>
  </tr>
  <tr>
    <td rowspan="2">
      <b>File Type</b>
    </td>
    <td align="right">
      <b>Notebook (.ipynb)</b>
    </td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">🚧</td>
    <td align="right">🚧</td>
  </tr>
  <tr>
    <td align="right">
      <b>Python (.py)</b>
    </td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">🚧</td>
    <td align="right">🚧</td>
  </tr>
</table>

--------

- [**Install**](#install)
- [**Usage**](#usage)
  - [Import GitHub Gists](#gists)
  - [Import arbitrary URLs](#urls)
  - [Configuration: `ur.opts`](#configs)
- [**Discussion**](#discussion)
  - ["package-less publishing"](#package-less)
  - ["anyone with the link can view" git repositories](#link-visibility)
  - [Use-case: portable, shareable "dotfiles"](#dotfiles)
  - [Future work](#future-work)
    - [Customize import behavior](#Customize-import-behavior)
    - [Usability](#Usability)
    - [Import Sources](#Import-Sources)
    - [Project Management](#Project-Management)

## Install: <a id="install"></a>
```bash
pip install ur
```
Or, in a Jupyter notebook:


```python
from sys import executable as python
!{python} -m pip install ur
```

    [33mWARNING: The directory '/github/home/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you may want sudo's -H flag.[0m
    Collecting ur
      Downloading ur-0.1.3.tar.gz (18 kB)
    Collecting jupyter
      Downloading jupyter-1.0.0-py2.py3-none-any.whl (2.7 kB)
    Requirement already satisfied: nbformat==4.4.0 in /usr/local/lib/python3.8/site-packages (from ur) (4.4.0)
    Collecting GitPython
      Downloading GitPython-3.1.3-py3-none-any.whl (451 kB)
    [K     |████████████████████████████████| 451 kB 11.8 MB/s 
    [?25hCollecting lxml
      Downloading lxml-4.5.1-cp38-cp38-manylinux1_x86_64.whl (5.4 MB)
    [K     |████████████████████████████████| 5.4 MB 42.5 MB/s 
    [?25hCollecting cssselect
      Downloading cssselect-1.1.0-py2.py3-none-any.whl (16 kB)
    Collecting notebook
      Downloading notebook-6.0.3-py3-none-any.whl (9.7 MB)
    [K     |████████████████████████████████| 9.7 MB 97.3 MB/s 
    [?25hRequirement already satisfied: nbconvert in /usr/local/lib/python3.8/site-packages (from jupyter->ur) (5.6.1)
    Collecting jupyter-console
      Downloading jupyter_console-6.1.0-py2.py3-none-any.whl (21 kB)
    Collecting qtconsole
      Downloading qtconsole-4.7.4-py2.py3-none-any.whl (118 kB)
    [K     |████████████████████████████████| 118 kB 101.3 MB/s 
    [?25hCollecting ipywidgets
      Downloading ipywidgets-7.5.1-py2.py3-none-any.whl (121 kB)
    [K     |████████████████████████████████| 121 kB 96.6 MB/s 
    [?25hRequirement already satisfied: ipykernel in /usr/local/lib/python3.8/site-packages (from jupyter->ur) (5.3.0)
    Requirement already satisfied: jupyter-core in /usr/local/lib/python3.8/site-packages (from nbformat==4.4.0->ur) (4.6.3)
    Requirement already satisfied: jsonschema!=2.5.0,>=2.4 in /usr/local/lib/python3.8/site-packages (from nbformat==4.4.0->ur) (3.2.0)
    Requirement already satisfied: traitlets>=4.1 in /usr/local/lib/python3.8/site-packages (from nbformat==4.4.0->ur) (4.3.3)
    Requirement already satisfied: ipython-genutils in /usr/local/lib/python3.8/site-packages (from nbformat==4.4.0->ur) (0.2.0)
    Collecting gitdb<5,>=4.0.1
      Downloading gitdb-4.0.5-py3-none-any.whl (63 kB)
    [K     |████████████████████████████████| 63 kB 34.8 MB/s 
    [?25hCollecting prometheus-client
      Downloading prometheus_client-0.8.0-py2.py3-none-any.whl (53 kB)
    [K     |████████████████████████████████| 53 kB 62.0 MB/s 
    [?25hCollecting Send2Trash
      Downloading Send2Trash-1.5.0-py3-none-any.whl (12 kB)
    Requirement already satisfied: jupyter-client>=5.3.4 in /usr/local/lib/python3.8/site-packages (from notebook->jupyter->ur) (6.1.3)
    Requirement already satisfied: tornado>=5.0 in /usr/local/lib/python3.8/site-packages (from notebook->jupyter->ur) (6.0.4)
    Requirement already satisfied: jinja2 in /usr/local/lib/python3.8/site-packages (from notebook->jupyter->ur) (2.11.2)
    Requirement already satisfied: pyzmq>=17 in /usr/local/lib/python3.8/site-packages (from notebook->jupyter->ur) (19.0.1)
    Collecting terminado>=0.8.1
      Downloading terminado-0.8.3-py2.py3-none-any.whl (33 kB)
    Requirement already satisfied: mistune<2,>=0.8.1 in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (0.8.4)
    Requirement already satisfied: pygments in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (2.6.1)
    Requirement already satisfied: bleach in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (3.1.5)
    Requirement already satisfied: defusedxml in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (0.6.0)
    Requirement already satisfied: testpath in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (0.4.4)
    Requirement already satisfied: pandocfilters>=1.4.1 in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (1.4.2)
    Requirement already satisfied: entrypoints>=0.2.2 in /usr/local/lib/python3.8/site-packages (from nbconvert->jupyter->ur) (0.3)
    Requirement already satisfied: prompt-toolkit!=3.0.0,!=3.0.1,<3.1.0,>=2.0.0 in /usr/local/lib/python3.8/site-packages (from jupyter-console->jupyter->ur) (3.0.5)
    Requirement already satisfied: ipython in /usr/local/lib/python3.8/site-packages (from jupyter-console->jupyter->ur) (7.15.0)
    Collecting qtpy
      Downloading QtPy-1.9.0-py2.py3-none-any.whl (54 kB)
    [K     |████████████████████████████████| 54 kB 65.9 MB/s 
    [?25hCollecting widgetsnbextension~=3.5.0
      Downloading widgetsnbextension-3.5.1-py2.py3-none-any.whl (2.2 MB)
    [K     |████████████████████████████████| 2.2 MB 94.8 MB/s 
    [?25hRequirement already satisfied: attrs>=17.4.0 in /usr/local/lib/python3.8/site-packages (from jsonschema!=2.5.0,>=2.4->nbformat==4.4.0->ur) (19.3.0)
    Requirement already satisfied: six>=1.11.0 in /usr/local/lib/python3.8/site-packages (from jsonschema!=2.5.0,>=2.4->nbformat==4.4.0->ur) (1.15.0)
    Requirement already satisfied: setuptools in /usr/local/lib/python3.8/site-packages (from jsonschema!=2.5.0,>=2.4->nbformat==4.4.0->ur) (46.4.0)
    Requirement already satisfied: pyrsistent>=0.14.0 in /usr/local/lib/python3.8/site-packages (from jsonschema!=2.5.0,>=2.4->nbformat==4.4.0->ur) (0.16.0)
    Requirement already satisfied: decorator in /usr/local/lib/python3.8/site-packages (from traitlets>=4.1->nbformat==4.4.0->ur) (4.4.2)
    Collecting smmap<4,>=3.0.1
      Downloading smmap-3.0.4-py2.py3-none-any.whl (25 kB)
    Requirement already satisfied: python-dateutil>=2.1 in /usr/local/lib/python3.8/site-packages (from jupyter-client>=5.3.4->notebook->jupyter->ur) (2.8.1)
    Requirement already satisfied: MarkupSafe>=0.23 in /usr/local/lib/python3.8/site-packages (from jinja2->notebook->jupyter->ur) (1.1.1)
    Requirement already satisfied: ptyprocess; os_name != "nt" in /usr/local/lib/python3.8/site-packages (from terminado>=0.8.1->notebook->jupyter->ur) (0.6.0)
    Requirement already satisfied: packaging in /usr/local/lib/python3.8/site-packages (from bleach->nbconvert->jupyter->ur) (20.4)
    Requirement already satisfied: webencodings in /usr/local/lib/python3.8/site-packages (from bleach->nbconvert->jupyter->ur) (0.5.1)
    Requirement already satisfied: wcwidth in /usr/local/lib/python3.8/site-packages (from prompt-toolkit!=3.0.0,!=3.0.1,<3.1.0,>=2.0.0->jupyter-console->jupyter->ur) (0.2.3)
    Requirement already satisfied: pexpect; sys_platform != "win32" in /usr/local/lib/python3.8/site-packages (from ipython->jupyter-console->jupyter->ur) (4.8.0)
    Requirement already satisfied: jedi>=0.10 in /usr/local/lib/python3.8/site-packages (from ipython->jupyter-console->jupyter->ur) (0.17.0)
    Requirement already satisfied: pickleshare in /usr/local/lib/python3.8/site-packages (from ipython->jupyter-console->jupyter->ur) (0.7.5)
    Requirement already satisfied: backcall in /usr/local/lib/python3.8/site-packages (from ipython->jupyter-console->jupyter->ur) (0.1.0)
    Requirement already satisfied: pyparsing>=2.0.2 in /usr/local/lib/python3.8/site-packages (from packaging->bleach->nbconvert->jupyter->ur) (2.4.7)
    Requirement already satisfied: parso>=0.7.0 in /usr/local/lib/python3.8/site-packages (from jedi>=0.10->ipython->jupyter-console->jupyter->ur) (0.7.0)
    Building wheels for collected packages: ur
      Building wheel for ur (setup.py) ... [?25l- done
    [?25h  Created wheel for ur: filename=ur-0.1.3-py3-none-any.whl size=17207 sha256=25a1ef9ef2128df1839344c2fb781e68c9e50bb4cbc6d8e29eb88b35d61b55da
      Stored in directory: /tmp/pip-ephem-wheel-cache-zvjbyw84/wheels/f5/89/df/4ff2ee970a3439f6fb80f7dfa1f9c43bfac77c9f010e517712
    Successfully built ur
    Installing collected packages: prometheus-client, Send2Trash, terminado, notebook, jupyter-console, qtpy, qtconsole, widgetsnbextension, ipywidgets, jupyter, smmap, gitdb, GitPython, lxml, cssselect, ur
    Successfully installed GitPython-3.1.3 Send2Trash-1.5.0 cssselect-1.1.0 gitdb-4.0.5 ipywidgets-7.5.1 jupyter-1.0.0 jupyter-console-6.1.0 lxml-4.5.1 notebook-6.0.3 prometheus-client-0.8.0 qtconsole-4.7.4 qtpy-1.9.0 smmap-3.0.4 terminado-0.8.3 ur-0.1.3 widgetsnbextension-3.5.1


## Usage <a id="usage"></a>

### Import GitHub Gists <a id="gists"></a>


```python
from gist._1288bff2f9e05394a94312010da267bb import *
a_b.a(), a_b.b(), c.c()
```

    Cloning https://gist.github.com/1288bff2f9e05394a94312010da267bb into .objs/Gist/1288bff2f9e05394a94312010da267bb/clone





    ('aaa', 'bbb', 'ccc')



That imports 2 Jupyter notebooks from https://gist.github.com/1288bff2f9e05394a94312010da267bb (note the leading underscore in the `import` statement, which is necessary when the Gist ID begins with a number), and calls functions defined in them.

### Import arbitrary URLs <a id="urls"></a>
The `ur` module exposes a powerful API for importing code from {local,remote} {`.py`,`.ipynb`} files.

Here is an example directly importing one of the files in [the example gist used above](https://gist.github.com/ryan-williams/1288bff2f9e05394a94312010da267bb):


```python
import ur
a_b = ur('https://gist.githubusercontent.com/ryan-williams/1288bff2f9e05394a94312010da267bb/raw/a_b.ipynb')
a_b.a(), a_b.b()
```




    ('aaa', 'bbb')



#### Import wildcards

In addition to calling the `ur` module (and returning a module), the `*` operator can be used:


```python
import ur
ur * 'https://gist.github.com/1288bff2f9e05394a94312010da267bb'
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')



This is is analogous to `import *` syntax, but can be used to import from arbitrary URLs (in this case, `ur` detects that the URL represents a gist, and imports the two `.ipynb` modules found there).

Here is an equivalent import using the `ur(…)` syntax:


```python
import ur
ur(gist='1288bff2f9e05394a94312010da267bb', all='*')
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')




```python
import ur
url = 'https://gist.githubusercontent.com/ryan-williams/1288bff2f9e05394a94312010da267bb/raw/0a2b5966c22c5461734063b78239262e39e4f363/c.ipynb'
ur(url, all=True)
c()
```




    'ccc'



### Configuration: `ur.opts` <a id="configs"></a>
Various behaviors can be configured via the `ur.opts` object:

#### `only_defs` <a id="config.only_defs"></a>
Default: `True`

Only bring certain top-level entities (functions, modules, and imported symbols; see [`CellDeleter`](./cells.py)) into scope from the imported module.

#### `verbose` <a id="config.verbose"></a>
Default: `False`
Eenable verbose logging during import magic

#### `skip_cache` <a id="config.skip_cache"></a>
Default: `False`

When set, pull latest versions of imported modules (instead of reusing Git clones cached by previous runs).

#### `cache_root` <a id="config.cache_root"></a>
Default `.objs`

Remote imported modules are cloned and cached here, namespaced by their type and a primary key.

For example, the example Gist referenced above will persist information in a directory called `.objs/Gist/1288bff2f9e05394a94312010da267bb`.

[`cache-root-example.ipynb`](./cache-root-example.ipynb) shows how to set a non-default `cache_root`, and what the cache dir's contents look like.

#### `encoding` <a id="config.encoding"></a>
Default: `utf-8`

Encoding to decode remote notebooks with.

## Discussion <a id="discussion"></a>
Jupyter notebooks provide a rich, literate programming experience that is preferable to conventional IDE-based Python environments in many ways.

However, conventional wisdom is that reusing code in notebooks requires porting it to `.py` files. This is tedious and often requires trashing some of what makes notebooks great in the first place (rich, inline documentation, easy reproducibility, etc.).

Jupyter itself provides [sample code for importing code from (local) Jupyter notebooks](https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Importing%20Notebooks.html) ([originally from 2014?](https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb)), and [several](https://github.com/marella/nbimport) [packages](https://github.com/rileyedmunds/import-ipynb), [repositories](https://github.com/ipython/ipynb), [blog posts](https://vispud.blogspot.com/2019/02/ipynb-import-another-ipynb-file.html), [and](https://github.com/jupyter/notebook/issues/1588) [issues](https://github.com/jupyter/notebook/issues/3479) have built on and published similar code.

[nbimporter](https://github.com/grst/nbimporter) (which this repo is a fork of) is perhaps most notable, allowing seamless reuse of Jupyter-resident utilities within single projects, but [its author now recommends factoring code out to `.py` modules](https://github.com/grst/nbimporter/blob/0fc2bdf458005be742090f67c306a4e3bcc04e77/README.md#update-2019-06-i-do-not-recommend-any-more-to-use-nbimporter).

The Jupyter ecosystem increasingly shines for the ease with which it allows of publishing and sharing notebooks, and stands to gain a lot from easier remixing+reuse of the wealth of code and data being published in Jupyter notebooks every day. I believe there are straightforward answers to [the reproducibility and testability concerns raised in `nbimporter`](https://github.com/grst/nbimporter/blob/0fc2bdf458005be742090f67c306a4e3bcc04e77/README.md#why), and built the `ur` package to bear that out (and solve immediate productivity and code-reuse needs in my day-to-day life).

### Remote importing: package-less publishing <a id="package-less"></a>
An animating idea of `ur` is that publishing+reusing a useful helper function should be no harder than
Reuse of code in Jupyter notebooks should be made as easy as possible. Users shouldn't have to mangle their utility-code and then publish it to Pip repositories in order to avoid copy/pasting standard helpers in every notebook/project they work in.

Importing code directly from remote Notebooks (or `.py` files) allows frictionless code reuse beyond what Python/Jupyter users are offered today.

### GitHub Gists: "anyone with the link can view" git repositories <a id="link-visibility"></a>
`ur` particularly emphasizes using and importing from [GitHub Gists](https://help.github.com/en/enterprise/2.13/user/articles/about-gists). Like `git` itself, Gists combine a few simple but powerful concepts orthogonally, forming a great platform for sharing and tracking code:
- Gists are the only service I'm aware of that allows "publishing" a Git repository to an opaque URL that can be easily shared, but is otherwise (cryptographically, I think?) private, not search-indexed, etc.
  - [GitLab snippets](https://docs.gitlab.com/ee/user/snippets.html) are a comparable product, but [a request for this feature is open at time of writing](https://gitlab.com/gitlab-org/gitlab/issues/14201)
- Each Gist is backed by a full Git repository, under the hood
  - Gists can therefore track changes to many files over time
  - Users can choose to view Gists' "latest `HEAD`" content (the default on https://gist.github.com), or specify frozen Git-SHA permalinks for guaranteed reproducibility
    - both "modes" are supported via web browser, Git CLI, or [GitHub API](https://developer.github.com/v3/gists/#get-a-single-gist)
- Many CLIs and SDKs exist for interacting with Gists from different languages/environments
  - [I previously wrote a `gist-dir` helper](https://github.com/defunkt/gist/issues/191#issuecomment-569572229) that uploads an entire directory as a Gist (also working around issues with binary data that the Gist API normally doesn't handle correctly)

### Use-case: portable, shareable "dotfiles" <a id="dotfiles"></a>
Something that `ur` makes easy is boilerplate-free reuse of common imports and aliases across notebooks/projects/users.

For example, "everyone" imports `numpy as np`, `pandas as pd`, `plotly as pl`, etc. I have a few that I like in addition: `from os import environ as env`, `from sys import python as executable`, etc.

`ur` offers several minimal-boilerplate ways to let you (and anyone you share your notebook with) use all the helpers you like, portably, without having to redeclare them or otherwise interfere with the environment you originally used them in:

```python
import ur
ur(github='ryan-williams/dotfiles', tree='v1.0', file='dotfiles.ipynb', all='*')
```

Many versions of this can be used, depending on your preferences, e.g.:

```python
from gist.abcdef0123456789abcdef0123456789 import *
```

### Future work <a id="future-work"></a>

#### Customize import behavior
- [x] test/handle intra-gist imports
- [ ] test/handle pip dependencies in gist imports
- [ ] API for tagging/skipping cells in notebooks (visualizations, tests, etc.)
- [ ] work with `importlib.reload`
- [ ] support `__init__.ipynb` (automatically load notebook when loading Gist), `__all__` (configure `import *` behavior)
- [ ] more nuanced TTL / `skip_cache` behavior (e.g. let cached URLs time-out appropriately based on HTTP headers, a la [`requests-cache`](https://pypi.org/project/requests-cache/))

#### Usability
- [ ] pretty-print info about what's imported (in notebook environments)
- proper logging:
  - [ ] support `dict` for `opts.verbose`
  - [ ] colorized / rich log rendering (incl. HTML in notebook environments)

#### Import Sources
- [ ] support github / gitlab imports
- [ ] Support `nbformat`/Jupyter versions >4

#### Project Management
- [ ] Minimize(+freeze!) [dependencies](./setup.py)
- Self-hosting:
  - [ ] put code in notebooks
  - [ ] mirror repository in a Gist
  - [ ] implement subsequent versions of `ur` using earlier versions of `ur` (importing from remote, package-less locations)
- [x] run `*-test.ipynb` notebooks as tests
- [x] set up CI
- [x] generate `README.md` from `README.ipynb` with pre-commit hook
- [ ] convert/copy all of these TODOs GitHub into issues!
