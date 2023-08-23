import re
from .baseprovider import ContentProvider
from requests import HTTPError, Session
import os
from os import path
import tempfile
import shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile, is_zipfile


def fetch_zipfile(session, url, dst_dir):
    resp = session.get(url, headers={"accept": "application/zip"}, stream=True)
    resp.raise_for_status()

    dst_filename = path.join(dst_dir, "meca.zip")
    with open(dst_filename, "wb") as dst:
        for chunk in resp.iter_content(chunk_size=128):
            dst.write(chunk)

    return dst_filename


def handle_items(_, item):
    print(item)


def extract_validate_and_identify_bundle(zip_filename, dst_dir):
    if not os.path.exists(zip_filename):
        raise RuntimeError("Download MECA bundle not found")

    if not is_zipfile(zip_filename):
        raise RuntimeError("MECA bundle is not a zip file")

    with ZipFile(zip_filename, "r") as zip_ref:
        zip_ref.extractall(dst_dir)

    try:
        manifest = path.join(dst_dir, "manifest.xml")
        if not os.path.exists(manifest):
            raise RuntimeError("MECA bundle is missing manifest.xml")
        article_source_dir = "bundle/"

        tree = ET.parse(manifest)
        root = tree.getroot()

        bundle_instance = root.findall(
            "{*}item[@item-type='article-source-directory']/{*}instance"
        )
        for attr in bundle_instance[0].attrib:
            if attr.endswith("href"):
                article_source_dir = bundle_instance[0].get(attr)

        return True, path.join(dst_dir, article_source_dir)
    except:
        return False, dst_dir


class MecaContentProvider(ContentProvider):
    """A repo2docker content provider for MECA bundles"""

    def __init__(self):
        super().__init__()
        self.session = Session()
        self.session.headers.update(
            {
                "user-agent": f"repo2docker MECA",
            }
        )

    def detect(self, url, ref=None, extra_args=None):
        """Assume url is used and trusted as a reachable MECA bundle from an allowed origin

        This is due to the binderhub RepoProvider class already checking for this. If not then
        we'd need to repeat specific checks like allowed_origin and reachable url in here.
        """
        _, self.record_id = re.split("http[s]://", url)
        return {"url": url, "record": self.record_id}

    def fetch(self, spec, output_dir):
        record_id = spec["record"]
        url = spec["url"]

        yield f"Creating temporary directory.\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            yield f"Temporary directory created at {tmpdir}.\n"

            yield f"Fetching MECA Bundle {record_id}.\n"
            zip_filename = fetch_zipfile(self.session, url, tmpdir)

            yield f"Extracting MECA Bundle {record_id}.\n"
            is_meca, bundle_dir = extract_validate_and_identify_bundle(
                zip_filename, tmpdir
            )

            yield f"Copying MECA Bundle {record_id} to {output_dir}.\n"
            files = os.listdir(bundle_dir)
            for f in files:
                shutil.move(os.path.join(bundle_dir, f), output_dir)

            yield f"Removing temporary directory.\n"

        yield f"MECA Bundle {record_id} fetched and unpacked.\n"

    @property
    def content_id(self):
        return self.record_id
