# rag/llm.py

from google import genai
import os
import json

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


def generate_answer_with_gemini(
    question: str,
    context: str = None,
    custom_prompt: str = None,
    tools_data: dict = None,
):
    """
    Generate an answer using Gemini.

    Parameters
    ----------
    question : User's question
    context : RAG context from ChromaDB
    custom_prompt : Optional complete prompt
    tools_data : Live data from backend APIs
                 Example:
                 {
                     "products": [...],
                     "customers": [...],
                     "orders": [...]
                 }
    """

    if custom_prompt:
        prompt = custom_prompt

    else:
        prompt = """
You are GoCyn AI Customer Success Assistant.

You answer using:

1. Retrieved knowledge (RAG)
2. Live business data (Tools)

Rules:
- Use the provided tool data whenever available.
- Use the context when relevant.
- Never invent data.
- If information is unavailable, clearly say so.
- Format lists as bullet points.
"""

        if context:
            prompt += f"\n\n## Knowledge Base\n{context}"

        if tools_data:
            prompt += (
                "\n\n## Live Business Data\n"
                + json.dumps(tools_data, indent=2)
            )

        prompt += f"""

## User Question

{question}

## Answer
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        return response.text.strip()

    except Exception as e:
        print(e)
        return "Sorry, I encountered an error while generating the answer."