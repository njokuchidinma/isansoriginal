# users/serializers.py
from rest_framework.serializers import ModelSerializer, EmailField, CharField
from rest_framework.exceptions import ValidationError
from .models import CustomUser  

class CustomUserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser  
        fields = (
            'id', 'first_name', 'last_name', 'email', 'password', 
            'gender', 'phone_number', 'location', 'shipping_address', 
            'country', 'street_address', 'city', 'state', 'zip_code', 
            'date_joined', 'is_active', 'is_staff'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'date_joined': {'read_only': True},  # Make date_joined read-only
            'is_active': {'read_only': True},    # Make is_active read-only
            'is_staff': {'read_only': True},      # Make is_staff read-only
        }
    
    def create(self, validated_data):
        # Use the manager's create_user method to handle password hashing
        user = CustomUser .objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            gender=validated_data.get('gender'),
            phone_number=validated_data.get('phone_number'),
            location=validated_data.get('location'),
            shipping_address=validated_data.get('shipping_address'),
            country=validated_data.get('country'),
            street_address=validated_data.get('street_address'),
            city=validated_data.get('city'),
            state=validated_data.get('state'),
            zip_code=validated_data.get('zip_code'),
        )
        return user

    def update(self, instance, validated_data):
        # Update the password if provided
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

class ForgotPasswordSerializer(ModelSerializer):
    email = EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email']


class ChangePasswordSerializer(ModelSerializer):
    old_password = CharField(required=True, write_only=True)
    new_password = CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['old_password', 'new_password']

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("Old password is incorrect.")
        return value

    def update(self, instance, validated_data):
        new_password = validated_data['new_password']
        instance.plain_password = new_password  
        instance.set_password(new_password) 
        instance.save()
        return instance