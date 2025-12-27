"""
Script to ingest all book documentation using sitemap.xml
"""
import argparse
import sys
import os
import logging
from typing import List

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sitemap_parser import get_all_book_urls
from pipeline import PipelineOrchestrator
from config.config import Config


def setup_logging(log_level: str = "INFO"):
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('sitemap_ingestion.log')
        ]
    )


def main():
    """
    Main entry point for sitemap-based ingestion.
    """
    parser = argparse.ArgumentParser(
        description="Ingest all book documentation using sitemap.xml"
    )
    parser.add_argument(
        '--sitemap-url',
        type=str,
        default='https://bilalaibook.vercel.app/sitemap.xml',
        help='URL to the sitemap.xml file (default: https://bilalaibook.vercel.app/sitemap.xml)'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default='https://bilalaibook.vercel.app',
        help='Base URL of the book website (default: https://bilalaibook.vercel.app)'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default='book_embeddings',
        help='Name of the Qdrant collection to store embeddings (default: book_embeddings)'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate the collection before storing (default: False)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting sitemap-based ingestion from: {args.sitemap_url}")
    logger.info(f"Base URL: {args.base_url}")

    # Get all documentation URLs from the sitemap
    try:
        doc_urls = get_all_book_urls(args.sitemap_url, args.base_url)
    except Exception as e:
        logger.error(f"Error parsing sitemap: {e}")
        sys.exit(1)

    if not doc_urls:
        logger.error("No documentation URLs found in sitemap")
        sys.exit(1)

    logger.info(f"Found {len(doc_urls)} documentation URLs to process")

    # Validate configuration
    try:
        Config().validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Create pipeline orchestrator
    try:
        orchestrator = PipelineOrchestrator()
        logger.info("Pipeline orchestrator created successfully")
    except Exception as e:
        logger.error(f"Failed to create pipeline orchestrator: {e}")
        sys.exit(1)

    # Execute the pipeline
    try:
        logger.info("Starting pipeline execution with sitemap URLs...")
        result = orchestrator.run_pipeline(
            urls=doc_urls,
            collection_name=args.collection_name,
            recreate_collection=args.recreate
        )

        logger.info("Pipeline execution completed")
        logger.info(f"Result: {result}")

        # Print summary
        if result.get('success'):
            print("\n" + "="*60)
            print("SITEMAP-BASED INGESTION SUMMARY")
            print("="*60)
            print(f"Total URLs processed: {result.get('total_urls', 0)}")
            print(f"Successfully crawled: {result.get('crawled_count', 0)}")
            print(f"Chunks processed: {result.get('processed_count', 0)}")
            print(f"Embeddings generated: {result.get('embedded_count', 0)}")
            print(f"Execution time: {result.get('execution_time', 0):.2f} seconds")
            print(f"Collection name: {args.collection_name}")
            print("="*60)
            print("SUCCESS: Sitemap-based ingestion completed successfully!")
        else:
            print("\n" + "="*60)
            print("SITEMAP-BASED INGESTION FAILED")
            print("="*60)
            print(f"Error: {result.get('message', 'Unknown error')}")
            print("="*60)
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()