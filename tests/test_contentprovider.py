import os
from requests import Session
from meca4binder import MecaContentProvider, extract_validate_and_identify_bundle
from meca4binder.utils import get_hashed_slug


def test_init():
    provider = MecaContentProvider()
    assert provider.session is not None


URL = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
ETAG = '"ff804073622a71e513dd5bae6cfe3f41"'


def mock_head(mocker, headers):
    return mocker.patch.object(
        Session, "head", return_value=mocker.Mock(headers=headers)
    )


def test_detect(mocker):
    head = mock_head(mocker, {"ETag": ETAG, "Content-Length": "1234"})
    provider = MecaContentProvider()
    result = provider.detect(
        "https+meca://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )

    head.assert_called_once_with(URL)
    assert result["url"] == URL
    assert result["slug"] == get_hashed_slug(URL, ETAG)
    assert provider.content_id == get_hashed_slug(URL, ETAG)


def test_detect_falls_back_to_content_length(mocker):
    mock_head(mocker, {"Content-Length": "1234"})
    provider = MecaContentProvider()
    result = provider.detect(
        "https+meca://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )

    assert result["slug"] == get_hashed_slug(URL, "1234")


def test_detect_with_query(mocker):
    head = mock_head(mocker, {"ETag": ETAG})
    provider = MecaContentProvider()
    query = "?foo=bar&signature=ChAnGeAeAcHtImE123"
    result = provider.detect(
        f"https+meca://journals.curvenote.com/agu/submissions/12345/meca.zip{query}"
    )

    head.assert_called_once_with(f"{URL}{query}")
    assert result["url"] == f"{URL}{query}"
    # the slug ignores query parameters, so a re-signed URL maps to the same build
    assert result["slug"] == get_hashed_slug(URL, ETAG)
    assert provider.content_id == get_hashed_slug(URL, ETAG)


def test_detect_other_scheme(mocker):
    head = mock_head(mocker, {"ETag": ETAG})
    provider = MecaContentProvider()

    assert provider.detect(URL) is None
    head.assert_not_called()


def test_extract_and_validate_bundle():
    tmpdir = "./output/unzip"
    zip_filename = os.path.abspath("./tests/examples/myst-full/meca.zip")

    is_meca, bundle_dir = extract_validate_and_identify_bundle(zip_filename, tmpdir)
    assert is_meca
    assert bundle_dir == f"{tmpdir}/bundle/"


def test_copy_bundle():
    pass
