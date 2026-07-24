from django import forms
from django.contrib.auth.models import User

from .models import Product, Review, Store

ACCOUNT_TYPE_CHOICES = (
    ("Buyers", "Buyer"),
    ("Vendors", "Vendor"),
)


class RegisterForm(forms.Form):
    """Registration form used for both buyers and vendors (see account_type)."""

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, min_length=8)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES, widget=forms.RadioSelect)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ["name", "description", "logo"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock", "image"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"rating": forms.Select(choices=[(i, i) for i in range(1, 6)])}


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
