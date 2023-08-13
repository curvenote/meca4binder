import re
from .baseprovider import ContentProvider
from requests import HTTPError, Session
import os
from os import path
from zipfile import ZipFile, is_zipfile

class MecaContentProvider(ContentProvider):
    """A repo2docker content provider for MECA bundles
    """

    def __init__(self):
        super().__init__()
        self.session = Session()
        self.session.headers.update(
            {
                "user-agent": f"repo2docker MECA",
            }
        )


    def detect(self, url, ref=None, extra_args=None):
        """url is used and trusted as a reachable MECA bundle from an allowed origin
        
        This is due to the binderhub RepoProvider class already checking for this.
        """
        _, self.record_id = re.split("http[s]::\/\/", self.url)
        return {"url": url, "record": self.record_id }

    def fetch(self, spec, output_dir):
        record_id = spec["record"]
        url = spec["url"]

        yield f"Fetching MECA Bundle {record_id}.\n"

        resp = self.session.get(url, headers={"accept": "application/zip"}, stream=True)
        resp.raise_for_status()

        dst_filename = path.join(output_dir, "meca.zip")
        with open(dst_filename, "wb") as dst:
            yield f"Fetching {dst_filename}\n"
            for chunk in resp.iter_content(chunk_size=128):
                dst.write(chunk)


        if not is_zipfile(dst_filename):
            raise RuntimeError("MECA bundle is not a zip file")

        yield f"Extracting bundle/ from {dst_filename}\n"
        found_bundle = False
        with ZipFile(dst_filename) as zfile:
            for member in zfile.namelist():
                fname = os.path.basename(member)
                if fname == "bundle":
                    yield f"Found bundle folder, extracting...\n"
                    found_bundle = True
                    zfile.extract(member, output_dir)

        if not found_bundle:
            yield f"No bundle folder found in {dst_filename}, extracting all to root folder...\n"
            with ZipFile(dst_filename) as zfile:
                zfile.extractall(output_dir)

        yield f"Removing {dst_filename}\n"
        os.remove(dst_filename)

        yield f"MECA Bundle {record_id} fetched and unpacked.\n"

    @property
    def content_id(self):
        self.record_id