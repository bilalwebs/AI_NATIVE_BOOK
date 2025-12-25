from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path


class OutputFormatter:
    """Format crawled content into standardized output structures."""

    @staticmethod
    def format_crawled_content(
        url: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "docusaurus",
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Format crawled content into a standardized structure.

        Args:
            url: Source URL
            title: Page title
            content: Extracted content
            metadata: Additional metadata
            source_type: Type of source (e.g., 'docusaurus', 'generic')
            timestamp: Timestamp of crawling (defaults to now)

        Returns:
            Formatted content dictionary
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        if metadata is None:
            metadata = {}

        return {
            'id': f"crawl_{hash(url)}_{int(timestamp.timestamp())}",
            'url': url,
            'title': title,
            'content': content,
            'source_type': source_type,
            'crawled_at': timestamp.isoformat(),
            'content_length': len(content),
            'metadata': metadata,
            'word_count': len(content.split()) if content else 0
        }

    @staticmethod
    def format_batch_results(
        results: List[Dict[str, Any]],
        source_urls: List[str],
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a batch of crawled results.

        Args:
            results: List of individual crawled content results
            source_urls: Original list of URLs that were crawled
            job_id: Optional job identifier

        Returns:
            Formatted batch results dictionary
        """
        successful_results = [r for r in results if 'error' not in r]
        failed_results = [r for r in results if 'error' in r]

        return {
            'job_id': job_id or f"batch_{int(datetime.utcnow().timestamp())}",
            'total_urls': len(source_urls),
            'successful_crawls': len(successful_results),
            'failed_crawls': len(failed_results),
            'success_rate': len(successful_results) / len(source_urls) * 100 if source_urls else 0,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'results': results,
            'summary': {
                'total_content_length': sum(r.get('content_length', 0) for r in successful_results),
                'total_word_count': sum(r.get('word_count', 0) for r in successful_results),
                'successful_urls': [r['url'] for r in successful_results],
                'failed_urls': [r['url'] for r in failed_results]
            }
        }

    @staticmethod
    def save_to_json(data: Dict[str, Any], output_path: str) -> bool:
        """
        Save formatted data to a JSON file.

        Args:
            data: Data to save
            output_path: Path to output file

        Returns:
            True if successful, False otherwise
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving to JSON: {str(e)}")
            return False

    @staticmethod
    def save_to_text(content: str, output_path: str) -> bool:
        """
        Save content to a text file.

        Args:
            content: Content to save
            output_path: Path to output file

        Returns:
            True if successful, False otherwise
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True
        except Exception as e:
            print(f"Error saving to text file: {str(e)}")
            return False

    @staticmethod
    def save_batch_results_to_files(
        batch_results: Dict[str, Any],
        output_dir: str,
        format_type: str = "json"
    ) -> bool:
        """
        Save batch results to files in the specified format.

        Args:
            batch_results: Batch results to save
            output_dir: Directory to save files to
            format_type: Format to use ('json' or 'text')

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_dir) / f"crawl_results_{batch_results['job_id']}.{format_type}"

            if format_type == "json":
                return OutputFormatter.save_to_json(batch_results, str(output_path))
            elif format_type == "text":
                # For text format, save each result separately
                success = True
                for i, result in enumerate(batch_results['results']):
                    text_output_path = Path(output_dir) / f"result_{i}.txt"
                    content = f"URL: {result['url']}\nTitle: {result['title']}\n\n{result['content']}"
                    success &= OutputFormatter.save_to_text(content, str(text_output_path))
                return success
            else:
                raise ValueError(f"Unsupported format type: {format_type}")

        except Exception as e:
            print(f"Error saving batch results: {str(e)}")
            return False

    @staticmethod
    def validate_output_format(result: Dict[str, Any]) -> List[str]:
        """
        Validate that a result follows the expected output format.

        Args:
            result: Result to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        required_fields = ['id', 'url', 'title', 'content', 'crawled_at']
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        # Validate URL format
        if 'url' in result and not result['url'].startswith(('http://', 'https://')):
            errors.append("URL must start with http:// or https://")

        # Validate content is not empty (unless there's an error)
        if 'content' in result and 'error' not in result and not result['content'].strip():
            errors.append("Content is empty")

        # Validate timestamp format
        if 'crawled_at' in result:
            try:
                datetime.fromisoformat(result['crawled_at'].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid timestamp format")

        return errors

    @staticmethod
    def filter_content_by_length(results: List[Dict[str, Any]], min_length: int = 50) -> List[Dict[str, Any]]:
        """
        Filter results by minimum content length.

        Args:
            results: List of results to filter
            min_length: Minimum content length in characters

        Returns:
            Filtered list of results
        """
        return [
            r for r in results
            if r.get('content') and len(r['content']) >= min_length and 'error' not in r
        ]

    @staticmethod
    def extract_content_chunks(
        result: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract content into overlapping chunks.

        Args:
            result: Single crawled result
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of content chunks with metadata
        """
        content = result.get('content', '')
        if not content:
            return []

        chunks = []
        start = 0
        content_length = len(content)

        while start < content_length:
            end = start + chunk_size
            chunk_content = content[start:end]

            # Add overlap if not at the end
            if end < content_length and overlap > 0:
                overlap_end = min(end + overlap, content_length)
                chunk_content = content[start:overlap_end]

            chunk = {
                'chunk_id': f"{result['id']}_chunk_{len(chunks)}",
                'content': chunk_content,
                'source_url': result['url'],
                'source_title': result['title'],
                'chunk_index': len(chunks),
                'total_chunks': 0,  # Will be updated after all chunks are created
                'metadata': {
                    'original_id': result['id'],
                    'crawled_at': result['crawled_at'],
                    'source_type': result.get('source_type', 'unknown')
                }
            }

            chunks.append(chunk)
            start = end  # Move to the next non-overlapping position

        # Update total_chunks for each chunk
        for i, chunk in enumerate(chunks):
            chunk['total_chunks'] = len(chunks)

        return chunks