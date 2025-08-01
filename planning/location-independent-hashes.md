# Location-Independent Image Naming for MECA Bundles

## Current State: Location-Dependent Naming

### Current Implementation
The current `MecaRepoProvider` creates image names and tags based on the **URL location** of the MECA bundle:

```python
# Current approach in utils.py
def get_hashed_slug(url, changes_with_content):
    parsed_url = urlparse(url)
    stripped_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
    )
    return "meca-" + md5(f"{stripped_url}-{changes_with_content}".encode()).hexdigest()
```

### Current Image Naming
- **Repository**: `meca-{url_hash}-{truncated_hash}`
- **Tag**: `meca-{url_hash}`

**Example:**
- URL: `https://pub.curvenote.com/12345/meca.zip`
- ETag: `"abc123"`
- Result: `meca-2df10e6d81881615d274bef324537fcd65-de1b43:meca-f10e6d81881615d274bef324537fcd65`

### Problems with Current Approach
1. **Location Dependency**: Moving a MECA bundle to a different URL creates a different image name
2. **Server Configuration Sensitivity**: Changes in ETag or Content-Length headers affect caching
3. **Fragile Caching**: Same content at different locations doesn't share cached images

## Proposed Solution: Content-Based Naming

### Goal
Make image names and tags **location-independent** by using the **actual content hash** of the MECA bundle file.

### Benefits
1. **True Content-Based**: Identical files get identical images regardless of location
2. **Portable**: Move files between servers without breaking caching
3. **Robust**: Server configuration changes don't affect caching
4. **Deterministic**: Same content = same image, always

## Cloud Storage Content-MD5 Support

### Services with Content-MD5 Headers

#### ✅ **Google Cloud Storage**
```bash
curl -I "https://storage.googleapis.com/bucket/object.zip"
# Headers:
# Content-MD5: abc123def456... (base64-encoded)
# ETag: "abc123def456..."
```

#### ✅ **AWS S3**
```bash
curl -I "https://bucket.s3.amazonaws.com/object.zip"
# Headers:
# ETag: "abc123def456..." (quoted MD5)
# Content-MD5: abc123def456... (base64-encoded)
```

#### ✅ **Azure Blob Storage**
```bash
curl -I "https://account.blob.core.windows.net/container/object.zip"
# Headers:
# Content-MD5: abc123def456... (base64-encoded)
# ETag: "0xabc123def456..." (hex format)
```

#### ✅ **Supabase Storage**
```bash
curl -I "https://project.supabase.co/storage/v1/object/public/bucket/object.zip"
# Headers:
# Content-MD5: abc123def456... (base64-encoded)
# ETag: "abc123def456..."
```

#### ✅ **DigitalOcean Spaces**
```bash
curl -I "https://bucket.region.digitaloceanspaces.com/object.zip"
# Headers:
# ETag: "abc123def456..." (quoted MD5)
# Content-MD5: abc123def456... (base64-encoded)
```

#### ✅ **Backblaze B2**
```bash
curl -I "https://f004.backblazeb2.com/file/bucket/object.zip"
# Headers:
# ETag: "abc123def456..." (quoted MD5)
# Content-MD5: abc123def456... (base64-encoded)
```

### Services with Limited MD5 Support

#### ⚠️ **GitHub Releases**
```bash
curl -I "https://github.com/user/repo/releases/download/v1.0/bundle.zip"
# Headers:
# ETag: "abc123def456..." (quoted SHA256, not MD5)
# No Content-MD5 header
```

#### ⚠️ **Generic HTTP Servers**
```bash
curl -I "https://example.com/bundle.zip"
# Headers:
# ETag: "abc123" (may be weak ETag)
# No Content-MD5 header
```

## Implementation Strategies

### Strategy 1: Full Content Download (Location-Independent)

#### Modified MecaRepoProvider
```python
async def get_resolved_ref(self):
    # Download the file to get its MD5
    client = AsyncHTTPClient()
    req = HTTPRequest(self.url, method="GET")
    response = await client.fetch(req)
    
    # Calculate MD5 of the actual content
    content_hash = md5(response.body).hexdigest()
    
    self.hashed_slug = f"meca-{content_hash}"
    return self.hashed_slug
```

#### Performance Implications
- **Pros**: True content-based, location-independent
- **Cons**: 
  - Downloads entire zip file (could be 100MB+)
  - Slower response time
  - Higher bandwidth usage
  - More expensive for large files

#### Modified MecaContentProvider
```python
def fetch(self, spec, output_dir, yield_output=False):
    # ... existing download code ...
    
    # Calculate content hash from actual file
    with open(zip_filename, 'rb') as f:
        content_hash = md5(f.read()).hexdigest()
    
    # Store the content hash for the provider to use
    self.content_hash = content_hash
    
    # ... rest of extraction code ...
```

#### Result
- **Repository**: `meca-{content_hash}-{truncated_hash}`
- **Tag**: `meca-{content_hash}`

### Strategy 2: Cloud Storage MD5 Headers (RECOMMENDED)

#### Universal Implementation for Cloud Storage
```python
async def get_resolved_ref(self):
    client = AsyncHTTPClient()
    req = HTTPRequest(self.url, method="HEAD")
    response = await client.fetch(req)
    
    # Try to get MD5 from various cloud storage headers
    content_hash = None
    
    # Check for Content-MD5 header (GCS, Azure, Supabase)
    content_md5 = response.headers.get("Content-MD5")
    if content_md5:
        import base64
        content_hash = base64.b64decode(content_md5).hex()
    
    # Check for ETag that looks like MD5 (AWS S3, DigitalOcean, Backblaze)
    elif response.headers.get("ETag"):
        etag = response.headers.get("ETag").strip('"')
        # Check if ETag looks like MD5 (32 hex characters)
        if len(etag) == 32 and all(c in '0123456789abcdef' for c in etag.lower()):
            content_hash = etag
    
    # Fallback to current approach
    if not content_hash:
        content_hash = md5(f"{self.url}-{response.headers.get('ETag') or response.headers.get('Content-Length')}".encode()).hexdigest()
    
    self.hashed_slug = f"meca-{content_hash}"
    return self.hashed_slug
```

#### Benefits of Cloud Storage Approach
1. **No Download Required**: Get the MD5 without downloading the file
2. **Fast**: HEAD request is much faster than GET
3. **Reliable**: Cloud providers guarantee the MD5 is accurate
4. **Location-Independent**: Same file on different buckets = same MD5
5. **Wide Support**: Works with most major cloud storage providers
6. **Cost-Effective**: No bandwidth costs for large files

### Strategy 3: Hybrid Approach

#### Content-Based Tags, URL-Based Repository Names
```python
# Use content hash for tag, URL hash for repository name
tag = f"meca-{content_hash}"
repo_name = f"meca-{url_hash}-{content_hash[:6]}"
```

#### Benefits
- **Location-independent tags** (content-based)
- **Location-dependent repository names** (for organization)
- **Content-based caching** (same content = same tag)

## Per-Deployment Configuration Strategy

### Configuration Options

Add these configuration options to `MecaRepoProvider`:

```python
from traitlets import Unicode, Bool, default
import os

class MecaRepoProvider(RepoProvider):
    # ... existing code ...
    
    # Add new configuration options
    hash_scheme = Unicode(
        "url",  # default to current URL-based scheme
        config=True,
        help="""Hashing scheme to use for MECA bundles.
        
        Options:
        - 'url': Use URL + metadata (current, location-dependent)
        - 'cloud': Use cloud storage MD5 headers (location-independent)
        - 'content': Use actual file content MD5 (location-independent, downloads file)
        """
    )
    
    enable_content_hashing = Bool(
        False,
        config=True,
        help="Enable content-based hashing for location-independent image names"
    )
    
    @default("hash_scheme")
    def _hash_scheme_default(self):
        return os.getenv("MECA_HASH_SCHEME", "url")
    
    @default("enable_content_hashing")
    def _enable_content_hashing_default(self):
        return os.getenv("MECA_ENABLE_CONTENT_HASHING", "false").lower() == "true"
```

### Modified get_resolved_ref() Method

```python
async def get_resolved_ref(self):
    client = AsyncHTTPClient()
    req = HTTPRequest(self.url, method="HEAD", user_agent="BinderHub")
    self.log.info(f"get_resolved_ref() HEAD: {self.url}")
    
    try:
        r = await client.fetch(req)
        self.log.info(f"URL is reachable: {self.url}")
        
        if self.hash_scheme == "cloud":
            # Use cloud storage MD5 headers (no download)
            self.log.info("Using cloud storage MD5 headers")
            content_hash = self._get_cloud_md5(r.headers)
            self.hashed_slug = f"meca-{content_hash}"
            
        elif self.hash_scheme == "content":
            # Content-based hashing - download the file
            self.log.info("Using content-based hashing")
            content_req = HTTPRequest(self.url, method="GET", user_agent="BinderHub")
            content_response = await client.fetch(content_req)
            content_hash = md5(content_response.body).hexdigest()
            self.hashed_slug = f"meca-{content_hash}"
            
        else:
            # Default URL-based hashing
            self.log.info("Using URL-based hashing")
            self.hashed_slug = get_hashed_slug(
                self.url, r.headers.get("ETag") or r.headers.get("Content-Length")
            )
            
    except Exception as e:
        raise ValueError(f"URL is unreachable ({e})")

    self.log.info(f"hashed_slug: {self.hashed_slug}")
    return self.hashed_slug

def _get_cloud_md5(self, headers):
    """Extract MD5 from cloud storage headers"""
    # Check for Content-MD5 header (GCS, Azure, Supabase)
    content_md5 = headers.get("Content-MD5")
    if content_md5:
        import base64
        return base64.b64decode(content_md5).hex()
    
    # Check for ETag that looks like MD5 (AWS S3, DigitalOcean, Backblaze)
    etag = headers.get("ETag", "").strip('"')
    if len(etag) == 32 and all(c in '0123456789abcdef' for c in etag.lower()):
        return etag
    
    # Fallback to URL-based hashing
    return get_hashed_slug(self.url, headers.get("ETag") or headers.get("Content-Length"))
```

### BinderHub Configuration

Add to `binderhub_config.py`:

```python
# MECA Provider Configuration
c.MecaRepoProvider.hash_scheme = os.getenv("MECA_HASH_SCHEME", "url")
c.MecaRepoProvider.enable_content_hashing = os.getenv("MECA_ENABLE_CONTENT_HASHING", "false").lower() == "true"
c.MecaRepoProvider.allowed_origins = os.getenv("MECA_ALLOWED_ORIGINS", "").split(",") if os.getenv("MECA_ALLOWED_ORIGINS") else []
```

### Environment Variables

```bash
# For cloud storage MD5 headers (RECOMMENDED)
export MECA_HASH_SCHEME="cloud"

# For content-based hashing (downloads file)
export MECA_HASH_SCHEME="content"
export MECA_ENABLE_CONTENT_HASHING="true"

# For URL-based hashing (current default)
export MECA_HASH_SCHEME="url"

# Optional: Restrict to specific origins
export MECA_ALLOWED_ORIGINS="storage.googleapis.com,s3.amazonaws.com,account.blob.core.windows.net"
```

### Docker Compose Example

```yaml
# docker-compose.yml
services:
  binderhub:
    environment:
      - MECA_HASH_SCHEME=cloud
      - MECA_ENABLE_CONTENT_HASHING=false
      - MECA_ALLOWED_ORIGINS=storage.googleapis.com,s3.amazonaws.com
```

### Per-Environment Configuration

```python
# Development environment
c.MecaRepoProvider.hash_scheme = "url"  # Fast, simple

# Production with cloud storage
c.MecaRepoProvider.hash_scheme = "cloud"  # Location-independent, efficient

# Research environment with content hashing
c.MecaRepoProvider.hash_scheme = "content"  # Most robust, but slower
```

## Repository Name Simplification

### Current Issue
BinderHub adds a **truncated SHA256 hash** to repository names for uniqueness:

```
meca-2df10e6d81881615d274bef324537fcd65-de1b43
                                    ^^^^^^^^
                                    truncated hash
```

### Solutions

#### Option 1: Modify BinderHub Configuration
```python
def _safe_build_slug(build_slug, limit, hash_length=0):  # Set hash_length=0
    return build_slug[:limit].lower()  # Just truncate, no hash
```

#### Option 2: Ensure Safe Build Slugs
```python
def get_build_slug(self):
    # Ensure the slug is already safe for Docker naming
    safe_slug = self.hashed_slug.replace("_", "-").lower()
    # Make sure it doesn't end with a dash
    if safe_slug.endswith("-"):
        safe_slug = safe_slug[:-1]
    return safe_slug
```

#### Option 3: Simple Naming
```python
def get_build_slug(self):
    return "meca-bundle"  # Simple, safe name
```

## Implementation Recommendations

### For Cloud Storage (RECOMMENDED)
1. **Use Strategy 2**: Leverage cloud storage MD5 headers
2. **Implement Option 2**: Ensure safe build slugs
3. **Result**: Clean, location-independent naming
4. **Wide Compatibility**: Works with GCS, AWS S3, Azure, Supabase, DigitalOcean, Backblaze
5. **Performance**: No file downloads required
6. **Cost-Effective**: Minimal bandwidth usage for large files

### For Other Storage Systems
1. **Use Strategy 1**: Download and calculate MD5
2. **Consider performance implications**
3. **Implement caching for repeated requests**

### Migration Strategy
1. **Phase 1**: Implement cloud storage MD5 headers approach
2. **Phase 2**: Configure per-deployment settings
3. **Phase 3**: Monitor caching effectiveness
4. **Phase 4**: Gradually migrate existing images (optional)

## Example Outcomes

### Current (Location-Dependent)
```
URL1: https://server1.com/bundle.zip → meca-hash1-de1b43:meca-hash1
URL2: https://server2.com/bundle.zip → meca-hash2-abc123:meca-hash2
```

### Proposed (Location-Independent)
```
URL1: https://server1.com/bundle.zip → meca-content123-de1b43:meca-content123
URL2: https://server2.com/bundle.zip → meca-content123-de1b43:meca-content123
```

## Benefits Summary

1. **True Content-Based Caching**: Identical files share cached images
2. **Portability**: Move files between locations without breaking caching
3. **Robustness**: Server configuration changes don't affect image names
4. **Deterministic**: Same content always produces same image name
5. **Performance**: Cloud storage approach avoids file downloads
6. **Compatibility**: Maintains existing BinderHub integration
7. **Wide Support**: Works with most major cloud storage providers
8. **Configurable**: Per-deployment hashing scheme selection
9. **Cost-Effective**: Minimal bandwidth usage for large files
10. **Flexible**: Easy migration between different hashing strategies

This approach would make MECA bundle caching much more effective and reliable across different storage locations and server configurations, with the cloud storage MD5 headers approach being the most efficient and practical solution.
