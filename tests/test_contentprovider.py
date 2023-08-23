import pytest
import os
from meca4binder import MecaContentProvider, extract_validate_and_identify_bundle


def test_init():
    provider = MecaContentProvider()
    assert provider.session is not None


def test_detect():
    provider = MecaContentProvider()
    spec = "https://journals.curvenote.com/agu/submissions/12345/meca.zip"
    result = provider.detect(spec)
    assert result["url"] == spec
    assert result["record"] == "journals.curvenote.com/agu/submissions/12345/meca.zip"
    assert provider.record_id == "journals.curvenote.com/agu/submissions/12345/meca.zip"
    assert (
        provider.content_id == "journals.curvenote.com/agu/submissions/12345/meca.zip"
    )


def test_extract_and_validate_bundle():
    tmpdir = "./output/unzip"
    zip_filename = os.path.abspath("./tests/examples/myst-full/meca.zip")

    is_meca, bundle_dir = extract_validate_and_identify_bundle(zip_filename, tmpdir)
    assert is_meca
    assert bundle_dir == f"{tmpdir}/bundle/"


def test_copy_bundle():
    pass
