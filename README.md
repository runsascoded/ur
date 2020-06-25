# ur

Import remote Python files and Jupyter notebooks, from GitHub Gists, the local filesystem, or arbitrary URLs:

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
    <td align="right">✅</td>
    <td align="right">✅</td>
  </tr>
  <tr>
    <td align="right">
      <b>Python (.py)</b>
    </td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">✅</td>
    <td align="right">✅</td>
  </tr>
</table>

--------

- [**Install**](#install)
- [**Usage**](#usage)
  - [Import GitHub Gists](#gists)
  - [Import from GitHub Repos](#github)
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
In a shell:
```bash
pip install ur
```
In a Jupyter notebook:
```python
from sys import executable as python
!{python} -m pip install ur 
```

## Usage <a id="usage"></a>

### Import GitHub Gists <a id="gists"></a>

Import several notebooks and Python files from [a Gist](https://gist.github.com/1288bff2f9e05394a94312010da267bb):


```python
from gist._1288bff2f9e05394a94312010da267bb import *
a_b.a(), a_b.b(), c.c()
```

    Cloning https://gist.github.com/1288bff2f9e05394a94312010da267bb.git into .objs/Gist/1288bff2f9e05394a94312010da267bb/clone





    ('aaa', 'bbb', 'ccc')



(note the leading underscore in the `import` statement, which is necessary when the Gist ID begins with a number)

### Import from GitHub, GitLab Repos <a id="github"></a>
Import some helper functions (in this case, various wrappers around [`subprocess`](https://docs.python.org/3/library/subprocess.html) functions) directly from [a notebook on GitHub](https://github.com/ryan-williams/jupyter-rc/blob/master/process.ipynb):


```python
from github.ryan_williams.jupyter_rc.process import *
lines('echo','yay')  # wrapper around subprocess.check_output that asserts and returns a single line written to stdout
```

    Cloning https://github.com/ryan-williams/jupyter-rc.git into .objs/Github/ryan-williams/jupyter-rc/clone
    Running: ['echo', 'yay']





    ['yay']



Importing from GitLab also works; here we import a `cd` ("change directory") [contextmanager](https://docs.python.org/3/library/contextlib.html):


```python
from gitlab.runsascoded.dotfiles.jupyter.cd import cd
from pathlib import Path
with cd('examples'): print(Path.cwd())
```

    Cloning https://gitlab.com/runsascoded/dotfiles/jupyter.git into .objs/Gitlab/runsascoded/dotfiles/jupyter/clone
    /github/workspace/examples


([gitlab.com notebook](https://gitlab.com/runsascoded/dotfiles/jupyter/-/blob/master/cd.ipynb))

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
- [ ] Context manager for controlling ancestor imports
- [ ] Skip importing notebooks with [Papermill `parameters` tags](https://papermill.readthedocs.io/en/latest/usage-parameterize.html#designate-parameters-for-a-cell)
- [ ] work with `importlib.reload`
- [x] support `__init__.ipynb` (automatically load notebook when loading Gist), `__all__` (configure `import *` behavior)
- [ ] more nuanced TTL / `skip_cache` behavior (e.g. let cached URLs time-out appropriately based on HTTP headers, a la [`requests-cache`](https://pypi.org/project/requests-cache/))
- [ ] `setup.py` "extras" to allow for `pip`-installing only specific pieces (e.g. exclude gists/github/gitlab?)
- [ ] use bare Git clones
- [ ] vet `.urignore` logic (I don't think it tracks which patterns are ignored for which directories, atm; all patterns end up glommed together and applied everywhere 🙀)

#### Usability
- [ ] pretty-print info about what's imported (in notebook environments)
- proper logging:
  - [ ] support `dict` for `opts.verbose`
  - [ ] colorized / rich log rendering (incl. HTML in notebook environments)

Speed
- [ ] do some benchmarking (WIP: [benchmark.ipynb](benchmark.ipynb))
- [ ] read from `__pycache__`, when present, instead of compiling

#### Import Sources
- [x] support github / gitlab imports
- [ ] Support `nbformat`/Jupyter versions >4

Import from specific refs within Gists/repos:
  - [ ] commit SHAs (e.g. `gist._1288bff2f9e05394a94312010da267bb._8d7c134f5ef7bd340fd52840006d37bdd52515a5`)
  - [ ] short commit SHAs (e.g. `gist._1288bff2f9e05394a94312010da267bb._8d7c134`)
  - [ ] branch names (e.g. `gist._1288bff2f9e05394a94312010da267bb.master`)
  - [ ] tags (e.g. `gist._1288bff2f9e05394a94312010da267bb.v1.0`)

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
