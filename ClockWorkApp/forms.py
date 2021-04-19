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
    current_goal = forms.IntegerField(widget=forms.NumberInput(attrs={'size':2}), min_value=0, max_value=168) # Minimum and maximum hours in a week

    class Meta:
        model = Profile
        fields = ["default_goal", "timezone", "day_start_time", "day_end_time"]
        widgets = {
                "default_goal":forms.NumberInput(attrs={'size':2})
                }

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance",None)
        if instance is not None and instance.latest_week:
            self.fields["current_goal"].initial = instance.latest_week.goal
        elif instance is not None:
            self.fields["current_goal"].initial = instance.default_goal
        else:
            self.fields["current_goal"].initial = 40

    def save(self, *args, **kwargs):
        profile = super(forms.ModelForm, self).save(*args, **kwargs)
        profile.latest_week.goal = self.cleaned_data["current_goal"]
        profile.latest_week.save(update_fields=["goal"])
        return profile

    def clean(self):
        cleaned_data = super().clean()
        day_start_time = cleaned_data.get("day_start_time")
        day_end_time = cleaned_data.get("day_end_time")

        if day_start_time >= day_end_time:
            raise ValidationError("End time must be later than start time")

class Timer_Form(forms.Form):
    work_time = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput())
    work_code = forms.IntegerField(initial=1, min_value=0, widget=forms.HiddenInput())

