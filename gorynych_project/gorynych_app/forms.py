from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class UserRegForm(UserCreationForm):
    username = forms.CharField(label="Ваше имя", widget=forms.TextInput)
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Пароль еще раз", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Ваше имя", widget=forms.TextInput)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
