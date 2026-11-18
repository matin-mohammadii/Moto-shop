
from django import forms
from .models import Order
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator


class OrderForm(forms.ModelForm):

    quantity = forms.IntegerField(min_value=1)

    class Meta:
        model = Order
        fields = ['customer_name', 'phone', 'quantity']


class RegisterForm(UserCreationForm):

    username = forms.CharField(
        label='شماره موبایل',
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{10,15}$',
                message='شماره موبایل معتبر وارد کنید.'
            )
        ]
    )

    first_name = forms.CharField(
        label='نام و نام خانوادگی',
        max_length=150
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'username',
            'password1',
            'password2'
        ]


class ProfileForm(forms.ModelForm):

    first_name = forms.CharField(
        label='نام و نام خانوادگی',
        max_length=150,
        required=False
    )

    username = forms.CharField(
        label='شماره موبایل',
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{10,15}$',
                message='شماره موبایل معتبر وارد کنید.'
            )
        ]
    )

    class Meta:
        model = User
        fields = ['first_name', 'username']

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')

        if not first_name.strip():
            raise forms.ValidationError(
                'لطفاً نام و نام خانوادگی خود را وارد کنید.'
            )

        return first_name.strip()
