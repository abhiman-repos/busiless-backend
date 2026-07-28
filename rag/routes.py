# rag/router.py

def determine_tools(question):
    q = question.lower()

    tools = []

    if any(word in q for word in [
        "product",
        "products",
        "price",
        "cost",
        "stock",
        "inventory",
        "item"
    ]):
        tools.append("products")

    return tools

def detect_intent(question):
    q = question.lower()

    if any(word in q for word in [
        "order",
        "buy",
        "purchase",
        "place order",
        "need",
        "book"
    ]):
        return "order"

    if any(word in q for word in [
        "product",
        "price",
        "stock",
        "inventory"
    ]):
        return "products"

    return "rag"

def route_question(question):

    q = question.lower()

    if any(word in q for word in [
        "order",
        "buy",
        "purchase",
        "need",
        "book",
        "place order"
    ]):
        return {
            "intent": "order",
            "tools": ["products", "orders"],
            "use_rag": False
        }

    if any(word in q for word in [
        "product",
        "products",
        "price",
        "cost",
        "stock",
        "inventory"
    ]):
        return {
            "intent": "products",
            "tools": ["products"],
            "use_rag": False
        }

    return {
        "intent": "rag",
        "tools": [],
        "use_rag": True
    }