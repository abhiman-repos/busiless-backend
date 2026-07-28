# rag/api_tool_handler.py

import requests
import json
from django.conf import settings
from .llm import generate_answer_with_gemini
from rag.api_tool_handler import TOOLS

def call_tool_and_answer(question: str, tool_name: str, request) -> str:
    """
    Call the specified API tool, fetch JSON, and let Gemini answer the question.
    """
    # Get the tool config
    tool = TOOLS.get(tool_name)
    if not tool:
        return "Sorry, I don't have a tool for that."

    # Build full URL
    base_url = settings.BASE_API_URL  # e.g., http://localhost:8000
    url = base_url + tool["path"]

    # Get the user's token from the request (assuming it's in request.headers)
    # We need to forward the Authorization header.
    headers = {
        "Authorization": request.headers.get("Authorization", ""),
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch data from {tool_name}: {str(e)}"

    # Convert data to a readable text for the prompt
    # For a list of objects, we can pretty-print it.
    data_text = json.dumps(data, indent=2)

    # Build a prompt that asks Gemini to answer the question based on the data.
    prompt = f"""
You are an AI assistant that answers questions based solely on the following business data.

Data (in JSON format):
{data_text}

Question:
{question}

Instructions:
- Answer the question using only the data provided.
- If the answer is not in the data, say "I don't have enough information about that."
- Be concise and natural.

Answer:
"""
    # Use Gemini to generate the final answer
    answer = generate_answer_with_gemini(question, prompt)  # but we need to modify the function to accept custom prompt

    return answer