import importlib
import sys
import types

import pytest
from traitlets.config import LoggingConfigurable

import meca4binder.baseprovider
import meca4binder.repoprovider


def reload_providers():
    importlib.reload(meca4binder.baseprovider)
    return importlib.reload(meca4binder.repoprovider).MecaRepoProvider


@pytest.fixture
def fake_binderhub(monkeypatch):
    """A stand-in binderhub.repoproviders, as on a BinderHub image."""

    class RepoProvider(LoggingConfigurable):
        pass

    binderhub = types.ModuleType("binderhub")
    repoproviders = types.ModuleType("binderhub.repoproviders")
    repoproviders.RepoProvider = RepoProvider
    binderhub.repoproviders = repoproviders
    monkeypatch.setitem(sys.modules, "binderhub", binderhub)
    monkeypatch.setitem(sys.modules, "binderhub.repoproviders", repoproviders)
    yield RepoProvider
    monkeypatch.undo()
    reload_providers()


def test_subclasses_binderhubs_repo_provider(fake_binderhub):
    # BinderHub rejects repo providers that don't subclass its RepoProvider.
    MecaRepoProvider = reload_providers()

    assert issubclass(MecaRepoProvider, fake_binderhub)


def test_falls_back_without_binderhub(monkeypatch):
    # repo2docker images and plain installs don't have binderhub.
    monkeypatch.setitem(sys.modules, "binderhub", None)
    monkeypatch.setitem(sys.modules, "binderhub.repoproviders", None)
    MecaRepoProvider = reload_providers()
    monkeypatch.undo()

    assert MecaRepoProvider.__mro__[1].__module__ == "meca4binder.baseprovider"
    reload_providers()


def test_binderhub_accepts_it():
    pytest.importorskip("binderhub.app")
    from binderhub.app import BinderHub
    from binderhub.repoproviders import GitHubRepoProvider

    MecaRepoProvider = reload_providers()
    app = BinderHub()
    app.repo_providers = {"gh": GitHubRepoProvider, "meca": MecaRepoProvider}

    assert set(app.repo_providers) == {"gh", "meca"}
