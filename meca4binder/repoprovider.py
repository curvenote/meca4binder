import re
import validators as val
from urllib.parse import urlparse, unquote, urlencode, quote
from .baseprovider import RepoProvider
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from traitlets import List, Unicode, Bool, default
from .utils import get_hashed_slug
from urllib.parse import urlparse, urlunparse


class MecaRepoProvider(RepoProvider):
    """BinderHub Provider that can handle the contents of a MECA bundle

    Users must provide a spec consisting of a public the URL to the bundle
    The URL origin must conform to the origin trait when that is set
    """

    name = Unicode("MECA Bundle")

    display_name = "MECA Bundle"

    display_config = {
        "displayName": "MECA Bundle Url",
        "id": "meca",
        "spec": {"validateRegex": r"^(https?)://[^\s/$.?#].[^\s]*$"},
        "repo": {
            "label": "MECA Bundle Url",
            "placeholder": "example: https://pub.curvenote.com/<id>/meca.zip",
            "urlEncode": False,
        },
        "ref": {"enabled": False},
    }

    labels = {
        "text": "MECA Bundle URL (https://journals.curvenote.com/journal/submissions/12345/meca.zip)",
        "tag_text": "<no tag required>",
        "ref_prop_disabled": True,
        "label_prop_disabled": True,
    }

    validate_bundle = Bool(config=True, help="Validate the file as MECA Bundle").tag(
        default=True
    )

    allowed_origins = List(
        config=True,
        help="""List of allowed origins for the URL

        If set, the URL must be on one of these origins.

        If not set, the URL can be on any origin.
        """,
    )

    @default("allowed_origins")
    def _allowed_origins_default(self):
        return []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        url = unquote(self.spec)

        if not val.url(url):
            raise ValueError(f"[MecaRepoProvider] Invalid URL {url}")

        if (
            len(self.allowed_origins) > 0
            and urlparse(self.spec).hostname not in self.allowed_origins
        ):
            raise ValueError("URL is not on an allowed origin")

        self.url = url

        self.log.info(f"MECA Bundle URL: {self.url}")
        self.log.info(f"MECA Bundle raw spec: {self.spec}")

    async def get_resolved_ref(self):
        # Check the URL is reachable
        client = AsyncHTTPClient()
        req = HTTPRequest(self.url, method="HEAD", user_agent="BinderHub")
        self.log.info(f"get_resolved_ref() HEAD: {self.url}")
        try:
            r = await client.fetch(req)
            self.log.info(f"URL is reachable: {self.url}")
            self.hashed_slug = get_hashed_slug(
                self.url, r.headers.get("ETag") or r.headers.get("Content-Length")
            )
        except Exception as e:
            raise ValueError(f"URL is unreachable ({e})")

        self.log.info(f"hashed_slug: {self.hashed_slug}")
        return self.hashed_slug

    async def get_resolved_spec(self):
        if not hasattr(self, "hashed_slug"):
            await self.get_resolved_ref()
        self.log.info(f"get_resolved_spec(): {self.hashed_slug}")
        return self.spec

    async def get_resolved_ref_url(self):
        self.log.info(f"get_resolved_ref_url(): {self.url}")
        return self.url

    def get_repo_url(self):
        """This is passed to repo2docker and is the URL that is to be fetched
        with a `http[s]+meca` protocol string. We do this by convention to enable
        detection of meca urls by the MecaContentProvider.
        """
        parsed = urlparse(self.url)
        parsed = parsed._replace(scheme=f"{parsed.scheme}+meca")
        url = urlunparse(parsed)
        self.log.info(f"get_repo_url(): {url}")
        url = quote(url)
        self.log.info(f"get_repo_url(): encoded {url}")
        return url

    def get_build_slug(self):
        """Should return a unique build slug"""
        return self.hashed_slug
