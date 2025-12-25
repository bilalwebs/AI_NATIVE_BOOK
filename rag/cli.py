#!/usr/bin/env python3
"""
Command Line Interface for the RAG Pipeline
"""

import argparse
import sys
import logging
import os
from typing import List
from pathlib import Path


def setup_cli():
    """
    Set up the command line interface with all available commands.
    """
    parser = argparse.ArgumentParser(
        description="RAG Pipeline CLI: Crawl Docusaurus URLs, generate embeddings, and store in Qdrant Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single URL
  python cli.py run --urls https://example.com/docs

  # Process URLs from a file
  python cli.py run --url-file urls.txt

  # Validate the pipeline
  python cli.py validate

  # Check configuration
  python cli.py check-config
        """
    )

    # Global options
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run the RAG pipeline')
    run_parser.add_argument(
        '--urls',
        nargs='+',
        help='List of URLs to process (alternative to --url-file)'
    )
    run_parser.add_argument(
        '--url-file',
        type=str,
        help='Path to a text file containing URLs to process (one per line)'
    )
    run_parser.add_argument(
        '--collection-name',
        type=str,
        default='book_embeddings',
        help='Name of the Qdrant collection to store embeddings (default: book_embeddings)'
    )
    run_parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate the collection before storing (default: False)'
    )
    run_parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (default: .env)'
    )

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate pipeline functionality')
    validate_parser.add_argument(
        '--test-urls',
        nargs='+',
        help='Test URLs to validate the pipeline with'
    )
    validate_parser.add_argument(
        '--test-queries',
        nargs='+',
        help='Test queries to validate search functionality'
    )

    # Check-config command
    check_config_parser = subparsers.add_parser('check-config', help='Check configuration')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show pipeline information')

    return parser


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
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_pipeline(args):
    """
    Run the main pipeline with provided arguments.
    """
    from rag.pipeline import PipelineOrchestrator
    from rag.config.config import Config

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not args.urls and not args.url_file:
        logger.error("Either --urls or --url-file must be provided")
        return 1

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
            return 1

    if not urls:
        logger.error("No URLs provided to process")
        return 1

    logger.info(f"Processing {len(urls)} URLs")

    # Validate configuration
    try:
        Config().validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return 1

    # Create pipeline orchestrator
    try:
        orchestrator = PipelineOrchestrator()
        logger.info("Pipeline orchestrator created successfully")
    except Exception as e:
        logger.error(f"Failed to create pipeline orchestrator: {e}")
        return 1

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
            return 0
        else:
            print("\n" + "="*60)
            print("PIPELINE EXECUTION FAILED")
            print("="*60)
            print(f"Error: {result.get('message', 'Unknown error')}")
            print("="*60)
            return 1

    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        return 1


def validate_pipeline(args):
    """
    Validate the pipeline functionality.
    """
    from rag.validation import PipelineValidator

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Use default test queries if none provided
    test_queries = args.test_queries or [
        "What is the main concept discussed?",
        "Explain the key features",
        "How does this work?"
    ]

    # For now, we'll just show the validation framework
    # In a real implementation, we'd need actual test URLs
    print("\n" + "="*60)
    print("PIPELINE VALIDATION")
    print("="*60)
    print("Validation framework ready")
    print(f"Test queries: {len(test_queries)} provided")
    print("Note: Actual validation requires real URLs to process")
    print("="*60)

    # Create validator and run
    validator = PipelineValidator(logger=logger)
    results = validator.run_comprehensive_validation()

    return 0


def check_config(args):
    """
    Check the configuration.
    """
    from rag.config.config import Config

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        Config().validate()
        print("✓ Configuration is valid")
        print(f"  - Cohere API key: {'SET' if Config.COHERE_API_KEY else 'NOT SET'}")
        print(f"  - Qdrant URL: {'SET' if Config.QDRANT_URL else 'NOT SET'}")
        print(f"  - Qdrant API key: {'SET' if Config.QDRANT_API_KEY else 'NOT SET'}")
        print(f"  - Chunk size: {Config.CHUNK_SIZE}")
        print(f"  - Chunk overlap: {Config.CHUNK_OVERLAP}")
        return 0
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return 1


def show_info(args):
    """
    Show pipeline information.
    """
    from rag.pipeline import PipelineOrchestrator
    from rag.config.config import Config

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    print("\n" + "="*60)
    print("RAG PIPELINE INFORMATION")
    print("="*60)
    print("Component: Book Embeddings Storage Pipeline")
    print("Purpose: Crawl Docusaurus URLs, generate embeddings, store in Qdrant Cloud")
    print("Tech Stack:")
    print("  - Language: Python")
    print("  - Embeddings: Cohere")
    print("  - Vector DB: Qdrant Cloud")
    print("  - Data Source: Docusaurus book URLs")
    print("\nConfiguration:")
    print(f"  - Chunk size: {Config.CHUNK_SIZE}")
    print(f"  - Chunk overlap: {Config.CHUNK_OVERLAP}")
    print(f"  - Cohere model: {Config.COHERE_MODEL}")
    print("="*60)

    return 0


def main():
    """
    Main entry point for the CLI.
    """
    parser = setup_cli()
    args = parser.parse_args()

    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return 0

    # Execute the appropriate command
    if args.command == 'run':
        return run_pipeline(args)
    elif args.command == 'validate':
        return validate_pipeline(args)
    elif args.command == 'check-config':
        return check_config(args)
    elif args.command == 'info':
        return show_info(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())