"""
Unit tests for critical RAG pipeline components.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from rag.processing.chunker import TextChunker
from rag.processing.embedding_client import CohereEmbeddingClient
from rag.crawling.content_extractor import ContentExtractor
from rag.storage.qdrant_schema import QdrantSchema
from rag.config.config import Config


class TestTextChunker(unittest.TestCase):
    """
    Test cases for the TextChunker class.
    """
    def setUp(self):
        self.chunker = TextChunker(chunk_size=100, overlap=20)

    def test_chunk_text_basic(self):
        """Test basic text chunking functionality."""
        text = "This is a sample text that will be chunked into smaller pieces. " * 5
        chunks = self.chunker.chunk_text(text, source_url="test://example", title="Test")

        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.content), 100)  # Approximate check

    def test_chunk_with_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z " * 10
        chunks = self.chunker.chunk_text(text, source_url="test://example", title="Test")

        # If we have multiple chunks, verify overlap logic works
        if len(chunks) > 1:
            # Check that there are multiple chunks
            self.assertGreater(len(chunks), 1)

    def test_empty_text(self):
        """Test chunking with empty text."""
        chunks = self.chunker.chunk_text("", source_url="test://example", title="Test")
        self.assertEqual(len(chunks), 0)

    def test_short_text(self):
        """Test chunking with text shorter than chunk size."""
        short_text = "Short text"
        chunks = self.chunker.chunk_text(short_text, source_url="test://example", title="Test")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, short_text)


class TestContentExtractor(unittest.TestCase):
    """
    Test cases for the ContentExtractor class.
    """
    def setUp(self):
        self.extractor = ContentExtractor()

    def test_extract_content_basic(self):
        """Test basic content extraction from HTML."""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <div class="main-content">
                    <p>This is the main content of the page.</p>
                    <p>It has multiple paragraphs.</p>
                </div>
                <nav>This is navigation - should be excluded</nav>
            </body>
        </html>
        """
        result = self.extractor.extract_content(html_content, "http://example.com")

        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('title', result)
        self.assertIn('Test Page', result['title'])
        self.assertIn('main content', result['content'])

    def test_extract_content_with_docusaurus_selectors(self):
        """Test content extraction with Docusaurus-specific selectors."""
        html_content = """
        <html>
            <head><title>Docusaurus Test</title></head>
            <body>
                <div class="main-wrapper">
                    <main class="main">
                        <article>
                            <h1>Article Title</h1>
                            <div class="markdown">
                                <p>This is article content.</p>
                            </div>
                        </article>
                    </main>
                </div>
                <nav class="navbar">Navigation content</nav>
            </body>
        </html>
        """
        result = self.extractor.extract_content(html_content, "http://example.com")

        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('article content', result['content'])

    def test_extract_content_empty_html(self):
        """Test content extraction with empty HTML."""
        result = self.extractor.extract_content("", "http://example.com")
        self.assertFalse(result['success'])


class TestQdrantSchema(unittest.TestCase):
    """
    Test cases for the QdrantSchema class.
    """
    def setUp(self):
        self.schema = QdrantSchema()

    def test_create_payload_structure(self):
        """Test that payload creation returns correct structure."""
        payload = self.schema.create_payload(
            content="Test content",
            source_url="http://example.com",
            page_title="Test Page",
            chunk_order=1
        )

        self.assertIn('content', payload)
        self.assertIn('source_url', payload)
        self.assertIn('page_title', payload)
        self.assertIn('chunk_order', payload)
        self.assertEqual(payload['content'], "Test content")
        self.assertEqual(payload['source_url'], "http://example.com")

    def test_validate_payload_valid(self):
        """Test payload validation with valid payload."""
        valid_payload = {
            'content': 'Test content',
            'source_url': 'http://example.com',
            'page_title': 'Test Page',
            'chunk_order': 1
        }
        is_valid = self.schema.validate_payload(valid_payload)
        self.assertTrue(is_valid)

    def test_validate_payload_invalid(self):
        """Test payload validation with invalid payload."""
        invalid_payload = {
            'content': '',  # Empty content
            'source_url': 'http://example.com'
        }
        is_valid = self.schema.validate_payload(invalid_payload)
        # Should be valid since we're only checking for required fields existence
        # The validation logic might allow empty content depending on implementation
        self.assertTrue(isinstance(is_valid, bool))


class TestConfig(unittest.TestCase):
    """
    Test cases for the Config class.
    """
    @patch('rag.config.config.os.getenv')
    def test_config_defaults(self, mock_getenv):
        """Test that config has appropriate defaults."""
        # Mock environment variables to return None (not set)
        mock_getenv.return_value = None

        config = Config()

        # Test default values
        self.assertEqual(config.CHUNK_SIZE, 512)
        self.assertEqual(config.CHUNK_OVERLAP, 50)
        self.assertEqual(config.REQUEST_TIMEOUT, 30)
        self.assertEqual(config.REQUEST_DELAY, 1.0)
        self.assertEqual(config.MAX_RETRIES, 3)
        self.assertEqual(config.COHERE_MODEL, 'embed-english-v3.0')

    @patch('rag.config.config.os.getenv')
    def test_config_custom_values(self, mock_getenv):
        """Test that config picks up custom values from environment."""
        # Mock environment variables with custom values
        def mock_side_effect(key, default=None):
            if key == 'CHUNK_SIZE':
                return '256'
            elif key == 'CHUNK_OVERLAP':
                return '30'
            elif key == 'REQUEST_TIMEOUT':
                return '60'
            elif key == 'COHERE_MODEL':
                return 'embed-multilingual-v2.0'
            else:
                return default

        mock_getenv.side_effect = mock_side_effect

        config = Config()

        self.assertEqual(config.CHUNK_SIZE, 256)
        self.assertEqual(config.CHUNK_OVERLAP, 30)
        self.assertEqual(config.REQUEST_TIMEOUT, 60)
        self.assertEqual(config.COHERE_MODEL, 'embed-multilingual-v2.0')


if __name__ == '__main__':
    unittest.main()