from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from .models import CustomUser
from .serializers import CustomUserSerializer, ChangePasswordSerializer, ForgotPasswordSerializer
from .utils import generate_random_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken



class UserRegistration(APIView):
    """ Endpoint for user registration """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """ Register a new user """
        serializer = CustomUserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Prepare the welcome email
            try:
                send_mail(
                    'Welcome to iSans Original',
                    f'Dear {user.email},\n\n'
                    'Thank you for signing up with iSans Original.\n\n'
                    'We are thrilled to have you on board! Explore our platform to enjoy the latest in fashion and exclusive offers.\n\n'
                    'If you have any questions or need assistance, please reach out to us at support@isansoriginal.com or through the support chat on your dashboard.\n\n'
                    'Best regards,\n'
                    'The iSans Original Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
            except Exception as e:
                return Response({
                    "data": "User  created successfully, but email could not be sent.",
                    "error": str(e),
                    "id": str(user.id),
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_201_CREATED)

            # Return the serialized data along with additional info
            return Response({
                "data": "User  created successfully",
                "id": str(user.id),
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)

        return Response({
            "data": "User  registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
            

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Attempt to retrieve the user by email
        try:
            user = CustomUser .objects.get(email=email)
        except CustomUser .DoesNotExist:
            return Response(
                {"error": "User  not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Authenticate the user with email and password
        if user.check_password(password):
            # Generate refresh and access tokens
            refresh = RefreshToken.for_user(user)

            serializer = CustomUserSerializer(user)


            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    
class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Attempt to retrieve the user by email
        try:
            user = CustomUser .objects.get(email=email)
        except CustomUser .DoesNotExist:
            return Response(
                {"error": "User  not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        
        # Check if the user is an admin
        if not user.is_staff:
            return Response(
                {"error": "Access denied. Admin privileges required."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Authenticate the user with email and password
        if user.check_password(password):
            # Generate refresh and access tokens
            refresh = RefreshToken.for_user(user)


            return Response({
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get the refresh token from the request body
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Attempt to blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ForgotPasswordView(APIView):
    queryset = CustomUser .objects.all()
    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        users = CustomUser .objects.filter(email=email)  # Use 'email' instead of 'email_address'

        if users.exists():
            user = users.first()
            new_password = generate_random_password() 
            try:
                # Send password reset email
                send_mail(
                    'Password Reset for iSans Original',
                    f'Dear {user.first_name},\n\n'  # Personalizing with first name
                    'We have received a request to reset your password for iSans Original.\n\n'
                    f'Your new password is: {new_password}\n\n'
                    'Please use this password to log in to your account. We recommend that you change your password to something more secure as soon as possible.\n\n'
                    'If you have any questions or concerns, please contact us at support@isansoriginal.com.\n\n'
                    'Best regards,\n'
                    'The iSans Original Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                # Set and save the new password
                user.set_password(new_password)
                user.save()
                return Response({"message": "New password sent to your email"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": "Failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"error": "Email not found"}, status=status.HTTP_400_BAD_REQUEST)

class ChangePassword(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully"}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfile(APIView):
    """ THIS ENDPOINT IS USED TO GET/UPDATE USER INFO ON THE SERVER """

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request):
        userSerializer = self.serializer_class(request.user).data
        return Response({"data":userSerializer},status=status.HTTP_200_OK)
    

    def put(self,request):
        user = request.user
        serializer = self.serializer_class(user,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"data":"ok"},status=status.HTTP_200_OK)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
