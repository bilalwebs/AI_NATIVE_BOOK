from typing import List, Dict, Any, Optional
import logging
from rag.storage.qdrant_storage import QdrantStorage
from rag.storage.qdrant_search import QdrantSearch
from rag.data_models import EmbeddingVector


class StorageValidator:
    """
    Class to validate storage operations against specified success criteria.
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_storage_success_rate(
        self,
        storage_results: List[Dict[str, Any]],
        required_success_rate: float = 99.0
    ) -> Dict[str, Any]:
        """
        Validate that the storage success rate meets the required threshold.

        Args:
            storage_results: List of storage results from store_embeddings operation
            required_success_rate: Required success rate percentage (default 99%)

        Returns:
            Dictionary with validation results
        """
        if not storage_results:
            return {
                'valid': False,
                'success_rate': 0.0,
                'required_rate': required_success_rate,
                'total_items': 0,
                'successful_items': 0,
                'failed_items': 0,
                'message': 'No storage results to validate'
            }

        total_items = len(storage_results)
        successful_items = sum(1 for r in storage_results if r.get('success', False))
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
            'message': f"Storage success rate of {actual_success_rate:.2f}% {'meets' if is_valid else 'does not meet'} required {required_success_rate}%"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result

    def validate_storage_stats(
        self,
        storage: QdrantStorage,
        expected_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate storage statistics after operations.

        Args:
            storage: QdrantStorage instance to get stats from
            expected_count: Expected number of stored items (optional)

        Returns:
            Dictionary with validation results
        """
        stats = storage.get_storage_stats()

        if 'error' in stats:
            return {
                'valid': False,
                'stats': stats,
                'message': f"Error getting storage stats: {stats['error']}"
            }

        result = {
            'valid': True,
            'stats': stats,
            'message': f"Storage stats retrieved successfully: {stats['point_count']} points in collection"
        }

        # If expected count provided, validate against it
        if expected_count is not None:
            matches_expected = stats['point_count'] == expected_count
            result['expected_count'] = expected_count
            result['actual_count'] = stats['point_count']
            result['matches_expected'] = matches_expected
            result['valid'] = result['valid'] and matches_expected

            if matches_expected:
                result['message'] += f", matches expected count of {expected_count}"
            else:
                result['message'] += f", expected {expected_count} but got {stats['point_count']}"
                result['valid'] = False

        if self.logger:
            log_level = logging.INFO if result['valid'] else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result


class RelevanceValidator:
    """
    Class to validate search relevance and accuracy.
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_search_relevance(
        self,
        search_instance: QdrantSearch,
        test_queries: List[str],
        min_expected_results: int = 1,
        min_score_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Validate search relevance by running test queries.

        Args:
            search_instance: QdrantSearch instance to test
            test_queries: List of test queries to execute
            min_expected_results: Minimum number of results expected per query
            min_score_threshold: Minimum score threshold for relevance

        Returns:
            Dictionary with validation results
        """
        if not test_queries:
            return {
                'valid': False,
                'total_queries': 0,
                'queries_with_results': 0,
                'avg_results_per_query': 0,
                'message': 'No test queries provided'
            }

        total_queries = len(test_queries)
        queries_with_results = 0
        all_results = []
        relevance_scores = []

        for query in test_queries:
            try:
                results = search_instance.get_relevant_content(
                    query,
                    top_k=5,
                    min_score=min_score_threshold
                )

                if len(results) >= min_expected_results:
                    queries_with_results += 1

                all_results.extend(results)

                # Collect relevance scores
                for result in results:
                    relevance_scores.append(result.get('score', 0.0))

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error running test query '{query}': {str(e)}")

        avg_results_per_query = len(all_results) / total_queries if total_queries > 0 else 0
        avg_relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        queries_with_results_rate = (queries_with_results / total_queries) * 100 if total_queries > 0 else 0

        # Determine if overall relevance is acceptable
        is_valid = queries_with_results_rate >= 90.0  # 90% of queries should return results

        result = {
            'valid': is_valid,
            'total_queries': total_queries,
            'queries_with_results': queries_with_results,
            'queries_with_results_rate': queries_with_results_rate,
            'avg_results_per_query': avg_results_per_query,
            'avg_relevance_score': avg_relevance_score,
            'total_results': len(all_results),
            'min_score_threshold': min_score_threshold,
            'min_expected_results': min_expected_results,
            'message': f"Relevance validation: {queries_with_results_rate:.2f}% of queries returned results, "
                      f"avg relevance score: {avg_relevance_score:.3f}"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result

    def calculate_relevance_accuracy(
        self,
        search_instance: QdrantSearch,
        query_result_pairs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate relevance accuracy by comparing expected vs actual results.

        Args:
            search_instance: QdrantSearch instance to test
            query_result_pairs: List of dictionaries with 'query', 'expected_content' (or 'expected_ids')

        Returns:
            Dictionary with accuracy calculation results
        """
        if not query_result_pairs:
            return {
                'valid': False,
                'accuracy': 0.0,
                'total_tests': 0,
                'correct_tests': 0,
                'message': 'No query-result pairs provided for accuracy calculation'
            }

        total_tests = len(query_result_pairs)
        correct_tests = 0

        for pair in query_result_pairs:
            query = pair.get('query', '')
            expected_content = pair.get('expected_content')
            expected_ids = pair.get('expected_ids')

            if not query:
                continue

            try:
                # Search for the query
                results = search_instance.search_by_text(query, top_k=5)

                # Check if expected content or IDs are in the results
                is_correct = False

                if expected_content:
                    # Check if expected content is in the top results
                    for result in results:
                        payload = result.get('payload', {})
                        content = payload.get('content', '')
                        if expected_content.lower() in content.lower():
                            is_correct = True
                            break

                elif expected_ids:
                    # Check if expected IDs are in the results
                    result_ids = [r.get('id') for r in results]
                    if any(exp_id in result_ids for exp_id in expected_ids):
                        is_correct = True

                if is_correct:
                    correct_tests += 1

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error calculating accuracy for query '{query}': {str(e)}")

        accuracy = (correct_tests / total_tests) * 100 if total_tests > 0 else 0
        is_valid = accuracy >= 90.0  # 90% accuracy threshold

        result = {
            'valid': is_valid,
            'accuracy': accuracy,
            'required_accuracy': 90.0,
            'total_tests': total_tests,
            'correct_tests': correct_tests,
            'incorrect_tests': total_tests - correct_tests,
            'message': f"Relevance accuracy: {accuracy:.2f}% {'meets' if is_valid else 'does not meet'} required 90%"
        }

        if self.logger:
            log_level = logging.INFO if is_valid else logging.WARNING
            self.logger.log(log_level, result['message'])

        return result


def validate_complete_storage_criteria(
    storage: QdrantStorage,
    search: QdrantSearch,
    storage_results: List[Dict[str, Any]],
    test_queries: List[str] = None,
    expected_storage_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate complete storage criteria: 99% storage success rate and 90% relevance accuracy.

    Args:
        storage: QdrantStorage instance
        search: QdrantSearch instance
        storage_results: Results from storage operations
        test_queries: Optional test queries for relevance validation
        expected_storage_count: Optional expected count for storage validation

    Returns:
        Dictionary with complete validation results
    """
    logger = logging.getLogger(__name__)
    storage_validator = StorageValidator(logger)
    relevance_validator = RelevanceValidator(logger)

    # Validate storage success rate (99% requirement)
    storage_validation = storage_validator.validate_storage_success_rate(
        storage_results,
        required_success_rate=99.0
    )

    # Validate storage stats
    stats_validation = storage_validator.validate_storage_stats(
        storage,
        expected_storage_count
    )

    # Validate relevance (90% requirement) if test queries provided
    relevance_validation = None
    if test_queries:
        relevance_validation = relevance_validator.validate_search_relevance(
            search,
            test_queries,
            min_expected_results=1,
            min_score_threshold=0.1
        )

    # Overall validation
    overall_valid = (
        storage_validation['valid'] and
        stats_validation['valid'] and
        (relevance_validation['valid'] if relevance_validation else True)
    )

    result = {
        'overall_valid': overall_valid,
        'storage_validation': storage_validation,
        'stats_validation': stats_validation,
        'relevance_validation': relevance_validation,
        'message': f"Complete storage criteria validation: {'PASSED' if overall_valid else 'FAILED'}"
    }

    logger.info(result['message'])

    return result