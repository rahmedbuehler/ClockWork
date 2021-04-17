from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.text import capfirst
from .models import *

class User_Creation_Form(UserCreationForm):
        
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super(User_Creation_Form, self).__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["username"].widget.attrs["placeholder"] = "Username*"
        self.fields["email"].widget.attrs["placeholder"] = "Email"
        self.fields["password1"].widget.attrs["placeholder"] = "Password*"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password*"

class Authentication_Form(AuthenticationForm):
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["password"].widget.attrs["placeholder"] = "Password"

        # Set the label for the "username" field.
        UserModel = get_user_model()
        self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)
 
class Settings_Form(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ["default_goal", "timezone", "day_start_time", "day_end_time"]
        widgets = {
                "default_goal":forms.NumberInput(attrs={'placeholder':"Default Weekly Goal"}),
                "timezone":forms.Select(attrs={'placeholder':"Timezone"}),
                "day_start_time":forms.Select(attrs={'placeholder':"Daily Start Time"}),
                "day_end_time":forms.Select(attrs={'placeholder':"Daily End Time"})
                }
