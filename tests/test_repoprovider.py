import pytest
from tornado.httpclient import AsyncHTTPClient, HTTPClientError
from tornado.httputil import HTTPHeaders
from meca4binder import MecaRepoProvider
from meca4binder.utils import get_hashed_slug


def test_init_with_spec():
    spec = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"

    provider = MecaRepoProvider(spec=spec)

    assert provider.spec == spec
    assert provider.url == spec
    assert provider.name == "MECA Bundle"
    assert provider.display_name == "MECA Bundle"
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


def mock_fetch(mocker, **kwargs):
    return mocker.patch.object(
        AsyncHTTPClient, "fetch", new_callable=mocker.AsyncMock, **kwargs
    )


@pytest.mark.asyncio
async def test_get_resolved_ref_unreachable(mocker):
    mock_fetch(mocker, side_effect=HTTPClientError(404))
    provider = MecaRepoProvider(
        spec="https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )

    with pytest.raises(ValueError, match=r"URL is unreachable \(HTTP 404: Not Found\)"):
        await provider.get_resolved_ref()


@pytest.mark.asyncio
async def test_get_resolved_ref(mocker):
    url = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    etag = '"ff804073622a71e513dd5bae6cfe3f41"'
    fetch = mock_fetch(
        mocker, return_value=mocker.Mock(headers=HTTPHeaders({"ETag": etag}))
    )
    provider = MecaRepoProvider(spec=url)

    ref = await provider.get_resolved_ref()

    fetch.assert_awaited_once()
    req = fetch.await_args.args[0]
    assert req.method == "HEAD"
    assert req.url == url
    assert ref == get_hashed_slug(url, etag)
    assert provider.get_build_slug() == get_hashed_slug(url, etag)


@pytest.mark.asyncio
async def test_get_resolved_ref_falls_back_to_content_length(mocker):
    url = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    mock_fetch(
        mocker,
        return_value=mocker.Mock(headers=HTTPHeaders({"Content-Length": "1234"})),
    )
    provider = MecaRepoProvider(spec=url)

    assert await provider.get_resolved_ref() == get_hashed_slug(url, "1234")


@pytest.mark.asyncio
async def test_get_resolved_ref_ignores_query(mocker):
    url = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    etag = '"ff804073622a71e513dd5bae6cfe3f41"'
    mock_fetch(mocker, return_value=mocker.Mock(headers=HTTPHeaders({"ETag": etag})))
    provider = MecaRepoProvider(spec=f"{url}?foo=bar&signature=ChAnGeAeAcHtImE123")

    assert await provider.get_resolved_ref() == get_hashed_slug(url, etag)


ALLOWED = ["journals.curvenote.com", "journal.agu.com"]


@pytest.mark.parametrize(
    "spec",
    [
        # BinderHub passes the spec as it appears in the request path, so a
        # bundle URL can arrive percent-encoded.
        "https%3A%2F%2Fjournals.curvenote.com%2Fagu%2Fsubmissions%2F12345%2Fmeca.zip",
        "https%3A//journals.curvenote.com/agu/submissions/12345/meca.zip",
        "https://JOURNALS.curvenote.com/agu/submissions/12345/meca.zip",
    ],
)
def test_encoded_or_mixed_case_spec_from_allowed_origin(spec):
    provider = MecaRepoProvider(spec=spec, allowed_origins=ALLOWED)
    assert provider.url.lower() == (
        "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )


@pytest.mark.parametrize(
    "spec",
    [
        "https%3A%2F%2Fother.google.com%2Fagu%2Fsubmissions%2F12345%2Fmeca.zip",
        "https://evil-journals.curvenote.com/agu/submissions/12345/meca.zip",
        "https://journals.curvenote.com.evil.com/agu/submissions/12345/meca.zip",
        "https://journals.curvenote.com@evil.com/agu/submissions/12345/meca.zip",
        "https%3A%2F%2Fjournals.curvenote.com%40evil.com%2Fmeca.zip",
    ],
)
def test_other_origin_throws(spec):
    with pytest.raises(ValueError, match="URL is not on an allowed origin"):
        MecaRepoProvider(spec=spec, allowed_origins=ALLOWED)


@pytest.mark.parametrize(
    "spec",
    [
        "ftp://journals.curvenote.com/agu/submissions/12345/meca.zip",
        "file%3A%2F%2F%2Fetc%2Fpasswd",
    ],
)
def test_non_http_url_throws(spec):
    with pytest.raises(ValueError, match="Invalid URL"):
        MecaRepoProvider(spec=spec, allowed_origins=ALLOWED)
