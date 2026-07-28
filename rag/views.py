from django.http import JsonResponse
import json
from rag.llm import generate_answer_with_gemini
from rag.embedding import embed_query
from rag.chroma_client import collection
from django.views.decorators.csrf import csrf_exempt
from .models import TrainingFile
from .tasks import process_uploaded_file
from rag.extractors import extract_text_from_file
from rag.utils import chunk_text
from rag.embedding import embed_texts



@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    user = request.user
    file_obj = request.FILES.get('file')
    description = request.POST.get('description', '')
    if not file_obj:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    tf = TrainingFile.objects.create(
        user=user,
        name=file_obj.name,
        description=description,
        file=file_obj,
        size=file_obj.size,
        type=file_obj.content_type,
        status='pending'
    )
    # Trigger background processing
    process_uploaded_file.delay(tf.id)
    return JsonResponse({'id': tf.id, 'status': 'pending', 'message': 'File uploaded and processing started.'})

@csrf_exempt
def upload_file_sync(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    user = request.user
    file_obj = request.FILES.get('file')
    description = request.POST.get('description', '')
    if not file_obj:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    tf = TrainingFile.objects.create(
        user=user,
        name=file_obj.name,
        description=description,
        file=file_obj,
        size=file_obj.size,
        type=file_obj.content_type,
        status='processing'
    )
    try:
        # Process synchronously (may take time)
        content = extract_text_from_file(tf.file.path)
        chunks = chunk_text(content)
        embeddings = embed_texts(chunks)
        ids = [f"{tf.id}_{i}" for i in range(len(chunks))]
        metadatas = [{"file_id": tf.id, "user_id": user.id, "chunk_index": i} for i in range(len(chunks))]
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
        tf.status = 'completed'
        tf.save()
        return JsonResponse({'id': tf.id, 'status': 'completed'})
    except Exception as e:
        tf.status = 'failed'
        tf.save()
        return JsonResponse({'error': str(e)}, status=500)

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


def ask_question(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    user = request.user
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Question cannot be empty'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Embed the question
    question_embedding = embed_query(question)
    
    # Retrieve relevant chunks from ChromaDB, filtered by user
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"user_id": user.id},
        include=["documents"]
    )
    
    if not results['documents'] or not results['documents'][0]:
        return JsonResponse({'answer': 'No relevant information found in your documents.'})
    
    chunks = results['documents'][0]
    context = "\n\n---\n\n".join(chunks)
    answer = generate_answer_with_gemini(question, context)
    
    return JsonResponse({'answer': answer, 'sources': chunks})  # optionally return source chunks