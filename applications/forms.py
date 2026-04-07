# applications/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import SocialApplication, Operator


class SocialApplicationForm(forms.ModelForm):
    class Meta:
        model = SocialApplication
        fields = ['last_name', 'first_name', 'patronymic', 'snils',
                  'service_type', 'description', 'passport_scan', 'snils_scan', 'additional_docs']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'}),
            'snils': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123-456-789 01'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Ежемесячная денежная выплата', 'Ежемесячная денежная выплата'),
                ('Пенсия по старости', 'Пенсия по старости'),
                ('Пенсия по инвалидности', 'Пенсия по инвалидности'),
                ('Материнский капитал', 'Материнский капитал'),
                ('Социальная доплата', 'Социальная доплата'),
                ('Другое', 'Другое'),
            ]),
            'passport_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),
            'snils_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),
            'additional_docs': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),
        }

    def clean_snils(self):
        snils = self.cleaned_data.get('snils')
        if snils:
            snils_clean = snils.replace(' ', '').replace('-', '')
            if not snils_clean.isdigit() or len(snils_clean) != 11:
                raise forms.ValidationError('СНИЛС должен содержать 11 цифр')
        return snils


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    patronymic = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Operator
        fields = ['username', 'email', 'first_name', 'last_name', 'patronymic', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'password1', 'password2']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserProfileForm(UserChangeForm):
    """Форма редактирования профиля"""
    password = None

    class Meta:
        model = Operator
        fields = ['username', 'email', 'first_name', 'last_name', 'patronymic', 'phone', 'date_of_birth', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }