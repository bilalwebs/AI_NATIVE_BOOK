"""
Sitemap parser to extract all documentation URLs from the book website
"""
import requests
from typing import List
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import logging


def parse_sitemap(sitemap_url: str, base_url: str = None) -> List[str]:
    """
    Parse a sitemap.xml file and extract all URLs.

    Args:
        sitemap_url: URL to the sitemap.xml file
        base_url: Base URL to resolve relative URLs (optional)

    Returns:
        List of URLs extracted from the sitemap
    """
    logger = logging.getLogger(__name__)

    try:
        # Fetch the sitemap
        response = requests.get(sitemap_url, timeout=30)
        response.raise_for_status()

        # Parse the XML
        root = ET.fromstring(response.content)

        # Handle both regular sitemap and sitemap index
        urls = []

        # Define namespaces for XML parsing
        namespaces = {
            'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }

        # Check if it's a sitemap index (contains other sitemaps)
        sitemap_tags = root.findall('.//sitemap:urlset/sitemap:url/sitemap:loc', namespaces) or \
                      root.findall('.//url/loc')

        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None and loc_elem.text:
                url = loc_elem.text.strip()

                # Only include URLs that are under the base URL (to avoid external links)
                if base_url and url.startswith(base_url):
                    urls.append(url)
                elif not base_url:
                    urls.append(url)

        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(urls))

        logger.info(f"Extracted {len(unique_urls)} URLs from sitemap")
        return unique_urls

    except ET.ParseError as e:
        logger.error(f"Error parsing sitemap XML: {e}")
        return []
    except requests.RequestException as e:
        logger.error(f"Error fetching sitemap: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing sitemap: {e}")
        return []


def filter_documentation_urls(urls: List[str], base_domain: str) -> List[str]:
    """
    Filter URLs to only include documentation pages.

    Args:
        urls: List of URLs to filter
        base_domain: Base domain to validate URLs

    Returns:
        Filtered list of documentation URLs
    """
    filtered_urls = []

    for url in urls:
        # Only include URLs that are from the specified domain
        if base_domain in url:
            # Filter out non-documentation pages (like home page, about, etc.)
            # Keep only URLs that look like documentation pages
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            # Include pages that are likely documentation
            # This includes /docs/, /module/, /tutorial/, etc.
            if any(keyword in path for keyword in ['docs', 'modules', 'module', 'tutorial', 'guide', 'api', 'reference']):
                filtered_urls.append(url)
            # Also include pages that are not common non-doc pages
            elif not any(keyword in path for keyword in ['/', '/index', '/about', '/contact', '/home', '/login', '/register']):
                # For pages that don't match obvious patterns, include them if they seem like content pages
                if len(path.strip('/').split('/')) > 1:  # Has subdirectories
                    filtered_urls.append(url)

    # Remove duplicates while preserving order
    unique_filtered_urls = list(dict.fromkeys(filtered_urls))

    return unique_filtered_urls


def get_all_book_urls(sitemap_url: str, base_url: str) -> List[str]:
    """
    Get all documentation URLs from the sitemap.

    Args:
        sitemap_url: URL to the sitemap.xml file
        base_url: Base URL of the book website

    Returns:
        List of all documentation URLs
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Parsing sitemap: {sitemap_url}")

    # Parse the main sitemap
    all_urls = parse_sitemap(sitemap_url, base_url)

    if not all_urls:
        logger.warning("No URLs found in sitemap")
        return []

    # Filter for documentation pages only
    doc_urls = filter_documentation_urls(all_urls, base_url)

    logger.info(f"Found {len(doc_urls)} documentation URLs")

    # Print some sample URLs for verification
    logger.info("Sample URLs:")
    for url in doc_urls[:10]:  # Show first 10 URLs
        logger.info(f"  - {url}")

    if len(doc_urls) > 10:
        logger.info(f"  ... and {len(doc_urls) - 10} more URLs")

    return doc_urls


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example usage
    sitemap_url = "https://bilalaibook.vercel.app/sitemap.xml"
    base_url = "https://bilalaibook.vercel.app"

    doc_urls = get_all_book_urls(sitemap_url, base_url)

    print(f"\nTotal documentation URLs found: {len(doc_urls)}")

    # Optionally save to file
    if doc_urls:
        with open("book_urls.txt", "w", encoding="utf-8") as f:
            for url in doc_urls:
                f.write(f"{url}\n")
        print(f"URLs saved to book_urls.txt")