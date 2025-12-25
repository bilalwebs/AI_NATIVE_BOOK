from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple
import re
import logging


class ContentExtractor:
    """
    Class to extract clean text content from HTML, specifically optimized for Docusaurus pages.
    """
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def extract_headings_hierarchy(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract headings hierarchy from HTML content.

        Args:
            html_content: HTML content to extract headings from

        Returns:
            List of headings with level, text, and position
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = []

        for i, heading in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            level = int(heading.name[1])  # Extract number from h1, h2, etc.
            text = heading.get_text().strip()
            if text:
                headings.append({
                    'level': level,
                    'text': text,
                    'position': i,
                    'id': heading.get('id', ''),
                    'classes': heading.get('class', [])
                })

        return headings

    def extract_code_blocks(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from HTML content.

        Args:
            html_content: HTML content to extract code blocks from

        Returns:
            List of code blocks with language and content
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        code_blocks = []

        # Find common code block patterns in Docusaurus
        code_elements = soup.find_all(['code', 'pre'])
        for i, element in enumerate(code_elements):
            # Skip if it's inline code (inside <p> tags)
            if element.find_parent('p'):
                continue

            # Get the code content
            code_text = element.get_text().strip()
            if not code_text:
                continue

            # Try to determine language from class or data attributes
            classes = element.get('class', [])
            language = None
            for cls in classes:
                if 'language-' in cls:
                    language = cls.replace('language-', '')
                    break
                elif 'lang-' in cls:
                    language = cls.replace('lang-', '')
                    break

            # Check for data attributes
            if not language:
                language = element.get('data-language') or element.get('data-lang')

            code_blocks.append({
                'id': f"code_{i}",
                'language': language,
                'content': code_text,
                'classes': classes
            })

        return code_blocks

    def extract_text_content(self, html_content: str, include_code: bool = False) -> str:
        """
        Extract clean text content from HTML, preserving paragraph structure.

        Args:
            html_content: HTML content to extract text from
            include_code: Whether to include code blocks in the output

        Returns:
            Clean text content
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Remove navigation and other non-content elements
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

        # Try to find main content area (Docusaurus specific)
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

        # If no main content found, use the whole body
        if not main_content:
            main_content = soup.find('body') or soup

        # Extract text while preserving paragraph structure
        paragraphs = []
        for element in main_content.find_all(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text().strip()
            if text and not self._is_navigation_element(element):
                paragraphs.append(text)

        # Join paragraphs with newlines
        clean_text = '\n\n'.join(paragraphs)

        # Clean up extra whitespace
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)  # Replace multiple newlines with single
        clean_text = clean_text.strip()

        return clean_text

    def _is_navigation_element(self, element) -> bool:
        """
        Check if an element is likely a navigation element.

        Args:
            element: BeautifulSoup element to check

        Returns:
            True if element is likely navigation, False otherwise
        """
        # Check classes and IDs for navigation indicators
        classes = element.get('class', [])
        element_id = element.get('id', '').lower()
        element_classes = ' '.join(classes).lower()

        navigation_indicators = [
            'nav', 'menu', 'sidebar', 'header', 'footer', 'breadcrumb',
            'toc', 'table-of-contents', 'pagination', 'pager'
        ]

        for indicator in navigation_indicators:
            if indicator in element_classes or indicator in element_id:
                return True

        return False

    def extract_metadata(self, html_content: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML content.

        Args:
            html_content: HTML content to extract metadata from

        Returns:
            Dictionary containing extracted metadata
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        metadata = {}

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')

        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')

        # Extract Open Graph tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['og_title'] = og_title.get('content', '')

        og_description = soup.find('meta', property='og:description')
        if og_description:
            metadata['og_description'] = og_description.get('content', '')

        og_url = soup.find('meta', property='og:url')
        if og_url:
            metadata['og_url'] = og_url.get('content', '')

        # Extract canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical_url'] = canonical.get('href', '')

        # Extract other useful metadata
        metadata['word_count'] = len(self.extract_text_content(html_content).split())
        metadata['headings_count'] = len(self.extract_headings_hierarchy(html_content))

        return metadata

    def extract_structured_content(self, html_content: str) -> Dict[str, Any]:
        """
        Extract all content in a structured format.

        Args:
            html_content: HTML content to extract from

        Returns:
            Dictionary with all extracted content and metadata
        """
        return {
            'text_content': self.extract_text_content(html_content),
            'headings': self.extract_headings_hierarchy(html_content),
            'code_blocks': self.extract_code_blocks(html_content),
            'metadata': self.extract_metadata(html_content)
        }

    def clean_docusaurus_content(self, html_content: str) -> str:
        """
        Specifically clean Docusaurus content by removing common Docusaurus UI elements.

        Args:
            html_content: HTML content from Docusaurus site

        Returns:
            Clean text content
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove Docusaurus-specific navigation and UI elements
        docusaurus_selectors = [
            '[class*="navbar"]',
            '[class*="sidebar"]',
            '[class*="docSidebar"]',
            '[class*="theme-edit-this-page"]',
            '[class*="theme-last-updated"]',
            '[class*="pagination"]',
            '[class*="toc"]',
            '[class*="table-of-contents"]',
            '[data-testid="sidebar"]',
            '[data-theme="dark"]',  # Dark mode toggle
            '[class*="back-to-top"]',
            '[class*="theme-compliance"]'  # GDPR compliance elements
        ]

        for selector in docusaurus_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Find the main content area - Docusaurus specific selectors
        main_selectors = [
            '[class*="docMainContainer"]',
            '[class*="docItem"]',
            '[class*="doc-content"]',
            '[class*="main-wrapper"]',
            '[class*="container"]',
            '[role="main"]'
        ]

        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # If main content not found, use body
        if not main_content:
            main_content = soup.find('body') or soup

        # Extract clean text
        text_content = main_content.get_text(separator=' ', strip=True)

        # Clean up extra whitespace and normalize
        text_content = re.sub(r'\s+', ' ', text_content)  # Replace multiple spaces with single
        text_content = text_content.strip()

        return text_content