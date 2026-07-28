import json
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import TrainingFile
from .chroma_client import collection
from .tasks import process_uploaded_file  # if Celery used
from .embedding import embed_query
from .llm import generate_answer_with_gemini
from rag.routes import determine_tools, detect_intent
from rag.tools import get_products

# ---------- LIST FILES ----------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_files(request):
    user = request.user
    files = TrainingFile.objects.filter(user=user).order_by('-created_at')
    data = [{
        'id': f.id,
        'name': f.name,
        'description': f.description,
        'size': f.size,
        'type': f.type,
        'status': f.status,
        'created_at': f.created_at.isoformat(),
    } for f in files]
    return Response(data)

# ---------- UPLOAD ----------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    user = request.user
    file_obj = request.FILES.get('file')
    description = request.data.get('description', '')
    if not file_obj:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    tf = TrainingFile.objects.create(
        user=user,
        name=file_obj.name,
        description=description,
        file=file_obj,
        size=file_obj.size,
        type=file_obj.content_type,
        status='pending'
    )
    # Process in background (Celery)
    process_uploaded_file(tf.id)
    return Response({'id': tf.id, 'status': 'pending', 'message': 'File uploaded and processing started.'})

# ---------- DELETE ----------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    user = request.user
    try:
        tf = TrainingFile.objects.get(id=file_id, user=user)
    except TrainingFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

    # Delete from ChromaDB
    try:
        collection.delete(where={"file_id": file_id, "user_id": user.id})
    except Exception as e:
        print(f"ChromaDB deletion error: {e}")

    tf.file.delete()
    tf.delete()
    return Response({'success': True, 'message': 'File deleted.'})

# ---------- QUERY ----------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask_question(request):
    user = request.user

    question = request.data.get("question", "").strip()

    if not question:
        return Response(
            {"error": "Question cannot be empty"},
            status=400
        )

    #########################################################
    # RAG
    #########################################################
    
    intent = detect_intent(question)

    if intent == "order":

        # Get available products
        products = get_products(request)

        # Send products + question to Gemini
        answer = generate_answer_with_gemini(
            question=question,
            tools_data={
                "products": products
            }
        )

        return Response({
            "answer": answer,
            "products": products
        })

    question_embedding = embed_query(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"user_id": str(user.id)},
        include=["documents"]
    )

    context = ""

    if results["documents"] and results["documents"][0]:
        context = "\n\n---\n\n".join(results["documents"][0])

    #########################################################
    # TOOLS
    #########################################################

    tool_data = {}

    tools = determine_tools(question)

    if "products" in tools:
        tool_data["products"] = get_products(request)


    #########################################################
    # GEMINI
    #########################################################

    answer = generate_answer_with_gemini(
    question=question,
    context=context,
    tools_data=tool_data
)

    

    return Response(
        {
            "answer": answer,
            "sources": results["documents"][0] if results["documents"] else [],
            "tools": tool_data
        }
    )

# ---------- TRAIN ----------f
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_training(request):
    user = request.user
    pending_files = TrainingFile.objects.filter(user=user, status='pending')
    if not pending_files.exists():
        return Response({'message': 'No pending files to train.', 'count': 0})

    for tf in pending_files:
        process_uploaded_file(tf.id)

    return Response({'message': f'Training started for {pending_files.count()} file(s).', 'count': pending_files.count()})

# ---------- STATUS ----------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_status(request):
    user = request.user
    files = TrainingFile.objects.filter(user=user)
    if not files.exists():
        return Response({
            'all_completed': True,
            'total': 0,
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
        })

    status_counts = {
        'pending': files.filter(status='pending').count(),
        'processing': files.filter(status='processing').count(),
        'completed': files.filter(status='completed').count(),
        'failed': files.filter(status='failed').count(),
    }
    all_completed = (status_counts['pending'] == 0 and status_counts['processing'] == 0)
    return Response({
        'all_completed': all_completed,
        'total': files.count(),
        **status_counts,
    })