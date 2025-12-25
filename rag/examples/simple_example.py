"""
Simple example of using the RAG pipeline to process Docusaurus book URLs.
"""

from rag.pipeline import PipelineOrchestrator
from rag.config.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Example usage of the RAG pipeline.
    """
    print("RAG Pipeline Example")
    print("="*50)

    # Validate configuration
    try:
        Config().validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("Please set up your environment variables in a .env file")
        return

    # Create the pipeline orchestrator
    orchestrator = PipelineOrchestrator()

    # Example URLs (replace with actual Docusaurus book URLs)
    example_urls = [
        "https://docusaurus.io/docs/introduction",
        "https://docusaurus.io/docs/getting-started",
        "https://docusaurus.io/docs/configuration"
    ]

    print(f"Processing {len(example_urls)} URLs...")
    for url in example_urls:
        print(f"  - {url}")

    # Run the pipeline
    result = orchestrator.run_pipeline(
        urls=example_urls,
        collection_name="example_embeddings",
        recreate_collection=True  # Set to False to append to existing collection
    )

    # Print results
    print("\nPipeline Results:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Total URLs: {result.get('total_urls', 0)}")
    print(f"  Crawled: {result.get('crawled_count', 0)}")
    print(f"  Processed: {result.get('processed_count', 0)}")
    print(f"  Embedded: {result.get('embedded_count', 0)}")
    print(f"  Execution Time: {result.get('execution_time', 0):.2f}s")

    if result.get('success'):
        print("\n✓ Pipeline executed successfully!")
        print("Embeddings are now stored in Qdrant Cloud and ready for search.")
    else:
        print(f"\n✗ Pipeline failed: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    main()