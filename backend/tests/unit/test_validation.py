import pytest
from src.services.validation_service import validation_service
from src.services.generation_service import generation_service


def test_selected_text_context_isolation_basic():
    """
    Test that selected-text mode responses are properly isolated from broader book context.
    
    This test verifies that when a user provides specific text and asks a question,
    the response is generated based only on that provided text, not from any broader knowledge.
    """
    # Sample selected text that contains information about a specific concept
    selected_text = """
    The transformer architecture is a deep learning architecture introduced in the paper 
    'Attention Is All You Need'. It relies heavily on attention mechanisms instead of 
    recurrent neural networks. The architecture consists of an encoder and decoder, 
    each composed of multiple layers with attention and feed-forward components.
    """
    
    # Question specifically about the concept mentioned in the selected text
    query = "What does the transformer architecture rely on instead of recurrent neural networks?"
    
    # Generate a response in selected-text mode
    response_data = {
        "query": query,
        "context_chunks": [{
            "id": "selected-text-test",
            "payload": {
                "content": selected_text,
                "source_chapter": "Test Chapter",
                "source_section": "Test Section"
            }
        }],
        "mode": "selected-text"
    }
    
    # Use the generation service to generate a response
    result = generation_service.generate_answer(
        query=response_data["query"],
        context_chunks=response_data["context_chunks"],
        mode=response_data["mode"]
    )
    
    # Validate the response using the validation service
    validation_result = validation_service.validate_selected_text_mode(
        query,
        selected_text,
        result["response"]
    )
    
    # The validation should confirm that the response follows context isolation policy
    assert validation_result["follows_policy"] is True
    assert "attention mechanisms" in result["response"].lower()


def test_selected_text_insufficient_context_response():
    """
    Test that the system properly responds when selected text is insufficient to answer a question.
    """
    # Very limited selected text that doesn't contain information to answer the question
    selected_text = "This section introduces the chapter."
    
    # Question that cannot be answered with the provided text
    query = "What are the main technical challenges with the transformer model?"
    
    # Generate a response in selected-text mode
    response_data = {
        "query": query,
        "context_chunks": [{
            "id": "insufficient-text-test",
            "payload": {
                "content": selected_text,
                "source_chapter": "Test Chapter",
                "source_section": "Test Section"
            }
        }],
        "mode": "selected-text"
    }
    
    result = generation_service.generate_answer(
        query=response_data["query"],
        context_chunks=response_data["context_chunks"],
        mode=response_data["mode"]
    )
    
    # The response should indicate that the answer is not available in the selected text
    assert "answer is not available in the selected text" in result["response"].lower()


def test_selected_text_mode_no_external_knowledge():
    """
    Test that selected-text mode doesn't incorporate any external knowledge beyond the provided text.
    """
    # Selected text about a specific, narrow topic
    selected_text = """
    Rhodium is a chemical element with symbol Rh and atomic number 45.
    It is a rare, silvery-white, hard, corrosion-resistant transition metal.
    It is also chemically inert. It was discovered in 1803 by William Hyde Wollaston.
    """
    
    # Question that could potentially trigger external knowledge about related elements
    query = "How is rhodium similar to platinum?"
    
    response_data = {
        "query": query,
        "context_chunks": [{
            "id": "rhodium-text-test",
            "payload": {
                "content": selected_text,
                "source_chapter": "Chemistry Chapter",
                "source_section": "Element Properties"
            }
        }],
        "mode": "selected-text"
    }
    
    result = generation_service.generate_answer(
        query=response_data["query"],
        context_chunks=response_data["context_chunks"],
        mode=response_data["mode"]
    )
    
    # Validate the response doesn't contain information not in the selected text
    validation_result = validation_service.validate_selected_text_mode(
        query,
        selected_text,
        result["response"]
    )
    
    # The validation should confirm that the response follows context isolation policy
    assert validation_result["follows_policy"] is True
    
    # The response should either indicate insufficient context or only use information from selected text
    # If it mentions platinum specifically, that would be concerning since it's not in the selected text


def test_book_wide_mode_proper_retrieval_usage():
    """
    Test that book-wide mode properly uses retrieved context for responses.
    """
    # Simulated retrieved context
    context_chunks = [
        {
            "id": "chunk-1",
            "payload": {
                "content": "The transformer architecture is a deep learning architecture that relies heavily on attention mechanisms. It was introduced in the 'Attention Is All You Need' paper and revolutionized NLP.",
                "source_chapter": "Chapter 3",
                "source_section": "3.2 Transformer Architecture"
            }
        },
        {
            "id": "chunk-2", 
            "payload": {
                "content": "The key innovation of transformers is the self-attention mechanism that allows the model to weigh the importance of different words in the input sequence.",
                "source_chapter": "Chapter 3", 
                "source_section": "3.3 Attention Mechanisms"
            }
        }
    ]
    
    query = "What is the key innovation of transformers?"
    
    response_data = generation_service.generate_answer(
        query=query,
        context_chunks=context_chunks,
        mode="book-wide"
    )
    
    # Validate that the response properly utilizes the retrieved context
    validation_result = validation_service.validate_book_wide_mode(
        query,
        response_data["response"],
        context_chunks
    )
    
    assert validation_result["follows_policy"] is True
    assert validation_result["alignment_ratio"] > 0.6  # At least 60% of response should be supported by retrieved context


def test_context_alignment_verification():
    """
    Test the core context alignment verification functionality.
    """
    # Sample response and context
    response = "The transformer architecture relies on attention mechanisms rather than recurrent networks."
    context_chunks = [
        {
            "id": "test-chunk",
            "payload": {
                "content": "Transformers use attention mechanisms instead of recurrent neural networks. This was the key insight from the Attention Is All You Need paper.",
                "source_chapter": "Chapter 3",
                "source_section": "3.2 Architecture Overview"
            }
        }
    ]
    
    validation_result = validation_service.validate_response_context_alignment(
        response,
        context_chunks
    )
    
    # The response should be well aligned with the provided context
    assert validation_result["is_aligned"] is True
    assert validation_result["alignment_score"] > 0.7