from typing import List
from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

EMBEDDING_MODEL = "gemini-embedding-001"


def embed_text(text: str) -> List[float]:
    """
    Embed a single document.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return response.embeddings[0].values


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple documents.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )

    return [embedding.values for embedding in response.embeddings]


def embed_query(text: str) -> List[float]:
    """
    Embed a search query.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return response.embeddings[0].values