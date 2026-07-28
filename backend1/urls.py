# urls.py (project root)
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import ProductViewSet,OrderViewSet, CustomerViewSet

router = DefaultRouter()
router.register(r'business/products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'customer', CustomerViewSet, basename='customer')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),   # google-login, profile, etc.
    path('api/', include(router.urls)), 
    path('api/', include(router.urls)),
    path('api/', include(router.urls)),               # /api/business/products/ (CRUD)
    path('api/training/', include('rag.urls')),
]