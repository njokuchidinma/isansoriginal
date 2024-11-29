from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            print(f"User found: {user}")  # Debug
            if user.check_password(password):
                print("Password is correct")  # Debug
                return user
            else:
                print("Password is incorrect")  # Debug
        except UserModel.DoesNotExist:
            print("No user found with this email address")  # Debug
        return None
