import requests
from typing import Dict, Any, List, Optional
import logging
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CrawlerError:
    """Class to handle different types of crawling errors."""

    def __init__(self, url: str, error_type: str, message: str, status_code: Optional[int] = None):
        self.url = url
        self.error_type = error_type  # 'connection', 'timeout', 'http_error', 'parsing_error', 'validation_error'
        self.message = message
        self.status_code = status_code
        self.timestamp = None

    def __str__(self):
        if self.status_code:
            return f"{self.error_type} ({self.status_code}): {self.message} for {self.url}"
        else:
            return f"{self.error_type}: {self.message} for {self.url}"


class CrawlerErrorHandler:
    """Handles errors during crawling with appropriate retry strategies."""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.errors = []

    def log_error(self, error: CrawlerError):
        """Log an error and add it to the errors list."""
        self.errors.append(error)
        if self.logger:
            self.logger.error(str(error))

    def is_retryable_error(self, error: CrawlerError) -> bool:
        """Determine if an error is retryable."""
        retryable_error_types = [
            'connection',
            'timeout',
            'http_error'
        ]

        # HTTP status codes that are retryable
        retryable_status_codes = {429, 502, 503, 504}

        return (
            error.error_type in retryable_error_types or
            (error.status_code and error.status_code in retryable_status_codes)
        )

    def handle_request_error(self, url: str, exception: Exception) -> CrawlerError:
        """Handle different types of request errors."""
        if isinstance(exception, requests.exceptions.ConnectionError):
            error = CrawlerError(
                url=url,
                error_type='connection',
                message=f"Connection error: {str(exception)}"
            )
        elif isinstance(exception, requests.exceptions.Timeout):
            error = CrawlerError(
                url=url,
                error_type='timeout',
                message=f"Request timeout: {str(exception)}"
            )
        elif isinstance(exception, requests.exceptions.HTTPError):
            response = getattr(exception, 'response', None)
            status_code = response.status_code if response else None
            error = CrawlerError(
                url=url,
                error_type='http_error',
                message=f"HTTP error: {str(exception)}",
                status_code=status_code
            )
        elif isinstance(exception, requests.exceptions.RequestException):
            error = CrawlerError(
                url=url,
                error_type='request_error',
                message=f"Request error: {str(exception)}"
            )
        else:
            error = CrawlerError(
                url=url,
                error_type='unknown_error',
                message=f"Unknown error: {str(exception)}"
            )

        self.log_error(error)
        return error

    def handle_validation_error(self, url: str, message: str) -> CrawlerError:
        """Handle validation errors."""
        error = CrawlerError(
            url=url,
            error_type='validation_error',
            message=message
        )
        self.log_error(error)
        return error

    def handle_parsing_error(self, url: str, message: str) -> CrawlerError:
        """Handle HTML parsing errors."""
        error = CrawlerError(
            url=url,
            error_type='parsing_error',
            message=message
        )
        self.log_error(error)
        return error

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors."""
        if not self.errors:
            return {'total_errors': 0, 'errors_by_type': {}, 'urls_with_errors': []}

        error_types = {}
        urls_with_errors = set()

        for error in self.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            urls_with_errors.add(error.url)

        return {
            'total_errors': len(self.errors),
            'errors_by_type': error_types,
            'urls_with_errors': list(urls_with_errors),
            'retryable_errors': sum(1 for e in self.errors if self.is_retryable_error(e))
        }

    def create_session_with_retries(
        self,
        total_retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (500, 502, 504, 429)
    ) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session


def validate_url_accessibility(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Validate if a URL is accessible and return information about its accessibility.

    Args:
        url: URL to validate
        timeout: Request timeout in seconds

    Returns:
        Dictionary with validation results
    """
    result = {
        'url': url,
        'accessible': False,
        'status_code': None,
        'content_type': None,
        'content_length': None,
        'error': None,
        'redirected_url': None
    }

    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        result['status_code'] = response.status_code
        result['content_type'] = response.headers.get('content-type', '')
        result['content_length'] = response.headers.get('content-length', 0)
        result['redirected_url'] = response.url

        # Consider 2xx and 3xx as accessible
        result['accessible'] = 200 <= response.status_code < 400

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
        result['accessible'] = False

    return result


def batch_validate_urls(urls: List[str], timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Batch validate multiple URLs for accessibility.

    Args:
        urls: List of URLs to validate
        timeout: Request timeout in seconds

    Returns:
        List of validation results for each URL
    """
    results = []
    for url in urls:
        result = validate_url_accessibility(url, timeout)
        results.append(result)
    return results


def is_docusaurus_url(url: str, content: str = None) -> bool:
    """
    Check if a URL points to a Docusaurus site, either by content analysis or URL patterns.

    Args:
        url: URL to check
        content: Optional HTML content to analyze

    Returns:
        True if likely a Docusaurus site, False otherwise
    """
    if content:
        # Check for Docusaurus-specific HTML patterns
        docusaurus_indicators = [
            'data-theme',
            'docItemContainer',
            'docMainContainer',
            'theme-doc-sidebar',
            'navbar',
            'docusaurus'
        ]

        content_lower = content.lower()
        for indicator in docusaurus_indicators:
            if indicator in content_lower:
                return True

    # Check URL patterns
    parsed = urlparse(url)
    docusaurus_patterns = [
        '.vercel.app',
        '.netlify.app',
        '.github.io',
        'docusaurus.io'
    ]

    return any(pattern in parsed.netloc for pattern in docusaurus_patterns)