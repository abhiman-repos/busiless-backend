from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from accounts.models import Product , Order, Customer
from accounts.serializers import ProductSerializer, OrderSerializer, CustomerSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Customer, Order, OrderItem, Product


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'quality', 'stock']
    search_fields = ['name', 'description', 'category']

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user).order_by("-created_at")

    # 👇 Add this method
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Extract fields from request data
        customer_name = request.data.get('customer_name')
        contact_number = request.data.get('contact_number')
        delivery_address = request.data.get('delivery_address')
        payment_mode = request.data.get('payment_mode')
        product_id = request.data.get('product')
        quantity = request.data.get('quantity')

        # Validate required fields
        required_fields = [customer_name, contact_number, delivery_address, payment_mode, product_id, quantity]
        if not all(required_fields):
            return Response(
                {"error": "Missing required fields. Provide: customer_name, contact_number, delivery_address, payment_mode, product, quantity."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create the customer
        customer, created = Customer.objects.get_or_create(
            user=request.user,
            name=customer_name,
            phone=contact_number,
            defaults={'address': delivery_address}
        )
        # Update address if customer already exists and a new address is provided
        if not created and delivery_address:
            customer.address = delivery_address
            customer.save(update_fields=['address'])

        # Get the product (must belong to the user)
        try:
            product = Product.objects.get(id=product_id, user=request.user)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create the order (no delivery_address field anymore)
        order = Order.objects.create(
            user=request.user,
            customer=customer,
            delivery_address=delivery_address,
            payment_mode=payment_mode,
            status='pending'   # default status
        )

        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price
            # total will be auto-calculated by the model's save()
        )

        # Recalculate total price from all items
        order.total_price = sum(item.total for item in order.items.all())
        order.save()

        # Serialize and return the created order
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show customers belonging to the authenticated user
        return Customer.objects.filter(user=self.request.user).order_by('-created_at')

    # Optionally override create/update to automatically set user
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)