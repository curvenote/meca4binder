from hashlib import md5
from urllib.parse import urlparse, urlunparse


def get_hashed_slug(url, changes_with_content):
    """Return a unique slug tht is invariant to query parameters in the url"""
    parsed_url = urlparse(url)
    stripped_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
    )

    return "meca-" + md5(f"{stripped_url}-{changes_with_content}".encode()).hexdigest()
