from hashlib import md5


def get_hashed_slug(url, changes_with_content):
    """Return a unique slug"""
    return "meca-" + md5(f"{url}-{changes_with_content}".encode()).hexdigest()
