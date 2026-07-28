from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    # Remove user_id if you want to use the built-in `id` field.
    # Otherwise keep it, but ensure it’s not null/blank.
    user_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,    # set to False if it's mandatory
        blank=True,
    )
    email = models.EmailField(unique=True, max_length=255)  # use EmailField
    created_at = models.DateTimeField(auto_now_add=True)

    # Removed onboarding_completed from here

    def __str__(self):
        return self.email


class Company(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company",
    )
    business_type = models.CharField(max_length=50)
    business_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    services = models.TextField()
    products = models.TextField(blank=True)
    location = models.TextField()
    support_email = models.EmailField()
    support_contact = models.CharField(max_length=20)
    onboarding_completed = models.BooleanField(default=False)  # moved here
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name
    

class Product(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)           # e.g., kg, pcs, litres
    stock = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quality = models.CharField(
        max_length=20,
        choices=[("Good", "Good"), ("Average", "Average"), ("Poor", "Poor")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,          # protect against deleting a customer who has orders
        related_name="orders",
        null=True,                         # allow null temporarily during migration
        blank=True
    )
    # Remove these three fields:
    # client_name = models.CharField(...)
    # contact_number = models.CharField(...)
    # delivery_address = models.TextField()
    payment_mode = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Customer(models.Model):
    # Each customer belongs to a business user (the owner of the shop)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customers'
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)   # extra info
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'phone')   # optional: prevent duplicates per business

    def __str__(self):
        return f"{self.name} ({self.phone})"