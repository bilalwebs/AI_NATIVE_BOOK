import argparse
import sys
import logging
import os
from typing import List
from rag.pipeline import PipelineOrchestrator
from rag.config.config import Config


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
            logging.FileHandler('pipeline.log')
        ]
    )


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


def main():
    """
    Main entry point for the RAG pipeline.
    """
    parser = argparse.ArgumentParser(
        description="RAG Pipeline: Crawl Docusaurus URLs, generate embeddings, and store in Qdrant Cloud"
    )
    parser.add_argument(
        '--urls',
        nargs='+',
        help='List of URLs to process (alternative to --url-file)'
    )
    parser.add_argument(
        '--url-file',
        type=str,
        help='Path to a text file containing URLs to process (one per line)'
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

    # Validate inputs
    if not args.urls and not args.url_file:
        logger.error("Either --urls or --url-file must be provided")
        parser.print_help()
        sys.exit(1)

    # Load URLs
    urls = []
    if args.urls:
        urls.extend(args.urls)
    if args.url_file:
        try:
            file_urls = load_urls_from_file(args.url_file)
            urls.extend(file_urls)
        except Exception as e:
            logger.error(f"Error loading URLs from file: {e}")
            sys.exit(1)

    if not urls:
        logger.error("No URLs provided to process")
        sys.exit(1)

    logger.info(f"Processing {len(urls)} URLs")
    for i, url in enumerate(urls[:5]):  # Log first 5 URLs
        logger.info(f"  {i+1}. {url}")
    if len(urls) > 5:
        logger.info(f"  ... and {len(urls) - 5} more URLs")

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
        logger.info("Starting pipeline execution...")
        result = orchestrator.run_pipeline(
            urls=urls,
            collection_name=args.collection_name,
            recreate_collection=args.recreate
        )

        logger.info("Pipeline execution completed")
        logger.info(f"Result: {result}")

        # Print summary
        if result.get('success'):
            print("\n" + "="*60)
            print("PIPELINE EXECUTION SUMMARY")
            print("="*60)
            print(f"Total URLs processed: {result.get('total_urls', 0)}")
            print(f"Successfully crawled: {result.get('crawled_count', 0)}")
            print(f"Chunks processed: {result.get('processed_count', 0)}")
            print(f"Embeddings generated: {result.get('embedded_count', 0)}")
            print(f"Execution time: {result.get('execution_time', 0):.2f} seconds")
            print(f"Collection name: {args.collection_name}")
            print("="*60)
            print("SUCCESS: Pipeline completed successfully!")
        else:
            print("\n" + "="*60)
            print("PIPELINE EXECUTION FAILED")
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