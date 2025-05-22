from django import forms

from database.models import User

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField()
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('', '-- 請選擇 --'),
        ('customer', '顧客'),
        ('deliverer', '外送員'),
        ('vendor', '餐廳業者')] ,required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'role']

class UserLoginForm(forms.Form):
    email = forms.EmailField(required = True)
    password = forms.CharField(widget=forms.PasswordInput)