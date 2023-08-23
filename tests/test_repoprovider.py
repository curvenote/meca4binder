import pytest
from meca4binder import MecaRepoProvider


def test_init_with_spec():
    spec = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"

    provider = MecaRepoProvider(spec=spec)

    assert provider.spec == spec
    assert provider.url == spec
    assert provider.name == "MECA Bundle"
    assert provider.display_name == "MECA Bundle (URL)"
    assert provider.allowed_origins == []


def test_init_with_origins():
    spec = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"

    provider = MecaRepoProvider(spec=spec, allowed_origins=["journals.curvenote.com"])

    assert provider.allowed_origins == ["journals.curvenote.com"]


@pytest.mark.parametrize(
    "invalid_spec",
    [
        "www.google.com",
        "journals.curvenote.com/agu/submissions/12345/meca.zip",
        "C:\\meca.zip",
        "file:///C:/meca.zip",
    ],
)
def test_invalid_url(invalid_spec):
    with pytest.raises(ValueError, match="Invalid URL"):
        MecaRepoProvider(spec=invalid_spec)


@pytest.mark.parametrize(
    "spec",
    [
        "https://journals.curvenote.com/agu/submissions/12345/meca.zip",
        "https://journal.agu.com/agu/submissions/12345/meca.zip",
    ],
)
def test_from_allowed_origin(spec):
    provider = MecaRepoProvider(
        spec=spec, allowed_origins=["journals.curvenote.com", "journal.agu.com"]
    )
    assert provider.allowed_origins == ["journals.curvenote.com", "journal.agu.com"]


def test_from_other_origin_throws():
    spec = "https://other.google.com/agu/submissions/12345/meca.zip"
    with pytest.raises(ValueError, match="URL is not on an allowed origin"):
        provider = MecaRepoProvider(
            spec=spec, allowed_origins=["journals.curvenote.com", "journal.agu.com"]
        )
        assert provider.allowed_origins == ["journals.curvenote.com", "journal.agu.com"]


@pytest.mark.asyncio
async def test_get_resolved_ref_url():
    provider = MecaRepoProvider(
        spec="https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )

    assert (
        provider.url == "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )


@pytest.mark.asyncio
async def test_get_resolved_ref_unreachable():
    provider = MecaRepoProvider(
        spec="https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )

    with pytest.raises(ValueError, match="URL is unreachable"):
        await provider.get_resolved_ref()


@pytest.mark.asyncio
async def test_get_resolved_ref():
    # Note: just need a reachable url for this to succeed, does not have to point to a file
    provider = MecaRepoProvider(
        spec="https://github.com/Notebooks-Now/submission-myst-full"
    )

    ref = await provider.get_resolved_ref()
    assert ref == "github.com/Notebooks-Now/submission-myst-full"
    assert provider.record_id == "github.com/Notebooks-Now/submission-myst-full"
    assert (
        provider.get_build_slug()
        == "meca--github.com/Notebooks-Now/submission-myst-full"
    )
