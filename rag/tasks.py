# rag/tasks.py
from .embedding import embed_texts
from rag.chroma_client import collection
from .models import TrainingFile
import google.generativeai as genai
from rag.extractors import extract_text_from_file


def embed_texts_in_batches(texts, batch_size=100):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        result = genai.embed_content(
            model="gemini-embedding-2",
            content=batch,
            task_type="retrieval_document"
        )
        all_embeddings.extend(result['embedding'])
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