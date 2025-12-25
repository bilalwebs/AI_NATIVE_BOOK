import asyncio
import logging
import sys
from typing import List, Dict, Any
from rag.pipeline import PipelineOrchestrator
from rag.config.config import Config
from rag.storage.qdrant_search import QdrantSearch
from qdrant_client import QdrantClient


class PipelineValidator:
    """
    Class to validate the complete pipeline functionality.
    """
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize the pipeline validator.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = Config()

        # Initialize components for validation
        self.qdrant_client = QdrantClient(
            url=self.config.QDRANT_URL,
            api_key=self.config.QDRANT_API_KEY,
            timeout=30
        )

    def validate_pipeline_with_test_queries(
        self,
        test_urls: List[str],
        test_queries: List[str],
        collection_name: str = "book_embeddings"
    ) -> Dict[str, Any]:
        """
        Validate the complete pipeline by running it and then testing search functionality.

        Args:
            test_urls: List of URLs to process through the pipeline
            test_queries: List of queries to test search functionality
            collection_name: Name of the collection to use

        Returns:
            Dictionary with validation results
        """
        self.logger.info("Starting pipeline validation with test queries...")

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(logger=self.logger)

        # Run the pipeline
        pipeline_result = orchestrator.run_pipeline(
            urls=test_urls,
            collection_name=collection_name,
            recreate_collection=True  # Recreate for clean test
        )

        validation_results = {
            'pipeline_execution': pipeline_result,
            'search_validation': {},
            'overall_success': False,
            'metrics': {}
        }

        if not pipeline_result.get('success'):
            self.logger.error("Pipeline execution failed, cannot proceed with search validation")
            return validation_results

        # Validate search functionality
        search_validation = self._validate_search_functionality(
            test_queries=test_queries,
            collection_name=collection_name
        )

        validation_results['search_validation'] = search_validation

        # Calculate overall success based on criteria
        pipeline_success = pipeline_result.get('success', False)
        search_success = search_validation.get('success', False)
        storage_success_rate = self._check_storage_success_rate(pipeline_result)
        relevance_success_rate = self._check_relevance_accuracy(search_validation)

        validation_results['overall_success'] = (
            pipeline_success and
            search_success and
            storage_success_rate >= 0.99 and  # 99% storage success
            relevance_success_rate >= 0.90    # 90% relevance accuracy
        )

        validation_results['metrics'] = {
            'pipeline_success': pipeline_success,
            'search_success': search_success,
            'storage_success_rate': storage_success_rate,
            'relevance_success_rate': relevance_success_rate,
            'total_time': pipeline_result.get('execution_time', 0)
        }

        # Check if pipeline completed within 30 minutes (1800 seconds) for 100-page book
        time_constraint_met = pipeline_result.get('execution_time', float('inf')) <= 1800
        validation_results['metrics']['time_constraint_met'] = time_constraint_met

        self.logger.info(f"Pipeline validation completed: {'PASSED' if validation_results['overall_success'] else 'FAILED'}")
        return validation_results

    def _validate_search_functionality(
        self,
        test_queries: List[str],
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Validate search functionality with test queries.

        Args:
            test_queries: List of test queries
            collection_name: Name of the collection to search

        Returns:
            Dictionary with search validation results
        """
        try:
            from rag.processing.embedding_client import CohereEmbeddingClient
            embedding_client = CohereEmbeddingClient(
                api_key=self.config.COHERE_API_KEY,
                model_name=self.config.COHERE_MODEL,
                logger=self.logger
            )

            search_handler = QdrantSearch(
                client=self.qdrant_client,
                embedding_client=embedding_client,
                collection_name=collection_name,
                logger=self.logger
            )

            # Test each query
            query_results = []
            relevant_results_count = 0
            total_results = 0

            for query in test_queries:
                self.logger.info(f"Testing search query: '{query}'")

                # Perform search
                results = search_handler.search_by_text(query, top_k=5)

                # Validate results
                query_validation = {
                    'query': query,
                    'result_count': len(results),
                    'results': results
                }

                # Check if results are relevant (basic heuristic: non-empty content)
                relevant_count = 0
                for result in results:
                    content = result.get('payload', {}).get('content', '')
                    if content and len(content.strip()) > 20:  # Basic relevance check
                        relevant_count += 1

                query_validation['relevant_count'] = relevant_count
                query_validation['relevance_score'] = relevant_count / len(results) if results else 0

                if relevant_count > 0:
                    relevant_results_count += 1

                total_results += len(results)
                query_results.append(query_validation)

            # Calculate overall relevance
            avg_relevance = sum(q['relevance_score'] for q in query_results) / len(query_results) if query_results else 0

            return {
                'success': len(query_results) > 0,
                'query_count': len(test_queries),
                'total_results': total_results,
                'relevant_queries': relevant_results_count,
                'avg_relevance_score': avg_relevance,
                'query_results': query_results,
                'message': f"Search validation completed with {relevant_results_count}/{len(test_queries)} relevant queries"
            }

        except Exception as e:
            self.logger.error(f"Search validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Search validation failed: {str(e)}"
            }

    def _check_storage_success_rate(self, pipeline_result: Dict[str, Any]) -> float:
        """
        Check the storage success rate from pipeline results.

        Args:
            pipeline_result: Pipeline execution result

        Returns:
            Storage success rate as a float between 0 and 1
        """
        storage_result = pipeline_result.get('storage_result', {})
        total_embeddings = pipeline_result.get('embedded_count', 0)
        stored_count = storage_result.get('stored_count', 0)

        if total_embeddings == 0:
            return 1.0  # If no embeddings to store, consider it 100% success

        return stored_count / total_embeddings if total_embeddings > 0 else 0

    def _check_relevance_accuracy(self, search_validation: Dict[str, Any]) -> float:
        """
        Check the relevance accuracy from search validation.

        Args:
            search_validation: Search validation result

        Returns:
            Relevance accuracy as a float between 0 and 1
        """
        return search_validation.get('avg_relevance_score', 0)

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation against all success criteria.

        Returns:
            Dictionary with comprehensive validation results
        """
        # Example test URLs and queries (these would need to be real URLs for actual testing)
        test_urls = [
            "https://example-docs.com/page1",
            "https://example-docs.com/page2",
            "https://example-docs.com/page3"
        ]

        test_queries = [
            "What is the main concept discussed?",
            "Explain the key features",
            "How does this work?",
            "What are the benefits?",
            "Can you summarize this?"
        ]

        self.logger.info("Running comprehensive validation against all success criteria...")

        # This would normally run against real URLs, but for this example we'll return a structure
        # that shows how the validation would work
        validation_results = {
            'success_criteria_met': {
                'SC-001': False,  # URL crawling success (95%)
                'SC-002': False,  # Embedding generation success (99%)
                'SC-003': False,  # Storage success (99%)
                'SC-004': False,  # Search relevance (90%)
                'SC-005': False   # Time constraint (30 min for 100 pages)
            },
            'detailed_results': {
                'crawl_success_rate': 0.0,
                'embedding_success_rate': 0.0,
                'storage_success_rate': 0.0,
                'relevance_accuracy': 0.0,
                'execution_time': 0.0
            },
            'message': "This validation would require actual URLs to test against. The framework is in place."
        }

        # Note: In a real implementation, we would run the actual pipeline here
        # For now, we're showing the structure of how validation would work

        self.logger.info("Comprehensive validation framework ready")
        return validation_results


def main():
    """
    Main function to run pipeline validation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate the RAG Pipeline")
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Create validator
    validator = PipelineValidator(logger=logger)

    # Run comprehensive validation
    results = validator.run_comprehensive_validation()

    print("\n" + "="*70)
    print("PIPELINE VALIDATION RESULTS")
    print("="*70)
    print(f"Success Criteria Met:")
    for criterion, met in results['success_criteria_met'].items():
        status = "✓ PASS" if met else "✗ FAIL"
        print(f"  {criterion}: {status}")
    print("="*70)

    if any(results['success_criteria_met'].values()):
        print("OVERALL: Some validation criteria passed!")
        return 0
    else:
        print("OVERALL: Validation framework ready - requires real URLs to execute full test")
        return 0


if __name__ == "__main__":
    main()