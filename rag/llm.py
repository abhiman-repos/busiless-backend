# rag/llm.py
from google import genai

def generate_answer_with_gemini(question: str, context: str) -> str:
    """
    Generate an answer using Gemini, based on the provided context.
    """
    # Choose a model – Gemini 1.5 Flash is fast and cheap
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.
If the answer is not present in the context, say "I don't have enough information about that."

Context:
{context}

Question: {question}

Answer:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Log the error and return a user-friendly message
        print(f"Gemini API error: {e}")
        return "Sorry, I encountered an error while generating the answer. Please try again later."