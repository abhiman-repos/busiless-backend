import chromadb
from chromadb.config import Settings
from django.conf import settings

# Persistent client – stores data in a local directory
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_DB_PATH,  # e.g., './chroma_db'
    settings=Settings(anonymized_telemetry=False)
)

# Get or create collection for your training data
collection = chroma_client.get_or_create_collection(
    name="training_docs",
    metadata={"hnsw:space": "cosine"}
)