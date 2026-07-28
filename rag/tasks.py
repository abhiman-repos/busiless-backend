# rag/tasks.py
from celery import shared_task
from .embedding import embed_texts
from rag.chroma_client import collection
from .models import TrainingFile
from google import genai
from rag.extractors import extract_text_from_file
from rag.utils import chunk_text
from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

EMBEDDING_MODEL = "gemini-embedding-001"


def embed_texts_in_batches(
    texts: list[str],
    batch_size: int = 100,
) -> list[list[float]]:
    """
    Generate embeddings for a list of texts in batches.
    Returns a list of embedding vectors.
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
        )

        all_embeddings.extend(
            embedding.values for embedding in response.embeddings
        )

    return all_embeddings

def process_file(training_file_id):
    tf = TrainingFile.objects.get(id=training_file_id)
    try:
        # 1. Extract text and create chunks (as before)
        content = extract_text_from_file(tf.file.path)  # your custom extractor
        chunks = chunk_text(content, chunk_size=500)

        # 2. Generate ALL embeddings in ONE batch (much faster)
        embeddings = embed_texts(chunks)  # list of lists

        # 3. Prepare ChromaDB data
        ids = [f"{tf.id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "file_id": tf.id,
                "user_id": tf.user.id,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        # 4. Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )

        tf.status = 'completed'
        tf.save()
    except Exception as e:
        tf.status = 'failed'
        tf.save()
        raise e
    
    
@shared_task
def process_uploaded_file(file_id):
    tf = TrainingFile.objects.get(id=file_id)
    try:
        content = extract_text_from_file(tf.file.path)
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        embeddings = embed_texts(chunks)  # batched with Gemini
        ids = [f"{tf.id}_{i}" for i in range(len(chunks))]
        metadatas = [{"file_id": tf.id, "user_id": tf.user.id, "chunk_index": i} for i in range(len(chunks))]
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )
        tf.status = 'completed'
        tf.save()
    except Exception as e:
        tf.status = 'failed'
        tf.save()
        raise e