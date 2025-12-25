from typing import Dict, Any, List
import logging


class CrawlingValidator:
    """
    Class to validate crawling results against specified success criteria.
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_crawling_success_rate(
        self,
        results: List[Dict[str, Any]],
        required_success_rate: float = 95.0
    ) -> Dict[str, Any]:
        """
        Validate that the crawling success rate meets the required threshold.

        Args:
            results: List of crawling results
            required_success_rate: Required success rate percentage (default 95%)

        Returns:
            Dictionary with validation results
        """
        if not results:
            return {
                'valid': False,
                'success_rate': 0.0,
                'required_rate': required_success_rate,
                'total_items': 0,
                'successful_items': 0,
                'failed_items': 0,
                'message': 'No results to validate'
            }

        total_items = len(results)
        successful_items = sum(1 for r in results if 'error' not in r and r.get('content'))
        failed_items = total_items - successful_items
        actual_success_rate = (successful_items / total_items) * 100 if total_items > 0 else 0

        is_valid = actual_success_rate >= required_success_rate

        result = {
            'valid': is_valid,
            'success_rate': actual_success_rate,
            'required_rate': required_success_rate,
            'total_items': total_items,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'message': f"Success rate of {actual_success_rate:.2f}% {'meets' if is_valid else 'does not meet'} required {required_success_rate}%"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result

    def validate_content_quality(
        self,
        results: List[Dict[str, Any]],
        min_content_length: int = 50
    ) -> Dict[str, Any]:
        """
        Validate content quality based on minimum length requirements.

        Args:
            results: List of crawling results
            min_content_length: Minimum content length in characters

        Returns:
            Dictionary with validation results
        """
        if not results:
            return {
                'valid': False,
                'total_items': 0,
                'items_meeting_quality': 0,
                'quality_rate': 0.0,
                'min_content_length': min_content_length,
                'message': 'No results to validate'
            }

        total_items = len(results)
        quality_items = sum(
            1 for r in results
            if 'error' not in r and
            r.get('content') and
            len(r['content']) >= min_content_length
        )
        quality_rate = (quality_items / total_items) * 100 if total_items > 0 else 0

        is_valid = quality_rate > 0  # Any content meeting quality is valid

        result = {
            'valid': is_valid,
            'total_items': total_items,
            'items_meeting_quality': quality_items,
            'quality_rate': quality_rate,
            'min_content_length': min_content_length,
            'message': f"Quality rate of {quality_rate:.2f}% - {quality_items}/{total_items} items meet minimum content length of {min_content_length}"
        }

        if self.logger:
            self.logger.info(result['message'])

        return result

    def validate_urls_accessibility(
        self,
        urls: List[str],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that the URLs in results match the input URLs and check accessibility.

        Args:
            urls: Original list of URLs to crawl
            results: List of crawling results

        Returns:
            Dictionary with validation results
        """
        if not urls or not results:
            return {
                'valid': False,
                'coverage_rate': 0.0,
                'total_urls': len(urls) if urls else 0,
                'urls_crawled': 0,
                'message': 'No URLs or results to validate'
            }

        original_set = set(urls)
        crawled_set = {r['url'] for r in results}
        coverage_rate = (len(crawled_set) / len(original_set)) * 100 if original_set else 0

        is_valid = coverage_rate >= 95.0  # Using same threshold as success rate

        result = {
            'valid': is_valid,
            'coverage_rate': coverage_rate,
            'total_urls': len(original_set),
            'urls_crawled': len(crawled_set),
            'urls_not_crawled': list(original_set - crawled_set),
            'message': f"Coverage rate of {coverage_rate:.2f}% - {len(crawled_set)}/{len(original_set)} URLs crawled"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result

    def run_comprehensive_validation(
        self,
        urls: List[str],
        results: List[Dict[str, Any]],
        required_success_rate: float = 95.0,
        min_content_length: int = 50
    ) -> Dict[str, Any]:
        """
        Run comprehensive validation on crawling results.

        Args:
            urls: Original list of URLs to crawl
            results: List of crawling results
            required_success_rate: Required success rate percentage
            min_content_length: Minimum content length in characters

        Returns:
            Dictionary with comprehensive validation results
        """
        success_validation = self.validate_crawling_success_rate(
            results, required_success_rate
        )
        quality_validation = self.validate_content_quality(
            results, min_content_length
        )
        coverage_validation = self.validate_urls_accessibility(urls, results)

        all_valid = (
            success_validation['valid'] and
            coverage_validation['valid']
        )

        overall_result = {
            'overall_valid': all_valid,
            'success_validation': success_validation,
            'quality_validation': quality_validation,
            'coverage_validation': coverage_validation,
            'message': f"Comprehensive validation {'passed' if all_valid else 'failed'}"
        }

        if self.logger:
            log_level = logging.INFO if all_valid else logging.ERROR
            self.logger.log(log_level, overall_result['message'])

        return overall_result

    def validate_embedding_success_rate(
        self,
        embedding_results: List[Dict[str, Any]],
        required_success_rate: float = 99.0
    ) -> Dict[str, Any]:
        """
        Validate that the embedding generation success rate meets the required threshold.

        Args:
            embedding_results: List of embedding results (successful or failed)
            required_success_rate: Required success rate percentage (default 99%)

        Returns:
            Dictionary with validation results
        """
        if not embedding_results:
            return {
                'valid': False,
                'success_rate': 0.0,
                'required_rate': required_success_rate,
                'total_items': 0,
                'successful_items': 0,
                'failed_items': 0,
                'message': 'No embedding results to validate'
            }

        total_items = len(embedding_results)

        # Count successful embeddings (those with embeddings generated)
        successful_items = sum(1 for r in embedding_results if r.get('embedding') is not None and len(r.get('embedding', [])) > 0)
        failed_items = total_items - successful_items
        actual_success_rate = (successful_items / total_items) * 100 if total_items > 0 else 0

        is_valid = actual_success_rate >= required_success_rate

        result = {
            'valid': is_valid,
            'success_rate': actual_success_rate,
            'required_rate': required_success_rate,
            'total_items': total_items,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'message': f"Embedding success rate of {actual_success_rate:.2f}% {'meets' if is_valid else 'does not meet'} required {required_success_rate}%"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result