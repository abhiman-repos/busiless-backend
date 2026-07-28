from django.conf import JsonResponse
import json

from rag.embedding import embed_query
from rag.chroma_client import collection

def query_training(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    user = request.user
    data = json.loads(request.body)
    question = data.get('question')

    # 1. Embed the question with retrieval_query task type
    question_embedding = embed_query(question)

    # 2. Query ChromaDB (filtered by user_id)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"user_id": user.id},
        include=["documents", "metadatas"]
    )

    # 3. Build context and generate answer
    chunks = results['documents'][0]
    context = "\n".join(chunks)
    answer = generate_answer_with_gemini(question, context)  # you can use Gemini for this too!
    return JsonResponse({'answer': answer})