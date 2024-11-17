from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UrlForm(forms.Form):
    url = forms.URLField(label='Enter the URLto check', max_length=200)

class RegisterForm(UserCreationForm):
    class Meta:
        model=User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=40, widget=forms.PasswordInput)