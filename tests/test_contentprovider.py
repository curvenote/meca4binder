import os
from meca4binder import MecaContentProvider, extract_validate_and_identify_bundle


def test_init():
    provider = MecaContentProvider()
    assert provider.session is not None


def test_detect():
    provider = MecaContentProvider()
    spec = "https+meca://journals.curvenote.com/agu/submissions/12345/meca.zip"
    result = provider.detect(spec)
    print(result)
    assert (
        result["url"] == "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    )
    assert result["slug"] == "meca-ff804073622a71e513dd5bae6cfe3f41"
    assert provider.content_id == "meca-ff804073622a71e513dd5bae6cfe3f41"


def test_detect_with_query():
    provider = MecaContentProvider()
    spec = "https+meca://journals.curvenote.com/agu/submissions/12345/meca.zip?foo=bar&signature=ChAnGeAeAcHtImE123"
    result = provider.detect(spec)
    print(result)
    assert (
        result["url"]
        == "https://journals.curvenote.com/agu/submissions/12345/meca.zip?foo=bar&signature=ChAnGeAeAcHtImE123"
    )
    assert result["slug"] == "meca-ff804073622a71e513dd5bae6cfe3f41"
    assert provider.content_id == "meca-ff804073622a71e513dd5bae6cfe3f41"


def test_extract_and_validate_bundle():
    tmpdir = "./output/unzip"
    zip_filename = os.path.abspath("./tests/examples/myst-full/meca.zip")

    is_meca, bundle_dir = extract_validate_and_identify_bundle(zip_filename, tmpdir)
    assert is_meca
    assert bundle_dir == f"{tmpdir}/bundle/"


def test_copy_bundle():
    pass
