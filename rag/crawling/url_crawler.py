import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import logging
from pathlib import Path

from rag.utils.url_utils import is_valid_url, normalize_url
from rag.utils.retry_utils import retryable_request
from rag.utils.metrics import ProgressTracker


class URLCrawler:
    """
    Class to crawl Docusaurus URLs and extract clean text content.
    """
    def __init__(
        self,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        logger: logging.Logger = None
    ):
        """
        Initialize the URL crawler.

        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            logger: Logger instance for logging
        """
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        # Set a user agent to be respectful to servers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BookEmbeddingsBot/1.0)'
        })
        self.progress_tracker = ProgressTracker(logger=self.logger)

    def get_page_content(self, url: str) -> Optional[str]:
        """
        Fetch the content of a single URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content of the page or None if failed
        """
        try:
            response = retryable_request(
                'GET',
                url,
                max_retries=self.max_retries,
                base_delay=1.0,
                max_delay=30.0,
                backoff_factor=2.0,
                logger=self.logger,
                timeout=self.timeout,
                session=self.session
            )

            if response.status_code == 200:
                return response.text
            else:
                if self.logger:
                    self.logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def get_crawling_metrics(self) -> Dict[str, Any]:
        """
        Get crawling metrics for the current session.

        Returns:
            Dictionary with crawling metrics
        """
        all_metrics = self.progress_tracker.get_all_metrics()
        crawling_metrics = all_metrics.get('crawling', None)

        if crawling_metrics:
            success_rate = crawling_metrics.success_rate or 0
            return {
                'items_processed': crawling_metrics.items_processed,
                'items_successful': crawling_metrics.items_successful,
                'items_failed': crawling_metrics.items_failed,
                'success_rate': success_rate,
                'total_time_seconds': crawling_metrics.total_time_seconds or 0,
                'meets_success_threshold': success_rate >= 95.0  # 95% threshold as per spec
            }
        else:
            return {
                'items_processed': 0,
                'items_successful': 0,
                'items_failed': 0,
                'success_rate': 0.0,
                'total_time_seconds': 0,
                'meets_success_threshold': False
            }

    def extract_page_title(self, html_content: str) -> str:
        """
        Extract the title from HTML content.

        Args:
            html_content: HTML content to extract title from

        Returns:
            Page title or empty string if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
            # Try h1 as alternative
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error extracting title: {str(e)}")

        return ""

    def is_docusaurus_page(self, html_content: str) -> bool:
        """
        Check if the page appears to be a Docusaurus page.

        Args:
            html_content: HTML content to check

        Returns:
            True if likely a Docusaurus page, False otherwise
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Look for common Docusaurus elements
            docusaurus_indicators = [
                soup.find('nav', class_=lambda x: x and 'navbar' in x.lower()),
                soup.find('div', class_=lambda x: x and 'doc' in x.lower()),
                soup.find('div', class_=lambda x: x and 'theme' in x.lower()),
                soup.find('div', {'data-theme': True}),
                soup.find('link', href=lambda x: x and 'docusaurus' in str(x).lower()),
            ]

            return any(docusaurus_indicators)

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error checking if page is Docusaurus: {str(e)}")
            return False

    def extract_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract clean text content from HTML, filtering out navigation elements.

        Args:
            html_content: HTML content to extract from
            url: Source URL for context

        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove navigation and other non-content elements
            for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Remove elements with common non-content classes
            non_content_selectors = [
                '[class*="nav"]',
                '[class*="sidebar"]',
                '[class*="menu"]',
                '[class*="header"]',
                '[class*="footer"]',
                '[class*="cookie"]',
                '[class*="advertisement"]',
                '[class*="promo"]',
                '[data-testid*="nav"]',
                '[data-testid*="sidebar"]'
            ]

            for selector in non_content_selectors:
                for element in soup.select(selector):
                    element.decompose()

            # Try to find main content area (common Docusaurus selectors)
            main_content = None
            content_selectors = [
                'main',
                '[class*="docItem"]',
                '[class*="doc-content"]',
                '[class*="main-content"]',
                '[role="main"]',
                'article',
                '[class*="theme"]',
                '[class*="doc"]'
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body') or soup

            # Extract text content
            text_content = main_content.get_text(separator=' ', strip=True)

            # Extract title
            title = self.extract_page_title(html_content)

            return {
                'url': url,
                'title': title,
                'content': text_content,
                'is_docusaurus': self.is_docusaurus_page(html_content)
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting content from {url}: {str(e)}")
            return {
                'url': url,
                'title': '',
                'content': '',
                'is_docusaurus': False,
                'error': str(e)
            }

    def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl a list of URLs and extract clean text content.

        Args:
            urls: List of URLs to crawl

        Returns:
            List of dictionaries with extracted content and metadata
        """
        if not urls:
            if self.logger:
                self.logger.warning("No URLs provided to crawl")
            return []

        # Validate URLs
        valid_urls = []
        for url in urls:
            if is_valid_url(url):
                normalized_url = normalize_url(url)
                valid_urls.append(normalized_url)
            else:
                if self.logger:
                    self.logger.warning(f"Invalid URL skipped: {url}")

        if not valid_urls:
            if self.logger:
                self.logger.warning("No valid URLs to crawl")
            return []

        results = []
        total_urls = len(valid_urls)

        self.progress_tracker.start_task('crawling', total_items=total_urls)

        for i, url in enumerate(valid_urls):
            if self.logger:
                self.logger.info(f"Crawling {i+1}/{total_urls}: {url}")

            try:
                html_content = self.get_page_content(url)
                if html_content:
                    content_data = self.extract_content(html_content, url)
                    results.append(content_data)
                    self.progress_tracker.update_progress('crawling', successful=True)
                else:
                    # Failed to get content
                    results.append({
                        'url': url,
                        'title': '',
                        'content': '',
                        'error': 'Failed to fetch content'
                    })
                    self.progress_tracker.update_progress('crawling', successful=False)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error processing {url}: {str(e)}")

                results.append({
                    'url': url,
                    'title': '',
                    'content': '',
                    'error': str(e)
                })
                self.progress_tracker.update_progress('crawling', successful=False)

            # Respectful delay between requests
            if i < len(valid_urls) - 1:  # Don't delay after the last request
                time.sleep(self.delay)

        self.progress_tracker.complete_task('crawling')

        return results

    def crawl_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Crawl URLs from a file.

        Args:
            file_path: Path to file containing URLs (one per line)

        Returns:
            List of dictionaries with extracted content and metadata
        """
        from rag.url_loader import load_urls_from_file

        urls = load_urls_from_file(file_path)
        return self.crawl_urls(urls)