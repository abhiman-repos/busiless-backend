from rest_framework import viewsets, permissions
from accounts.models import Product , Order, Customer
from accounts.serializers import ProductSerializer, OrderSerializer, CustomerSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter


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
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        items_data = request.data.pop("items", [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            order = serializer.save(user=request.user)
            total = 0
            for item in items_data:
                product_id = item.get("product")
                product = Product.objects.filter(id=product_id, user=request.user).first()
                unit_price = product.price if product else item.get("unit_price", 0)
                item_obj = OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=item.get("product_name", ""),
                    quantity=item.get("quantity", 1),
                    unit_price=unit_price
                )
                total += item_obj.total
            order.total_price = total
            order.save()

        output_serializer = self.get_serializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show customers belonging to the authenticated user
        return Customer.objects.filter(user=self.request.user).order_by('-created_at')

    # Optionally override create/update to automatically set user
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)