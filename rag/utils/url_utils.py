from urllib.parse import urlparse, urljoin, parse_qs
from typing import List, Optional
import re


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize a URL by standardizing its format.

    Args:
        url: URL string to normalize

    Returns:
        Normalized URL
    """
    # Parse the URL
    parsed = urlparse(url)

    # Ensure scheme is present
    if not parsed.scheme:
        url = 'https://' + url
        parsed = urlparse(url)

    # Remove fragments and normalize
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Add trailing slash if path is empty
    if not parsed.path or parsed.path == '/':
        normalized = normalized.rstrip('/') + '/'

    return normalized


def is_docusaurus_url(url: str) -> bool:
    """
    Check if a URL appears to be a Docusaurus site based on common patterns.

    Args:
        url: URL to check

    Returns:
        True if likely a Docusaurus site, False otherwise
    """
    # Check for common Docusaurus patterns in the HTML response
    # This would typically require fetching the page, but we can check for patterns in the URL
    parsed = urlparse(url)

    # Common Docusaurus hosting patterns
    docusaurus_patterns = [
        '.vercel.app',
        '.netlify.app',
        '.github.io',
        'docusaurus.io'
    ]

    return any(pattern in parsed.netloc for pattern in docusaurus_patterns)


def extract_canonical_url(html_content: str, base_url: str) -> Optional[str]:
    """
    Extract canonical URL from HTML content if present.

    Args:
        html_content: HTML content to search
        base_url: Base URL for relative canonical links

    Returns:
        Canonical URL if found, None otherwise
    """
    # Look for canonical link tag
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html_content, re.IGNORECASE)

    if canonical_match:
        canonical_url = canonical_match.group(1)
        # If it's a relative URL, join with base URL
        if canonical_url.startswith('/'):
            from urllib.parse import urljoin
            return urljoin(base_url, canonical_url)
        elif canonical_url.startswith(('http://', 'https://')):
            return canonical_url
        else:
            return urljoin(base_url, canonical_url)

    return None


def get_robots_txt_url(base_url: str) -> str:
    """
    Get the robots.txt URL for a given base URL.

    Args:
        base_url: Base URL

    Returns:
        robots.txt URL
    """
    return urljoin(base_url.rstrip('/') + '/', 'robots.txt')


def sanitize_query_params(url: str, allowed_params: List[str] = None) -> str:
    """
    Remove or filter query parameters from URL.

    Args:
        url: URL to sanitize
        allowed_params: List of query parameters to keep (default: keep all)

    Returns:
        Sanitized URL
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if allowed_params is not None:
        # Keep only allowed parameters
        filtered_params = {k: v for k, v in query_params.items() if k in allowed_params}
    else:
        # Keep all parameters
        filtered_params = query_params

    # Reconstruct query string
    query_string = '&'.join([f"{k}={'&'.join(v)}" for k, v in filtered_params.items()])

    # Reconstruct URL
    sanitized = parsed._replace(query=query_string).geturl()

    return sanitized