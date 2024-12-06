from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import os


class Category(models.Model):
    name = models.CharField(max_length=100)

class Product(models.Model):
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('FS', 'Free Size'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sizes = models.CharField(max_length=100, choices=SIZE_CHOICES, null=False, blank=True, help_text="Comma-separated sizes (XS,S,M,L,XL)")  # e.g., "S, M, L, XL"
    barcode = models.OneToOneField('Barcode', on_delete=models.SET_NULL, null=True, blank=True, related_name="product",)
    quantity = models.PositiveIntegerField(default=0)  # Total stock
    is_in_stock = models.BooleanField(default=True)  # Stock status

    def clean(self):
        # Validate sizes
        if self.sizes:
            size_list = self.sizes.split(',')
            valid_sizes = [choice[0] for choice in self.SIZE_CHOICES]
            invalid_sizes = set(size_list) - set(valid_sizes)
            
            if invalid_sizes:
                raise ValidationError({
                    'sizes': f'Invalid sizes: {invalid_sizes}'
                })

    def get_sizes_list(self):
        """
        Convert sizes string to a list
        """
        return self.sizes.split(',') if self.sizes else []

    def set_sizes(self, sizes_list):
        """
        Set sizes from a list
        """
        # Validate sizes
        valid_sizes = [choice[0] for choice in self.SIZE_CHOICES]
        invalid_sizes = set(sizes_list) - set(valid_sizes)
        
        if invalid_sizes:
            raise ValueError(f"Invalid sizes: {invalid_sizes}")
        
        self.sizes = ','.join(sizes_list)

    def save(self, *args, **kwargs):
        self.full_clean()
        # Automatically update stock status based on quantity
        self.is_in_stock = self.quantity > 0
        super().save(*args, **kwargs)



class Barcode(models.Model):
    STATUS_CHOICES = [
        ('unused', 'Unused'),
        ('used', 'Used'),
    ]
    code = models.CharField(max_length=13, unique=True)  # EAN-13 codes are 13 digits
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default='unused')
    

    def __str__(self):
        return self.code


class DeliveryCompany(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=350)
    branch = models.CharField(max_length=150)
    state = models.CharField(max_length=150)
    website = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_companies")

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    delivery_company = models.ForeignKey(DeliveryCompany, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('packaged', 'Packaged'),
        ('sent_out', 'Sent Out for Delivery'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.email} - Status: {self.status}"
    
    def total_price(self):
        if self.product and self.product.price:
            return self.quantity * self.product.price
        return 0

class Cart(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='carts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='carts')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.firstname}'s cart - {self.product.name}"

class Wishlist(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlists')

class Review(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    comment = models.TextField()
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product} by {self.user}"
