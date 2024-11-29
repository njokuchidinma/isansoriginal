from django.contrib import admin
from .models import Category, Product, Barcode, DeliveryCompany, Order

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'barcode', 'sizes')
    list_filter = ('category', 'price',)
    search_fields = ('name', 'description',)
    autocomplete_fields = ('category', 'barcode')
    readonly_fields = ('barcode',)
    fieldsets = (
        (None, {
            'fields': ('name', 'image', 'price', 'description', 'category', 'sizes', 'barcode')
        }),
    )

@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'status')
    search_fields = ('code',)
    readonly_fields = ('status',)

@admin.register(DeliveryCompany)
class DeliveryCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact_number', 'branch', 'state')
    search_fields = ('name', 'branch', 'state',)
    list_filter = ('state',)
    fieldsets = (
        (None, {
            'fields': ('name', 'contact_number', 'address', 'branch', 'state', 'website')
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'delivery_company', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at',)
    search_fields = ('user__email', 'delivery_company__name',)
    readonly_fields = ('created_at', 'updated_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'delivery_company', 'status', 'created_at', 'updated_at')
        }),
    )
