# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification, UserPreferredDeliveryCompany

@admin.register(CustomUser )
class CustomUserAdmin(UserAdmin):
    model = CustomUser 

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {
            "fields": (
                "first_name", "last_name", "gender", "phone_number", 
                "location", "shipping_address", "country", 
                "street_address", "city", "state", "zip_code"
            )
        }),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Important dates", {"fields": ("date_joined",)}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )
    
    list_display = ("email", "first_name", "last_name", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_superuser", "is_active",)
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("date_joined",)

    def save_model(self, request, obj, form, change):
        if not change:
            # New user
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser
    


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_read', 'created_at')
    search_fields = ('user__email', 'message')

@admin.register(UserPreferredDeliveryCompany)
class UserPreferredDeliveryCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'delivery_company')
    search_fields = ('user__email', 'delivery_company__name')