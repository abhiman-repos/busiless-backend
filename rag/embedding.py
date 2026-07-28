# rag/embedding.py
from google import genai
from django.conf import settings
from typing import List, Union
import os

# Configure the Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Use the latest embedding model
# Options: "models/text-embedding-004" (recommended), "models/embedding-001"
EMBEDDING_MODEL = "models/text-embedding-004"

def embed_text(text: str) -> List[float]:
    """
    Embed a single text string using Gemini.
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document"  # good for RAG documents
    )
    return result['embedding']

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts in a single batch call (more efficient).
    Gemini supports up to 100 texts per batch.
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=texts,
        task_type="retrieval_document"
    )
    return result['embedding']

def embed_query(text: str) -> List[float]:
    """
    Embed a user query (use 'retrieval_query' task type for better results).
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']