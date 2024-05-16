from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError



class EmailAuthBackend():
    def authenticate(self, request, email, password):
        
        try:
            user = User.objects.get(email=email)
            print("user", user)
            # if email is registered then verify the password is correct or not
            success = user.check_password(password)
            # if password is correct then returned user to UserLogin function in views.py of login app directory
            if success:
                print("Entered in success")
                return user
            else:
                print("Entered in else")
                messages.error(request, ('Incorrect Password, please try again.'))	
                return None
            
        except User.DoesNotExist:
            messages.error(request, ('Incorrect Email Address, please try again.'))
        return None

    def get_user(self,uid):
        
        try:
            return User.objects.get(pk=uid)
        except:
            return None
        

class EmailValidationOnForgotPassword(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            
            raise ValidationError(f"There is no user registered with the {email} - email address!")

        return email