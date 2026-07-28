# rag/intent.py

def detect_tool(question: str) -> str | None:
    """
    Returns the tool name if the question matches, else None.
    """
    q = question.lower()

    # Product-related keywords
    product_keywords = ["product", "price", "stock", "inventory", "item", "material", "cement", "steel"]
    if any(kw in q for kw in product_keywords):
        return "products"

    # Customer-related keywords
    customer_keywords = ["customer", "client", "buyer", "purchaser", "contact"]
    if any(kw in q for kw in customer_keywords):
        return "customers"

    # Order-related keywords
    order_keywords = ["order", "purchase", "sale", "transaction", "delivery", "invoice"]
    if any(kw in q for kw in order_keywords):
        return "orders"

    # If no match, fallback to RAG
    return None