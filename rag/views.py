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
from rag.tools import get_products, create_order
from django.core.cache import cache
import logging

from .order_agent import (
    new_session, save_answer, next_question,
    completed, summary, ORDER_STEPS, QUESTIONS
)
from .tools import get_products, create_order


logger = logging.getLogger(__name__)




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
        return Response({"error": "Question cannot be empty"}, status=400)

    cache_key = f"order_session_{user.id}"

    # -------------------------------------------------------
    # 1. Check if we have an active order session
    # -------------------------------------------------------
    session = cache.get(cache_key)

    if session:
        # User is in the middle of an order conversation
        if completed(session):
            # Confirmation step
            if question.lower() in ["yes", "y"]:
                # Place the order
                try:
                    products = get_products(request)
                    product_name = session["data"].get("product_name", "")
                    product = next(
                        (p for p in products if p["name"].lower() == product_name.lower()),
                        None
                    )
                    if not product:
                        cache.delete(cache_key)
                        return Response({
                            "answer": f"Sorry, product '{product_name}' not found. Please start a new order.",
                            "session_active": False,
                        })

                    order = create_order(
                        request=request,
                        customer_name=session["data"]["customer_name"],
                        product_id=product["id"],
                        quantity=int(session["data"]["quantity"]),
                        delivery_address=session["data"]["delivery_address"],
                        payment_mode=session["data"]["payment_mode"],
                        contact_number=session["data"].get("contact_number", ""),
                    )
                    cache.delete(cache_key)
                    return Response({
                        "answer": f"✅ Order placed successfully.\n\nOrder ID: {order['id']}",
                        "session_active": False,
                    })
                except Exception as e:
                    logger.error(f"Order creation failed: {e}")
                    return Response({
                        "error": "Order creation failed. Please try again.",
                        "session_active": True,
                    }, status=500)

            elif question.lower() in ["no", "n", "cancel"]:
                cache.delete(cache_key)
                return Response({
                    "answer": "Order cancelled.",
                    "session_active": False,
                })
            
            else:
                # Invalid response – ask for confirmation again
                return Response({
                    "answer": summary(session) + "\n\nPlease reply with YES to place the order, or NO to cancel.",
                    "session_active": True,
                    "needs_confirmation": True,
                })
                
        else:
                # Not completed – save the user's answer and move to next step
            try:
                session = save_answer(session, question)
                cache.set(cache_key, session, timeout=1800)
                next_q = next_question(session)
                return Response({
                    "answer": next_q,
                    "session_active": True,
                })
            except ValueError as e:
                # Validation failed – ask the same question again
                current_step = session["step"]
                field = ORDER_STEPS[current_step]
                error_msg = str(e)
                return Response({
                    "answer": f"❌ {error_msg}\n\n{QUESTIONS[field]}",
                    "session_active": True,
                })

    # -------------------------------------------------------
    # 2. No active session – check if user wants to start an order
    # -------------------------------------------------------
    order_keywords = ["order", "buy", "purchase", "place order", "new order", "i want"]
    if any(kw in question.lower() for kw in order_keywords):
        session = new_session()
        cache.set(cache_key, session, timeout=1800)
        first_question = next_question(session)
        return Response({
            "answer": first_question,
            "session_active": True,
        })

    # -------------------------------------------------------
    # 3. Fallback: RAG + live tools
    # -------------------------------------------------------
    intent = detect_intent(question)
    if intent == "order":
        products = get_products(request)
        answer = generate_answer_with_gemini(
            question=question,
            tools_data={"products": products}
        )
        return Response({"answer": answer, "products": products})

    # Embed and query ChromaDB
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

    tool_data = {}
    tools = determine_tools(question)
    if "products" in tools:
        tool_data["products"] = get_products(request)

    answer = generate_answer_with_gemini(
        question=question,
        context=context,
        tools_data=tool_data
    )

    return Response({
        "answer": answer,
        "sources": results["documents"][0] if results["documents"] else [],
        "tools": tool_data,
        "session_active": False,
    })
    # -------------------------------------------------
    # 2. No active session – check if user wants to order
    # -------------------------------------------------
    order_keywords = ["order", "buy", "purchase", "place order", "new order"]
    if any(kw in question.lower() for kw in order_keywords):
        session = new_session()
        cache.set(cache_key, session, timeout=1800)
        first_question = next_question(session)
        return Response({
            "answer": first_question,
            "session_active": True,
        })

    # -------------------------------------------------
    # 3. Fallback: RAG + Live Tools (no order flow)
    # -------------------------------------------------
    # (the existing logic with intent detection, embedding, tools, etc.)
    # ...

    # For brevity, we keep the existing RAG & tools code here.
    # Make sure to handle 'intent' and 'determine_tools' as before.

    # Example:
    intent = detect_intent(question)
    if intent == "order":
        products = get_products(request)
        answer = generate_answer_with_gemini(
            question=question,
            tools_data={"products": products}
        )
        return Response({"answer": answer, "products": products})

    # Embed and query ChromaDB
    question_embedding = embed_query(question)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where={"user_id": str(user.id)},
        include=["documents"]
    )
    context = "\n\n---\n\n".join(results["documents"][0]) if results["documents"] and results["documents"][0] else ""

    # Tools data (products, customers, etc.)
    tool_data = {}
    tools = determine_tools(question)
    if "products" in tools:
        tool_data["products"] = get_products(request)

    # Generate final answer with Gemini
    answer = generate_answer_with_gemini(
        question=question,
        context=context,
        tools_data=tool_data
    )

    return Response({
        "answer": answer,
        "sources": results["documents"][0] if results["documents"] else [],
        "tools": tool_data,
        "session_active": False,
    })

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