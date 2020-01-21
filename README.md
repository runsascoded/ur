# ur
import remote Python and Jupyter notebook files, from GitHub Gists, the local filesystem, or arbitrary URLs.

## Install:


```python
from sys import executable as python
!{python} -m pip install -q ur
```

## Usage

### Import GitHub gists


```python
from gists._1288bff2f9e05394a94312010da267bb import *
a_b.a(), a_b.b(), c.c()
```




    ('aaa', 'bbb', 'ccc')



That imports 2 Jupyter notebooks from https://gist.github.com/1288bff2f9e05394a94312010da267bb (note the leading underscore in the `import` statement, which is necessary when the Gist ID begins with a number), and calls functions defined in them.

### Import arbitrary URLs
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



## Discussion
Jupyter notebooks provide a rich, literate programming experience that is preferable to conventional IDE-based Python environments in many ways.

However, conventional wisdom is that reusing code in notebooks requires porting it to `.py` files. This is tedious and often requires trashing some of what makes notebooks great in the first place (rich, inline documentation, easy reproducibility, etc.).

Jupyter itself provides [sample code for importing code from (local) Jupyter notebooks](https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Importing%20Notebooks.html) ([originally from 2014?](https://github.com/adrn/ipython/blob/master/examples/Notebook/Importing%20Notebooks.ipynb)), and [several](https://github.com/marella/nbimport) [packages](https://github.com/rileyedmunds/import-ipynb), [repositories](https://github.com/ipython/ipynb), [blog posts](https://vispud.blogspot.com/2019/02/ipynb-import-another-ipynb-file.html), [and](https://github.com/jupyter/notebook/issues/1588) [issues](https://github.com/jupyter/notebook/issues/3479) have built on and published similar code.

[nbimporter](https://github.com/grst/nbimporter) (which this repo is a fork of) is perhaps most notable, allowing seamless reuse of Jupyter-resident utilities within single projects, but [its author now recommends factoring code out to `.py` modules](https://github.com/grst/nbimporter/blob/0fc2bdf458005be742090f67c306a4e3bcc04e77/README.md#update-2019-06-i-do-not-recommend-any-more-to-use-nbimporter).

The Jupyter ecosystem increasingly shines for the ease with which it allows of publishing and sharing notebooks, and stands to gain a lot from easier remixing+reuse of the wealth of code and data being published in Jupyter notebooks every day. I believe there are straightforward answers to [the reproducibility and testability concerns raised in `nbimporter`](https://github.com/grst/nbimporter/blob/0fc2bdf458005be742090f67c306a4e3bcc04e77/README.md#why), and built the `ur` package to bear that out (and solve immediate productivity and code-reuse needs in my day-to-day life).

### Remote importing: package-less publishing
An animating idea of `ur` is that publishing+reusing a useful helper function should be no harder than
Reuse of code in Jupyter notebooks should be made as easy as possible. Users shouldn't have to mangle their utility-code and then publish it to Pip repositories in order to avoid copy/pasting standard helpers in every notebook/project they work in.

Importing code directly from remote Notebooks (or `.py` files) allows frictionless code reuse beyond what Python/Jupyter users are offered today.

### GitHub Gists: "anyone with the link can view" git repositories
`ur` particularly emphasizes using and importing from [GitHub Gists](https://help.github.com/en/enterprise/2.13/user/articles/about-gists). Like `git` itself, Gists combine a few simple but powerful concepts orthogonally, forming a great platform for sharing and tracking code:
- Gists are the only service I'm aware of that allows "publishing" a Git repository to an opaque URL that can be easily shared, but is otherwise (cryptographically, I think?) private, not search-indexed, etc.
  - [GitLab snippets](https://docs.gitlab.com/ee/user/snippets.html) are a comparable product, but [a request for this feature is open at time of writing](https://gitlab.com/gitlab-org/gitlab/issues/14201)
- Each Gist is backed by a full Git repository, under the hood
  - Gists can therefore track changes to many files over time
  - Users can choose to view Gists' "latest `HEAD`" content (the default on https://gist.github.com), or specify frozen Git-SHA permalinks for guaranteed reproducibility
    - both "modes" are supported via web browser, Git CLI, or [GitHub API](https://developer.github.com/v3/gists/#get-a-single-gist)
- Many CLIs and SDKs exist for interacting with Gists from different languages/environments
  - [I previously wrote a `gist-dir` helper](https://github.com/defunkt/gist/issues/191#issuecomment-569572229) that uploads an entire directory as a Gist (also working around issues with binary data that the Gist API normally doesn't handle correctly)

### Use-case: portable, shareable "dotfiles"
Something that `ur` makes easy is boilerplate-free reuse of common imports and aliases across notebooks/projects/users.

For example, "everyone" imports `numpy as np`, `pandas as pd`, `plotly as pl`, etc. I have a few that I like in addition: `from os import environ as env`, `from sys import python as executable`, etc.

`ur` offers several minimal-boilerplate ways to let you (and anyone you share your notebook with) use all the helpers you like, portably, without having to redeclare them or otherwise interfere with the environment you originally used them in:

```python
import ur
ur(github='ryan-williams/dotfiles', tree='v1.0', file='dotfiles.ipynb', all='*')
```

Many versions of this can be used, depending on your preferences, e.g.:

```python
from gists.abcdef0123456789abcdef0123456789 import *
```

### Future work
- pretty-print info about what's imported (in notebook environments)
- test/handle intra-gist imports
- test/handle pip dependencies in gist imports
- support github / gitlab imports
- API for tagging/skipping cells in notebooks (visualizations, tests, etc.)
- Support Jupyter versions >4
- Minimize(+freeze!) [dependencies](./setup.py)
- proper logging
- self-host (put code in notebooks in gists, implement subsequent versions of `ur` using earlier versions of `ur` to import from remote, package-less locations)
