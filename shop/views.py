from barcode import Code128
from barcode.writer import ImageWriter
from datetime import timedelta
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from django.core.files import File
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework import status
from users.models import CustomUser
from .barcodegen import generate_barcode_images
from .models import Barcode, Cart, Category, DeliveryCompany, Order, Product, Review, Wishlist
from .serializers import BarcodeSerializer, CartSerializer, CategorySerializer, DeliveryCompanySerializer, OrderSerializer, AdminOrderHistorySerializer, ProductSerializer, ReviewSerializer, WishlistSerializer
import os
import requests 

class CategoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            return Response({"detail": "Category deleted."}, status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
    
        
class GetCategory(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
        

        
class ProductView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Prepare data
        data = request.data.copy()
        
        # Handle barcode
        if 'barcode' in data and isinstance(data['barcode'], dict):
            barcode_code = data['barcode'].get('code')
            try:
                # Find an unused barcode by code
                barcode = Barcode.objects.get(
                    code=barcode_code, 
                    status='unused'
                )
                data['barcode'] = barcode.id
            except Barcode.DoesNotExist:
                return Response(
                    {"barcode": ["Barcode does not exist or is already in use."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate and save
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                ProductSerializer(product).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            
            # Prepare data
            data = request.data.copy()
            
            # Handle barcode
            if 'barcode' in data and isinstance(data['barcode'], dict):
                barcode_code = data['barcode'].get('code')
                try:
                    # Find an unused barcode by code
                    barcode = Barcode.objects.get(
                        code=barcode_code, 
                        status='unused'
                    )
                    data['barcode'] = barcode.id
                except Barcode.DoesNotExist:
                    return Response(
                        {"barcode": ["Barcode does not exist or is already in use."]}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate and update
            serializer = ProductSerializer(product, data=data, partial=True)
            if serializer.is_valid():
                product = serializer.save()
                return Response(ProductSerializer(product).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

class GetProducts(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class GenerateBarcode(APIView):
    permission_classes = [IsAdminUser ]

    def post(self, request):
        start = request.data.get("start", 1000)  # Default start value
        count = request.data.get("count", 50)  # Default count value

        if not isinstance(start, int) or not isinstance(count, int) or start < 0 or count <= 0:
            return Response({"detail": "Start and count must be positive integers."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            generate_barcode_images(start=start, count=count)
            return Response({"detail": f"Generated {count} barcodes starting from {start}."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BarcodeView(APIView):
    permission_classes = [IsAdminUser ]

    def get(self, request):
        barcodes = Barcode.objects.all()  # Retrieve all barcodes
        serializer = BarcodeSerializer(barcodes, many=True)  # Serialize the queryset
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        try:
            # Get barcode value from request
            barcode_value = request.data.get("code")
            if not barcode_value:
                return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)
            if Barcode.objects.filter(code=barcode_value).exists():
                return Response({"detail": "Barcode already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Save to database with status 'unused'
            barcode = Barcode(code=barcode_value)
            barcode.save()
            return Response(BarcodeSerializer(barcode).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminDeliveryCompany(APIView):
    permission_classes = [IsAdminUser]  # Admin-only access

    def get(self, request):
        # Admin can view all delivery companies
        companies = DeliveryCompany.objects.all()
        serializer = DeliveryCompanySerializer(companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Admin can create a new delivery company
        serializer = DeliveryCompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        # Admin can edit any delivery company
        try:
            company = DeliveryCompany.objects.get(pk=pk)
        except DeliveryCompany.DoesNotExist:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        # Allow admin to edit the company
        serializer = DeliveryCompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeliveryCompany(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get delivery companies that were created by admins
        admin_companies = DeliveryCompany.objects.filter(created_by__isnull=True)  # Admin-created companies
        user_companies = DeliveryCompany.objects.filter(created_by=request.user)  # User-created companies
        all_companies = admin_companies | user_companies  # Combine both sets

        # Serialize the companies and return them
        serializer = DeliveryCompanySerializer(all_companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Create a new delivery company for the user
        serializer = DeliveryCompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # Assign user as creator
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            company = DeliveryCompany.objects.get(pk=pk, created_by=request.user)
        except DeliveryCompany.DoesNotExist:
            return Response({"detail": "Company not found or you do not have permission to edit this company."}, 
                            status=status.HTTP_404_NOT_FOUND)

        serializer = DeliveryCompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderStatus(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            status_before = order.status
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if status_before != serializer.data.get('status'):
                    # Notify user of status change
                    send_mail(
                        subject="Order Status Updated",
                        message=f"Your order status is now: {serializer.data['status']}.",
                        from_email="admin@fashionstore.com",
                        recipient_list=[order.user.email],
                    )
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all cart items for the user."""
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to the cart."""
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """Update quantity for a specific cart item."""
        try:
            cart_item = Cart.objects.get(pk=pk, user=request.user)
            serializer = CartSerializer(cart_item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """Remove a specific cart item."""
        try:
            cart_item = Cart.objects.get(pk=pk, user=request.user)
            cart_item.delete()
            return Response({"detail": "Cart item removed."}, status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Place orders from the cart."""

        delivery_company_id = request.data.get('delivery_company_id')

        try:
            # Fetch the delivery company instance first
            delivery_company = DeliveryCompany.objects.get(id=delivery_company_id)
        except DeliveryCompany.DoesNotExist:
            return Response({"detail": "Invalid delivery company"}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        orders = []
        for cart_item in cart_items:
            product = cart_item.product

            if product.quantity < cart_item.quantity:
                return Response(
                    {"detail": f"Insufficient stock for {product.name}. Available: {product.quantity}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Deduct the product quantity
            product.quantity -= cart_item.quantity
            product.save()

            # Create the order
            order = Order.objects.create(
                user=request.user,
                product=product,
                quantity=cart_item.quantity,
                delivery_company=delivery_company
            )
            orders.append(order)
            cart_item.delete()  # Remove item from cart after placing the order.

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve all wishlist items for the authenticated user
        """
        try:
            wishlist = Wishlist.objects.filter(user=request.user)
            
            # Check if wishlist is empty
            if not wishlist.exists():
                return Response({
                    'message': 'Your wishlist is empty',
                    'wishlist_items': []
                }, status=status.HTTP_200_OK)
            
            serializer = WishlistSerializer(wishlist, many=True)
            
            return Response({
                'total_items': wishlist.count(),
                'wishlist_items': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': 'An unexpected error occurred while fetching wishlist',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Add a new item to the wishlist
        """
        try:
            # Validate product exists and is not already in wishlist
            product_id = request.data.get('product')
            
            if not product_id:
                return Response({
                    'error': 'Product ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if product exists
            product = get_object_or_404(Product, id=product_id)
            
            # Check if product is already in wishlist
            existing_wishlist_item = Wishlist.objects.filter(
                user=request.user, 
                product=product
            ).first()
            
            if existing_wishlist_item:
                return Response({
                    'error': 'Product already exists in your wishlist',
                    'wishlist_item_id': existing_wishlist_item.id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new wishlist item
            serializer = WishlistSerializer(data={
                'product': product_id
            })
            
            if serializer.is_valid():
                wishlist_item = serializer.save(user=request.user)
                
                return Response({
                    'message': 'Product added to wishlist successfully',
                    'wishlist_item': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found',
                'product_id': product_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': 'An unexpected error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        Remove a specific item from the wishlist
        """
        try:
            # Retrieve and delete wishlist item
            wishlist_item = get_object_or_404(
                Wishlist, 
                pk=pk, 
                user=request.user
            )
            
            # Store product details before deletion for response
            product_details = {
                'id': wishlist_item.product.id,
                'name': wishlist_item.product.name
            }
            
            # Delete the wishlist item
            wishlist_item.delete()
            
            return Response({
                'message': 'Wishlist item deleted successfully',
                'deleted_item': {
                    'wishlist_item_id': pk,
                    'product': product_details
                }
            }, status=status.HTTP_200_OK)
        
        except Wishlist.DoesNotExist:
            return Response({
                'error': 'Wishlist item not found',
                'wishlist_item_id': pk
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': 'An unexpected error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReview(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            reviews = Review.objects.filter(product_id=product_id)

            if not reviews.exists():
                return Response({
                    'message': 'No reviews found for this product',
                    'product_id': product_id
                }, status=status.HTTP_404_NOT_FOUND)
            serializer = ReviewSerializer(reviews, many=True)
            return Response({
                'product_id': product_id,
                'total_reviews': reviews.count(),
                'reviews': serializer.data
            }, status=status.HTTP_200_OK)  
     
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found',
                'product_id': product_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': 'An unexpected error occurred',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        review_data = {**request.data, 'product': product_id, 'user': request.user.id}

        serializer = ReviewSerializer(data=review_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 

class Metrics(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Total number of orders
        total_orders = Order.objects.count()

        # Top 3 most ordered products
        top_products = (
            Order.objects.values("product__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:3]
        )

        # Total number of registered customers
        total_customers = CustomUser.objects.filter(is_staff=False).count()

        # Total number of products in a category
        category_products = Product.objects.values("category__name").annotate(total=Count("id"))

        # Prepare the response data
        data = {
            "total_orders": total_orders,
            "top_products": [{"product": p["product__name"], "total_quantity": p["total_quantity"]} for p in top_products],
            "total_customers": total_customers,
            "category_products": [{"category": c["category__name"], "total_products": c["total"]} for c in category_products],
        }
        return Response(data)


class PaymentInit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get order details from the request
        amount = request.data.get("amount")  # Ensure amount is in kobo (multiply by 100 for NGN)
        email = request.user.email

        # Paystack API endpoint
        url = "https://api.paystack.co/transaction/initialize"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "callback_url": "https://your-frontend-url.com/payment-success",  # Frontend callback
        }

        # Make the request
        response = requests.post(url, json=data, headers=headers)

        # Return the response to the frontend
        if response.status_code == 200:
            return Response(response.json(), status=200)
        return Response(response.json(), status=response.status_code)
    

class PaymentVerify(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the transaction reference from the request
        reference = request.data.get("reference")

        # Paystack API endpoint
        url = f"https://api.paystack.co/transaction/verify/{reference}"

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }

        # Make the request
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data["status"] and data["data"]["status"] == "success":
                # Payment successful
                return Response({"message": "Payment verified successfully!"}, status=200)

        # Payment failed
        return Response({"message": "Payment verification failed."}, status=400)
    

class OrderHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve order history for the authenticated user."""
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class UpdateProductQuantity(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, product_id):
        """Update the quantity of a specific product."""
        try:
            product = Product.objects.get(id=product_id)
            quantity = request.data.get('quantity')

            if quantity is not None and isinstance(quantity, int) and quantity >= 0:
                product.quantity_available = quantity
                product.save()
                return Response({"detail": "Product quantity updated successfully."})
            return Response({"detail": "Invalid quantity provided."}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminOrderHistory(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Retrieve all order history for admin
        """
        # Optimize query with select_related to reduce database hits
        queryset = Order.objects.select_related(
            'user', 'product', 'delivery_company'
        ).all().order_by('-created_at')

        # Serialize data
        serializer = AdminOrderHistorySerializer(queryset, many=True)

        # Return all orders
        return Response(serializer.data)

class AdminOrderStatistics(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Provide comprehensive order statistics for admin dashboard
        """

        # Total order statistics
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(
            total_revenue=Sum(ExpressionWrapper(F('quantity') * F('product__price'), output_field=DecimalField())))

        # Order status breakdown
        status_breakdown = Order.objects.values('status').annotate(
            count=Count('id')
        )

        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)

        recent_orders = {
            'today': Order.objects.filter(created_at__date=today).count(),
            'last_week': Order.objects.filter(
                created_at__date__gte=last_week
            ).count(),
            'last_month': Order.objects.filter(
                created_at__date__gte=last_month
            ).count()
        }

        # Top selling products
        top_products = Order.objects.values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(ExpressionWrapper( F('quantity') * F('product__price'), output_field=DecimalField()))
        ).order_by('-total_quantity')[:10]

        return Response({
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'status_breakdown': list(status_breakdown),
            'recent_order_trends': recent_orders,
            'top_products': list(top_products)
        })