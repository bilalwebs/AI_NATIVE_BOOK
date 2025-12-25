"""
CSS selectors for Docusaurus-specific content areas and navigation filtering.
This module provides pre-defined selectors optimized for extracting content
from Docusaurus-generated documentation sites.
"""


class DocusaurusSelectors:
    """
    Pre-defined CSS selectors for Docusaurus sites.
    """
    # Content containers - where the main content lives
    CONTENT_CONTAINERS = [
        'main',  # Main content area
        '[class*="docItemContainer"]',  # Docusaurus doc item container
        '[class*="docMainContainer"]',  # Docusaurus main container
        '[class*="doc-content"]',  # Docusaurus content area
        '[class*="theme-content"]',  # Theme content wrapper
        '[role="main"]',  # Semantic main role
        'article',  # Article tag often used for content
        '[class*="container"]',  # Generic container (when in main content area)
    ]

    # Navigation and UI elements to exclude
    NAVIGATION_SELECTORS = [
        '[class*="navbar"]',  # Navigation bar
        '[class*="nav"]',  # Navigation elements
        '[class*="sidebar"]',  # Side navigation
        '[class*="docSidebar"]',  # Docusaurus sidebar
        '[class*="menu"]',  # Menu items
        '[class*="header"]',  # Header sections
        '[class*="footer"]',  # Footer sections
        '[class*="cookie"]',  # Cookie banners
        '[class*="advertisement"]',  # Ad elements
        '[class*="promo"]',  # Promotional elements
        '[data-testid*="nav"]',  # Test ID based navigation
        '[data-testid*="sidebar"]',  # Test ID based sidebar
        '[class*="theme-edit-this-page"]',  # Edit page links
        '[class*="theme-last-updated"]',  # Last updated info
        '[class*="pagination"]',  # Pagination controls
        '[class*="toc"]',  # Table of contents
        '[class*="table-of-contents"]',  # Table of contents alternative
        '[class*="back-to-top"]',  # Back to top button
        '[class*="theme-compliance"]',  # Compliance elements (GDPR, etc.)
        '[class*="search"]',  # Search UI elements
        '[class*="dropdown"]',  # Dropdown menus
    ]

    # Docusaurus-specific UI elements to exclude
    DOCUSAURUS_UI_SELECTORS = [
        '[data-theme="dark"]',  # Dark mode toggle
        '[class*="theme-doc-sidebar"]',  # Theme sidebar
        '[class*="theme-doc-breadcrumb"]',  # Breadcrumb
        '[class*="theme-doc-footer"]',  # Doc-specific footer
        '[class*="theme-last-updated"]',  # Last updated
        '[class*="theme-edit-this-page"]',  # Edit link
        '[class*="theme-tags"]',  # Tags
        '[class*="theme-pagination"]',  # Pagination
    ]

    # Headings that are part of the content structure
    CONTENT_HEADINGS = [
        'h1:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
        'h2:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
        'h3:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
        'h4:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
        'h5:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
        'h6:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"])',
    ]

    # Code blocks and preformatted text
    CODE_SELECTORS = [
        'pre',
        'code',
        '[class*="codeBlock"]',
        '[class*="prism"]',
        '[class*="theme-code-block"]',
    ]

    # Content paragraphs and text containers
    TEXT_CONTAINERS = [
        'p',
        'div:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"]):not([class*="footer"])',
        'li:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"]):not([class*="footer"])',
        'span:not([class*="navbar"]):not([class*="sidebar"]):not([class*="header"]):not([class*="footer"])',
    ]

    @classmethod
    def get_all_content_selectors(cls) -> list:
        """Get all selectors for content containers."""
        return cls.CONTENT_CONTAINERS

    @classmethod
    def get_all_navigation_selectors(cls) -> list:
        """Get all selectors for navigation/UI elements to exclude."""
        return cls.NAVIGATION_SELECTORS + cls.DOCUSAURUS_UI_SELECTORS

    @classmethod
    def get_all_selectors(cls) -> dict:
        """Get all selector categories."""
        return {
            'content_containers': cls.CONTENT_CONTAINERS,
            'navigation': cls.NAVIGATION_SELECTORS,
            'docusaurus_ui': cls.DOCUSAURUS_UI_SELECTORS,
            'headings': cls.CONTENT_HEADINGS,
            'code': cls.CODE_SELECTORS,
            'text_containers': cls.TEXT_CONTAINERS
        }

    @classmethod
    def get_content_extraction_selectors(cls) -> dict:
        """
        Get selectors optimized for content extraction.
        Returns a dictionary with 'include' and 'exclude' lists.
        """
        return {
            'include': cls.CONTENT_CONTAINERS + cls.CONTENT_HEADINGS + cls.TEXT_CONTAINERS,
            'exclude': cls.NAVIGATION_SELECTORS + cls.DOCUSAURUS_UI_SELECTORS
        }


# Convenience functions for common operations
def get_docusaurus_content_selector() -> str:
    """
    Get a CSS selector string for the main content area of Docusaurus sites.
    """
    return ', '.join(DocusaurusSelectors.CONTENT_CONTAINERS)


def get_docusaurus_exclude_selectors() -> str:
    """
    Get a CSS selector string for elements to exclude from content extraction.
    """
    all_excludes = (
        DocusaurusSelectors.NAVIGATION_SELECTORS +
        DocusaurusSelectors.DOCUSAURUS_UI_SELECTORS
    )
    return ', '.join(all_excludes)


def get_docusaurus_code_selectors() -> str:
    """
    Get a CSS selector string for code blocks in Docusaurus sites.
    """
    return ', '.join(DocusaurusSelectors.CODE_SELECTORS)