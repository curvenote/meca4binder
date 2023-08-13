import re
import logging
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, List

SHA1_PATTERN = re.compile(r"[0-9a-f]{40}")


"""
    Copied in from binderhub to avoid circular dependency
    Not needed once we integrate back fully with binderhub
"""
class RepoProvider(LoggingConfigurable):
    """Base class for a repo provider"""

    name = Unicode(
        help="""
        Descriptive human readable name of this repo provider.
        """
    )

    spec = Unicode(
        help="""
        The spec for this builder to parse
        """
    )

    banned_specs = List(
        help="""
        List of specs to blacklist building.

        Should be a list of regexes (not regex objects) that match specs which should be blacklisted
        """,
        config=True,
    )

    high_quota_specs = List(
        help="""
        List of specs to assign a higher quota limit.

        Should be a list of regexes (not regex objects) that match specs which should have a higher quota
        """,
        config=True,
    )

    spec_config = List(
        help="""
        List of dictionaries that define per-repository configuration.

        Each item in the list is a dictionary with two keys:

            pattern : string
                defines a regex pattern (not a regex object) that matches specs.
            config : dict
                a dictionary of "config_name: config_value" pairs that will be
                applied to any repository that matches `pattern`
        """,
        config=True,
    )

    unresolved_ref = Unicode()

    git_credentials = Unicode(
        "",
        help="""
        Credentials (if any) to pass to git when cloning.
        """,
        config=True,
    )

    def is_banned(self):
        """
        Return true if the given spec has been banned
        """
        for banned in self.banned_specs:
            # Ignore case, because most git providers do not
            # count DS-100/textbook as different from ds-100/textbook
            if re.match(banned, self.spec, re.IGNORECASE):
                return True
        return False

    def has_higher_quota(self):
        """
        Return true if the given spec has a higher quota
        """
        for higher_quota in self.high_quota_specs:
            # Ignore case, because most git providers do not
            # count DS-100/textbook as different from ds-100/textbook
            if re.match(higher_quota, self.spec, re.IGNORECASE):
                return True
        return False

    def repo_config(self, settings):
        """
        Return configuration for this repository.
        """
        repo_config = {}

        # Defaults and simple overrides
        if self.has_higher_quota():
            repo_config["quota"] = settings.get("per_repo_quota_higher")
        else:
            repo_config["quota"] = settings.get("per_repo_quota")

        # Spec regex-based configuration
        for item in self.spec_config:
            pattern = item.get("pattern", None)
            config = item.get("config", None)
            if not isinstance(pattern, str):
                raise ValueError(
                    "Spec-pattern configuration expected "
                    "a regex pattern string, not "
                    f"type {type(pattern)}"
                )
            if not isinstance(config, dict):
                raise ValueError(
                    "Spec-pattern configuration expected "
                    "a specification configuration dict, not "
                    f"type {type(config)}"
                )
            # Ignore case, because most git providers do not
            # count DS-100/textbook as different from ds-100/textbook
            if re.match(pattern, self.spec, re.IGNORECASE):
                repo_config.update(config)
        return repo_config

    async def get_resolved_ref(self):
        raise NotImplementedError("Must be overridden in child class")

    async def get_resolved_spec(self):
        """Return the spec with resolved ref."""
        raise NotImplementedError("Must be overridden in child class")

    def get_repo_url(self):
        """Return the git clone-able repo URL"""
        raise NotImplementedError("Must be overridden in the child class")

    async def get_resolved_ref_url(self):
        """Return the URL of repository at this commit in history"""
        raise NotImplementedError("Must be overridden in child class")

    def get_build_slug(self):
        """Return a unique build slug"""
        raise NotImplementedError("Must be overriden in the child class")

    @staticmethod
    def is_valid_sha1(sha1):
        return bool(SHA1_PATTERN.match(sha1))
    


"""
Base classes for repo2docker ContentProviders

ContentProviders accept a `spec` of various kinds, and
provide the contents from the spec to a given output directory.
"""

class ContentProviderException(Exception):
    """Exception raised when a ContentProvider can not provide content."""

    pass


class ContentProvider:
    def __init__(self):
        self.log = logging.getLogger("repo2docker")

    @property
    def content_id(self):
        """A unique ID to represent the version of the content.
        This ID is used to name the built images. If the ID is the same between
        two runs of repo2docker we will reuse an existing image (if it exists).
        By providing an ID that summarizes the content we can reuse existing
        images and speed up build times. A good ID is the revision of a Git
        repository or a hash computed from all the content.
        The type content ID can be any string.
        To disable this behaviour set this property to `None` in which case
        a fresh image will always be built.
        """
        return None

    def detect(self, repo, ref=None, extra_args=None):
        """Determine compatibility between source and this provider.

        If the provider knows how to fetch this source it will return a
        `spec` that can be passed to `fetch`. The arguments are the `repo`
        string passed on the command-line, the value of the --ref parameter,
        if provided and any provider specific arguments provided on the
        command-line.

        If the provider does not know how to fetch this source it will return
        `None`.
        """
        raise NotImplementedError()

    def fetch(self, spec, output_dir, yield_output=False):
        """Provide the contents of given spec to output_dir

        This generator yields logging information if `yield_output=True`,
        otherwise log output is printed to stdout.

        Arguments:
            spec -- Dict specification understood by this ContentProvider
            output_dir {string} -- Path to output directory (must already exist)
            yield_output {bool} -- If True, return output line by line. If not,
                                   output just goes to stdout.
        """
        raise NotImplementedError()


