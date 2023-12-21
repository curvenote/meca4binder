# meca4binder

Providers enabling a BinderHub installation to work from URLs to MECA Bundles.

This in a minimal python package that can be installed and imported into a custom BinderHub installation.

The package contains:

- A Binderhub `RepoProvider` implementation for MECA Bundles, `MecaProvider`, which should be added to the list of providers in the Binderhub installation.
- A `repo2docker` `ContentProvider` for MECA bindles, `MecaContentProvider`, which should be added to the list of content providers in a custom `repo2docker` installation.

## Development

```
python -m venv env
source env/bin/activate
python -m pip install -e .[all]
```

Run tests

```
pytest
```

with watch

```
ptw
```

## Binderhub Installation

Currently this requires manual modification of binderhub:

- app.py - import `MecaRepoProvider` and add this to `repo_providers`
- main.py - add to the `SPEC_NAMES` list
- launch.json - add to the `provider` enum
- index.js - add `providerPrefix === 'meca'` to the test alongside Zenodo etc..., that sets `ref` to an empty string
- index.html - add information on meca as you like

## repo2docker Installation

Currently this needs manual modifications to `repo2docker/repo2docker/app.py` in order import the `MecaContentProvider` class an add it to the `content_providers` list.

## Contributors

This package was developed as part of the [AGU (American Geophysical Union) NotebooksNow! initiative](https://data.agu.org/notebooks-now/). The aim of the project is to elevate Computational Notebooks as part of the scientific record and the [MECA (Manuscript Exchange Common Approach) bundle format](https://meca.zip), along with JATS xml has been used to ensure notebooks can be represented as scholarly objects independent of the toolchain that produced them. Read more about the JATS+MECA specification work that was undertaken [here](https://agu-nnn.curve.space/improvements).

This package was developed by [Curvenote](https://curvenote.com) as part of the NotebookNow! pilot project in 2023,. This work was supported by a grant from the Alfred P. Sloan Foundation, and in kind support from Curvenote and AGU.
