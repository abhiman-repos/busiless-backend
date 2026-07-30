import requests


BASE_URL = "http://127.0.0.1:8000"


def get_products(request):
    """
    Fetch products from the business API and return only
    the fields the user should see: id, name, price, status.
    """
    token = request.auth

    # Handle both string tokens and Token objects
    if hasattr(token, "key"):
        token = token.key

    try:
        response = requests.get(
            f"{BASE_URL}/api/business/products/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    data = response.json()

    # Handle both paginated and plain list responses
    products = data.get("results", data) if isinstance(data, dict) else data

    if not isinstance(products, list):
        return []

    cleaned = []
    for p in products:
        cleaned.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "status": p.get("status"),   # e.g. "available", "out_of_stock"
        })

    return cleaned

def create_order(request, customer_name, product_id, quantity, delivery_address, payment_mode, contact_number):
    response = requests.post(
        f"{BASE_URL}/api/orders/",
        headers={"Authorization": f"Bearer {request.auth}"},
        json={
            "customer_name": customer_name,
            "product": product_id,
            "quantity": quantity,
            "delivery_address": delivery_address,
            "payment_mode": payment_mode,
            "contact_number": contact_number,
        },
    )
    response.raise_for_status()
    return response.json()