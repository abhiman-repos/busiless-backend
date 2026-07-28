import requests
from accounts.views import OrderViewSet


BASE_URL = "http://127.0.0.1:8000"


def get_products(request):
    """
    Call the products API using the user's authentication.
    """
    token = request.auth

    response = requests.get(
        f"{BASE_URL}/api/business/products/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    if response.status_code == 200:
        return response.json()

    return []

def create_order(token, product_id, quantity):

    response = requests.post(
        f"{BASE_URL}/api/business/orders/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product": product_id,
            "quantity": quantity
        }
    )

    return response.json()

TOOL_REGISTRY = {
    "products": get_products,
    "orders": OrderViewSet,
}