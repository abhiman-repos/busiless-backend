# accounts/urls.py
from django.urls import path
from accounts.auth.views import profile, update_company
from accounts.auth.services import google_login
from accounts.views import Product, OrderViewSet

urlpatterns = [
    path("google-login/", google_login, name="google-login"),
    path("profile/", profile, name="profile"),
    path("profile/update/", update_company, name="profile-update"),
    path("company/update/", update_company, name="company-update"),
    path("products/", Product),
]