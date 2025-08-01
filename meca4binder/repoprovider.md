# MecaRepoProvider Overview

## What is MecaRepoProvider?

The `MecaRepoProvider` is a BinderHub repository provider that enables BinderHub to handle MECA (Manuscript Exchange Common Approach) bundles. It allows users to launch interactive Jupyter environments directly from MECA-formatted scholarly publications.

## How it Works in BinderHub

### Integration Points

1. **BinderHub UI**: Users can paste MECA bundle URLs (e.g., `https://pub.curvenote.com/12345/meca.zip`)
2. **URL Validation**: The provider validates the URL format and accessibility
3. **Content Detection**: Converts the URL to a `https+meca://` protocol for repo2docker
4. **Image Building**: repo2docker builds a Docker image containing the MECA bundle content
5. **Environment Launch**: Users get an interactive Jupyter environment with the MECA content

### Key Functions

- **`get_resolved_ref()`**: Verifies URL accessibility and creates a unique content hash
- **`get_repo_url()`**: Converts URL to `https+meca://` protocol for repo2docker detection
- **`get_build_slug()`**: Provides unique identifier for Docker image naming
- **`get_resolved_spec()`**: Returns the final specification for the build process

## Image Naming and Tagging

### How Image Names and Tags are Created

The Docker image name and tag are generated deterministically from the MECA bundle URL using the following process:

#### Step 1: URL Metadata Extraction
```python
# Make HEAD request to get ETag or Content-Length
response = requests.head(meca_url)
metadata = response.headers.get("ETag") or response.headers.get("Content-Length")
```

#### Step 2: URL Normalization
```python
# Strip query parameters and fragments, keep only scheme://hostname/path
parsed_url = urlparse(url)
stripped_url = urlunparse(
    (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
)
```

#### Step 3: Hash Generation
```python
# Create MD5 hash of normalized URL + metadata
content_hash = md5(f"{stripped_url}-{metadata}".encode()).hexdigest()
```

#### Step 4: Image Name Construction
```python
# Final format: {prefix}{full_hash}-{truncated_hash}:meca-{content_hash}
image_name = f"meca-{content_hash}-{content_hash[:6]}:meca-{content_hash}"
```

### Example

**Input URL**: `https://pub.curvenote.com/12345/meca.zip`
**ETag**: `"abc123"`
**Normalized URL**: `https://pub.curvenote.com/12345/meca.zip`
**Content Hash**: `2df10e6d81881615d274bef324537fcd65`

**Result**:
- **Image Name**: `meca-2df10e6d81881615d274bef324537fcd65-de1b43`
- **Tag**: `meca-f10e6d81881615d274bef324537fcd65`

## Recreating Tags from URLs

### How to Compute the Tag

Given a MECA bundle URL, you can compute the expected Docker image tag:

```python
import requests
from hashlib import md5
from urllib.parse import urlparse, urlunparse

def compute_meca_tag(url):
    # Get metadata from HEAD request
    response = requests.head(url)
    metadata = response.headers.get("ETag") or response.headers.get("Content-Length")
    
    # Normalize URL
    parsed_url = urlparse(url)
    stripped_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
    )
    
    # Generate hash
    content_hash = md5(f"{stripped_url}-{metadata}".encode()).hexdigest()
    
    return f"meca-{content_hash}"

# Usage
url = "https://pub.curvenote.com/12345/meca.zip"
tag = compute_meca_tag(url)
print(f"Expected tag: {tag}")
```

### Caveats and Dependencies

#### 1. **Location Dependency**
The tag is **location-dependent** because it includes the URL in the hash calculation. If a MECA bundle is moved to a different URL:

- **Same content, different URL** = **Different tag**
- **Same content, same URL** = **Same tag**

This means:
- Moving a MECA bundle from `https://server1.com/bundle.zip` to `https://server2.com/bundle.zip` will create a different tag
- The same bundle at the same URL will always produce the same tag

#### 2. **Metadata Dependency**
The tag depends on HTTP headers (ETag or Content-Length):

- **ETag changes** (e.g., server configuration changes) = **Different tag**
- **Content-Length changes** (e.g., file modifications) = **Different tag**
- **No metadata available** = **Falls back to Content-Length or empty string**

#### 3. **Content Integrity**
The tag serves as a **content integrity check**:

- **Identical MECA bundles** at the same URL = **Identical tags**
- **Modified MECA bundles** = **Different tags**
- **Different MECA bundles** = **Different tags**

### Practical Implications

1. **Caching**: Identical tags enable Docker layer caching and image reuse
2. **Reproducibility**: Same URL + same content = same environment
3. **Versioning**: Content changes are automatically detected via tag changes
4. **Portability**: Tags can be computed independently of the build process

### Example Scenarios

```python
# Scenario 1: Same content, same URL
url1 = "https://pub.curvenote.com/12345/meca.zip"
url2 = "https://pub.curvenote.com/12345/meca.zip"
# Result: Same tag (enables caching)

# Scenario 2: Same content, different URL
url1 = "https://server1.com/bundle.zip"
url2 = "https://server2.com/bundle.zip"
# Result: Different tags (no caching)

# Scenario 3: Different content, same URL
# (Content-Length or ETag would differ)
# Result: Different tags (content change detected)
```

This deterministic tagging system ensures that MECA bundles are properly cached, versioned, and reproducible while maintaining content integrity.
