# rag/llm.py
import google.generativeai as genai

def generate_answer(question, context):
    model = genai.GenerativeModel('gemini-1.5-flash')  # or 'gemini-1.5-pro'
    prompt = f"""Answer the question based ONLY on the provided context.

Context:
{context}

Question: {question}

Answer:"""
    response = model.generate_content(prompt)
    return response.text