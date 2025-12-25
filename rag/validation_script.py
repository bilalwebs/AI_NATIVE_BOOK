#!/usr/bin/env python3
"""
Validation script to test the complete pipeline with sample URLs.
This script validates the end-to-end functionality of the book embedding pipeline.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.pipeline_orchestrator import BookEmbeddingPipeline
from rag.config.config import Config


def setup_logging():
    """Set up logging for the validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('validation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_basic_validation():
    """Run basic validation of the pipeline components."""
    logger = logging.getLogger(__name__)
    logger.info("Starting basic pipeline validation...")

    try:
        # Initialize the pipeline
        pipeline = BookEmbeddingPipeline()
        logger.info("Pipeline initialized successfully")

        # Check pipeline status
        status = pipeline.get_pipeline_status()
        logger.info(f"Pipeline status: {status['components_initialized']}")

        # Verify configuration
        Config.validate()
        logger.info("Configuration validation passed")

        return True, "Basic validation passed"
    except Exception as e:
        logger.error(f"Basic validation failed: {str(e)}")
        return False, f"Basic validation failed: {str(e)}"


def run_sample_pipeline_test():
    """Run a sample pipeline test with mock URLs."""
    logger = logging.getLogger(__name__)
    logger.info("Starting sample pipeline test...")

    # For testing purposes, we'll use a small sample of URLs
    # In a real scenario, these would be actual book URLs
    sample_urls = [
        "https://example.com/book/page1",
        "https://example.com/book/page2",
        "https://example.com/book/page3"
    ]

    try:
        # Initialize the pipeline
        pipeline = BookEmbeddingPipeline()

        # Run the complete pipeline
        result = pipeline.run_complete_pipeline(
            urls=sample_urls,
            validate_results=True,
            test_queries=["sample query", "test search", "example content"]
        )

        success = result.get('success', False)
        message = result.get('message', 'Unknown result')

        logger.info(f"Sample pipeline test result: {message}")

        if success:
            logger.info("Sample pipeline test completed successfully")
            return True, message
        else:
            logger.error(f"Sample pipeline test failed: {message}")
            return False, message

    except Exception as e:
        logger.error(f"Sample pipeline test failed with exception: {str(e)}")
        return False, f"Sample pipeline test failed: {str(e)}"


def run_performance_test():
    """Run performance validation to ensure pipeline completes within time limits."""
    logger = logging.getLogger(__name__)
    logger.info("Starting performance validation...")

    try:
        # Test with a larger set of mock URLs to validate performance
        test_urls = [f"https://example.com/book/page{i}" for i in range(1, 11)]  # 10 pages

        start_time = datetime.utcnow()
        pipeline = BookEmbeddingPipeline()

        result = pipeline.run_complete_pipeline(
            urls=test_urls,
            validate_results=False  # Skip validation for performance test
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        success = result.get('success', False)
        message = result.get('message', 'Unknown result')

        # Check if completion time is within acceptable limits (e.g., 30 minutes for 100 pages)
        # For 10 pages, we'd expect much less time
        expected_time_for_10_pages = (30 * 60) * (10 / 100)  # 30 minutes for 100 pages = 180 seconds for 100 = 18 seconds for 10
        time_limit = max(60, expected_time_for_10_pages)  # At least 60 seconds, or calculated time

        within_time_limit = duration <= time_limit

        logger.info(f"Performance test completed in {duration:.2f} seconds")
        logger.info(f"Time limit: {time_limit:.2f} seconds, Within limit: {within_time_limit}")

        if success and within_time_limit:
            logger.info("Performance validation passed")
            return True, f"Performance validation passed: completed in {duration:.2f}s (limit: {time_limit:.2f}s)"
        else:
            status = []
            if not success:
                status.append("pipeline failed")
            if not within_time_limit:
                status.append(f"exceeded time limit ({duration:.2f}s > {time_limit:.2f}s)")
            return False, f"Performance validation failed: {', '.join(status)}"

    except Exception as e:
        logger.error(f"Performance validation failed with exception: {str(e)}")
        return False, f"Performance validation failed: {str(e)}"


def run_validation_suite():
    """Run the complete validation suite."""
    logger = logging.getLogger(__name__)
    logger.info("Starting complete validation suite...")

    results = {
        'basic_validation': run_basic_validation(),
        'sample_pipeline_test': run_sample_pipeline_test(),
        'performance_test': run_performance_test()
    }

    # Summarize results
    passed_count = sum(1 for result in results.values() if result[0])
    total_count = len(results)

    logger.info(f"Validation suite completed: {passed_count}/{total_count} tests passed")

    for test_name, (success, message) in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status} - {message}")

    overall_success = all(result[0] for result in results.values())

    if overall_success:
        logger.info("🎉 All validation tests passed!")
        return True
    else:
        logger.error("❌ Some validation tests failed!")
        return False


def main():
    """Main function to run the validation script."""
    print("🔍 Running Book Embedding Pipeline Validation...")
    print("=" * 60)

    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Check if required environment variables are set
    missing_vars = []
    if not os.getenv('COHERE_API_KEY'):
        missing_vars.append('COHERE_API_KEY')
    if not os.getenv('QDRANT_API_KEY'):
        missing_vars.append('QDRANT_API_KEY')
    if not os.getenv('QDRANT_URL'):
        missing_vars.append('QDRANT_URL')

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the validation.")
        return 1

    try:
        # Run the complete validation suite
        success = run_validation_suite()

        if success:
            print("\n✅ All validation tests completed successfully!")
            return 0
        else:
            print("\n❌ Some validation tests failed!")
            return 1

    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        print("\n⚠️  Validation interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {str(e)}")
        print(f"\n💥 Validation failed with unexpected error: {str(e)}")
        return 3


if __name__ == "__main__":
    sys.exit(main())