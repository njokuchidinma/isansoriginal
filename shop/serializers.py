from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, CharField
from .models import  Barcode, Cart, Category, DeliveryCompany, Order, Product, Review, Wishlist
from users.models import CustomUser  # Assuming the custom user model

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class BarcodeSerializer(ModelSerializer):
    class Meta:
        model = Barcode
        fields = ['id', 'code', 'status']

class ProductSerializer(ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )
    barcode = serializers.PrimaryKeyRelatedField(
        queryset=Barcode.objects.filter(status='unused'),
        required=False,
        allow_null=True
    )
    sizes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price', 'description', 'category', 'sizes', 'barcode', 'quantity']

    def validate_sizes(self, value):
        """
        Validate and parse the sizes field.
        It should be a comma-separated string of valid size choices.
        """
        if not value:
            return ""  # Allow empty sizes

        sizes = [size.strip() for size in value.split(",") if size.strip()]
        valid_sizes = [choice[0] for choice in Product.SIZE_CHOICES]
        invalid_sizes = set(sizes) - set(valid_sizes)

        if invalid_sizes:
            raise serializers.ValidationError(
                f"The following sizes are invalid: {', '.join(invalid_sizes)}"
            )

        return ",".join(sizes)  # Return a clean comma-separated string

    def to_representation(self, instance):
        """
        Convert stored sizes (comma-separated string) to a list for the response.
        """
        ret = super().to_representation(instance)
        ret['sizes'] = instance.get_sizes_list()  # Convert to list
        return ret

    def to_internal_value(self, data):
        """
        Convert sizes field from list or comma-separated string to consistent format.
        """
        sizes = data.get('sizes', '')
        if isinstance(sizes, list):  # If frontend sends as a list
            sizes = ",".join(sizes)
        data['sizes'] = sizes.strip()
        return super().to_internal_value(data)

    def create(self, validated_data):
        sizes = validated_data.pop('sizes', '')
        barcode_data = validated_data.pop('barcode', None)

        # Create the product
        product = Product.objects.create(**validated_data)
        product.set_sizes(sizes.split(',') if sizes else [])

        # Handle barcode
        if barcode_data:
            try:
                barcode = Barcode.objects.get(pk=barcode_data.id, status='unused')
                barcode.status = 'used'
                barcode.save()
                product.barcode = barcode
                product.save()
            except Barcode.DoesNotExist:
                product.delete()
                raise serializers.ValidationError(
                    {"barcode": ["Barcode does not exist or is already in use."]}
                )
        return product

    def update(self, instance, validated_data):
        sizes = validated_data.pop('sizes', None)
        barcode_data = validated_data.pop('barcode', None)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if sizes is not None:
            instance.set_sizes(sizes.split(',') if sizes else [])

        # Handle barcode update
        if barcode_data:
            try:
                new_barcode = Barcode.objects.get(pk=barcode_data.id, status='unused')

                # If an old barcode exists, mark it as unused
                if instance.barcode:
                    old_barcode = instance.barcode
                    old_barcode.status = 'unused'
                    old_barcode.save()

                # Assign new barcode
                new_barcode.status = 'used'
                new_barcode.save()
                instance.barcode = new_barcode
            except Barcode.DoesNotExist:
                raise serializers.ValidationError(
                    {"barcode": ["Barcode does not exist or is already in use."]}
                )

        instance.save()
        return instance

class ProductInfoSerializer(ModelSerializer):
    class Meta:
        model = Product  # Assuming you have a Product model
        fields = ['id', 'name']  # Include the fields you want


class DeliveryCompanySerializer(ModelSerializer):
    class Meta:
        model = DeliveryCompany
        fields = ['id', 'name', 'contact_number', 'address', 'branch', 'state', 'website']
        read_only_fields = ['created_by']

class OrderSerializer(ModelSerializer):
    user = serializers.StringRelatedField()  # Representing user as their email
    delivery_company = DeliveryCompanySerializer(read_only=True)
    delivery_company_id = serializers.PrimaryKeyRelatedField(queryset=DeliveryCompany.objects.all(), write_only=True, source='delivery_company')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    product = ProductInfoSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_company', 'delivery_company_id', 'product', 'status', 'quantity','created_at', 'updated_at', 'total_price']

    def get_user(self, obj):
        """Return the user's email and shipping details."""
        user = obj.user
        return {
            "email": user.email,
            "phone_number": user.phone_number,
            "shipping_address": user.shipping_address,
            "country": user.country,
            "street_address": user.street_address,
            "city": user.city,
            "state": user.state,
            "zip_code": user.zip_code,
        }


class CartSerializer(ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')
    total_price = serializers.SerializerMethodField() 
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ['user']

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

class WishlistSerializer(ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id']

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data.get('product')

        existing_wishlist_item = Wishlist.objects.filter(user=user, product=product).first()
        if existing_wishlist_item:
            raise serializers.ValidationError({
                'product_id': 'Product already exists in your wishlist'
            })
        
        wishlist_item = Wishlist.objects.create(
            user=user,
            product=product
        )
        return wishlist_item

class ReviewSerializer(ModelSerializer):
    user_first_name = CharField(source='user.first_name', read_only=True)
    user_last_name = CharField(source='user.last_name', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_first_name', 'user_last_name','product', 'comment', 'rating', 'created_at']


class AdminOrderHistorySerializer(ModelSerializer):
    user_details = serializers.SerializerMethodField()
    product_details = serializers.SerializerMethodField()
    delivery_company = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'user_details', 
            'product_details', 
            'delivery_company', 
            'status', 
            'quantity', 
            'total_price',
            'created_at', 
            'updated_at'
        ]

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'phone_number': obj.user.phone_number,
            'shipping_address': {
                'street': obj.user.street_address,
                'city': obj.user.city,
                'state': obj.user.state,
                'zip_code': obj.user.zip_code,
                'country': obj.user.country
            }
        }

    def get_product_details(self, obj):
        return {
            'id': obj.product.id,
            'name': obj.product.name,
            'price': obj.product.price
        }
    
    def get_delivery_company(self, obj):
        if obj.delivery_company:
            return {
                'id': obj.delivery_company.id,
                'name': obj.delivery_company.name
            }
        return None

