# meca4binder

Providers enabling a BinderHub installation to work from URLs to MECA Bundles.

This in a minimal python package that can be installed and imported into a custom BinderHub installation.

The package contains:

- A Binderhub `RepoProvider` implementation for MECA Bundles, `MecaProvider`, whcih should be added to the list of providers in the Binderhub installation.
- A `repo2docker` `ContentProvider` for MECA bindles, `MecaContentProvider`, which should be added to the list of content providers in a custom `repo2docker` installation.
