import os
from typing import List
from pathlib import Path


def load_urls_from_file(file_path: str) -> List[str]:
    """
    Load URLs from a text file, one URL per line.

    Args:
        file_path: Path to the file containing URLs

    Returns:
        List of URLs
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"URL file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    return urls


def load_urls_from_env() -> List[str]:
    """
    Load URLs from environment variable.

    Returns:
        List of URLs
    """
    urls_str = os.getenv('BOOK_URLS')
    if not urls_str:
        return []

    # Split by comma or newline
    urls = [url.strip() for url in urls_str.replace('\n', ',').split(',') if url.strip()]
    return urls


def load_urls(urls_input: str = None) -> List[str]:
    """
    Load URLs from either a file or environment variable.

    Args:
        urls_input: Either a file path or a comma-separated list of URLs

    Returns:
        List of URLs
    """
    if urls_input and os.path.exists(urls_input):
        # If input is a file path
        return load_urls_from_file(urls_input)
    elif urls_input:
        # If input is a comma-separated string
        return [url.strip() for url in urls_input.split(',') if url.strip()]
    else:
        # Try to load from environment variable
        urls = load_urls_from_env()
        if not urls:
            raise ValueError("No URLs provided. Either specify a file path, comma-separated URLs, or set BOOK_URLS environment variable.")
        return urls