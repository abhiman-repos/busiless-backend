from rest_framework import serializers
from accounts.models import User, Company, Product, Order, OrderItem, Customer


class CustomerSerializer(serializers.ModelSerializer):
    # Optional: include the customer's orders
    orders = serializers.StringRelatedField(many=True, read_only=True)  # or use OrderSerializer

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'address', 'notes', 'orders', 'created_at']
        read_only_fields = ['id', 'created_at']
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "total"]
        
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "business_type",
            "services",
            "products",
            "business_name",
            "location",
            "owner_name",
            "support_email",
            "support_contact",
            "onboarding_completed",   # ← add this
            "created_at",
        ]
        read_only_fields = ["created_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)   # <-- must be present

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "company",
            "created_at",
        ]

class ProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "user", "name", "description", "category", "unit",
            "stock", "reorder_point", "price", "quality", "created_at"
        ]
        read_only_fields = ["id", "user", "created_at"]




class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "delivery_address",
            "total_price",
            "payment_mode",
            "status",
            "items",
            "created_at",
        ]
        read_only_fields = ["id", "user", "total_price", "created_at"]


