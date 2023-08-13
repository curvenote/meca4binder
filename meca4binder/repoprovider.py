import re
from urllib.parse import urlparse
from .baseprovider import RepoProvider
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from traitlets import List, Unicode, Bool, default


class MecaRepoProvider(RepoProvider):
    """BinderHub Provider that can handle the contents of a MECA bundle

    Users must provide a spec consisting of a public the URL to the bundle
    The URL origin must conform to the origin trait when that is set
    """

    name = Unicode("MECA Bundle")

    display_name = Unicode("MECA Bundle (URL)")

    labels = {
        "text": "MECA Bundle URL (https://journals.curvenote.com/agu/submissions/12345/meca.zip)",
        "tag_text": "<no tag required>",
        "ref_prop_disabled": True,
        "label_prop_disabled": True,
    }

    validate_bundle = Bool(config=True, default=True, help="Validate the file as MECA Bundle")

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
        url_pattern = re.compile(
            r'^(?:http|https)://'  # Start with http or https
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if url_pattern.match(self.spec) is None:
            raise ValueError("Invalid URL")
        
        if len(self.allowed_origins) > 0 and urlparse(self.spec).netloc not in self.allowed_origins:
            raise ValueError("URL is not on an allowed origin")

        self.url = self.spec        

    async def get_resolved_ref(self):

        # Check the URL is reachable
        client = AsyncHTTPClient()
        req = HTTPRequest(self.url, method="HEAD", user_agent="BinderHub")
        r = await client.fetch(req)
        if r.code != 200:
            raise ValueError("URL is not reachable")

        _, self.record_id = re.split("http[s]::\/\/", self.url)
        return self.record_id

    async def get_resolved_spec(self):
        if not hasattr(self, "record_id"):
            self.record_id = await self.get_resolved_ref()
        return self.record_id

    def get_repo_url(self):
        return self.url
    
    async def get_resolved_ref_url(self):
        return self.url

    def get_build_slug(self):
        return f"meca-{self.record_id}"

