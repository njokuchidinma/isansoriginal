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
    sizes = serializers.MultipleChoiceField(
        choices=Product.SIZE_CHOICES,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'price', 'description', 'category', 'sizes', 'barcode', 'quantity']

    def to_representation(self, instance):
        """
        Convert stored comma-separated sizes to a list
        """
        ret = super().to_representation(instance)
        ret['sizes'] = instance.get_sizes_list()
        return ret

    def to_internal_value(self, data):
        """
        Handle sizes conversion
        """
        # If sizes is a string, convert to list
        if isinstance(data.get('sizes'), str):
            data['sizes'] = data['sizes'].split(',')
        return super().to_internal_value(data)

    def create(self, validated_data):
        #Extract sizes
        sizes =  validated_data.pop('sizes', [])
        # Handle barcode
        barcode_data = validated_data.pop('barcode', None)
        
        # Create product first
        product = Product.objects.create(**validated_data)
        
        # Set sizes if provided
        if sizes:
            product.set_sizes(sizes)
        else:
            product.sizes = None

        # Update barcode if provided
        if barcode_data:
            try:
                # Get the barcode and update its status
                barcode = Barcode.objects.get(
                    pk=barcode_data.id, 
                    status='unused'
                )
                barcode.status = 'used'
                barcode.save()
                
                # Assign barcode to product
                product.barcode = barcode
                product.save()
            except Barcode.DoesNotExist:
                # Rollback product creation if barcode is invalid
                product.delete()
                raise serializers.ValidationError({
                    "barcode": ["Barcode does not exist or is already in use."]
                })
        product.save()
        return product

    def update(self, instance, validated_data):
        #Extract sizes
        sizes = validated_data.pop('sizes', None)
        # Handle barcode update
        barcode_data = validated_data.pop('barcode', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update sizes if provided
        if sizes is not None:
            if sizes:
                instance.sizes = ','.join(sizes)
            else:
                instance.sizes = None
        
        # If a new barcode is being assigned
        if barcode_data:
            try:
                # Get the new barcode
                new_barcode = Barcode.objects.get(
                    pk=barcode_data.id, 
                    status='unused'
                )
                
                # If product already has a barcode, mark it as unused
                if instance.barcode:
                    old_barcode = instance.barcode
                    old_barcode.status = 'unused'
                    old_barcode.save()
                
                # Update new barcode status
                new_barcode.status = 'used'
                new_barcode.save()
                
                # Assign new barcode
                instance.barcode = new_barcode
            except Barcode.DoesNotExist:
                raise serializers.ValidationError({
                    "barcode": ["Barcode does not exist or is already in use."]
                })
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
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
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_first_name', 'product', 'comment', 'rating', 'created_at']


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

