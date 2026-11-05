import re
from urllib.parse import quote

import pytest

from meca4binder import MecaRepoProvider


def regexparam_parse(route):
    """Python port of regexparam's parse() (v3), which BinderHub's React UI
    (via wouter) uses to turn /v2/<provider>/(?<buildSpec>validateRegex) into
    a regex. It splits on "/", stops at the first empty segment, and treats
    segments starting with ":" or "*" as parameters."""
    pattern = ""
    parts = route.split("/")
    if not parts[0]:
        parts.pop(0)
    for part in parts:
        if not part:
            break
        if part[0] in ":*":
            raise AssertionError(f"segment {part!r} would become a route parameter")
        pattern += "/" + part
    return re.compile("^" + pattern + "/?$", re.IGNORECASE)


def route():
    validate = MecaRepoProvider.display_config["spec"]["validateRegex"]
    # JS named groups are (?<name>...); Python's are (?P<name>...)
    return regexparam_parse(f"/v2/meca/(?<buildSpec>{validate})".replace("(?<", "(?P<"))


BUNDLE = "https://scms.curvenote.com/x/meca.zip?signature=AbC123&expires=99"


@pytest.mark.parametrize(
    "path",
    [
        "/v2/meca/" + quote(BUNDLE, safe="") + "/",  # what the form and links make
        "/v2/meca/https://scms.curvenote.com/x/meca.zip",  # a plain URL
        "/v2/meca/http%3a%2f%2fexample.com%2fmeca.zip",
    ],
)
def test_ui_route_matches(path):
    m = route().match(path)
    assert m, path
    assert re.match(MecaRepoProvider.display_config["spec"]["validateRegex"], m.group("buildSpec"))


def test_ui_route_survives_regexparam():
    # The whole validateRegex must make it into the route: no "//" or empty
    # segments to cut it short.
    validate = MecaRepoProvider.display_config["spec"]["validateRegex"]
    assert validate in route().pattern


@pytest.mark.parametrize("path", ["/v2/meca/", "/v2/meca/ftp%3A%2F%2Fexample.com%2Fmeca.zip", "/v2/meca/not-a-url"])
def test_ui_route_rejects(path):
    assert not route().match(path)


def test_links_are_url_encoded():
    # Keeps a signed URL's query string part of the spec.
    assert MecaRepoProvider.display_config["repo"]["urlEncode"] is True
