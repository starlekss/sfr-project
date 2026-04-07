from django import forms
from .models import SocialApplication


class SocialApplicationForm(forms.ModelForm):
    class Meta:
        model = SocialApplication
        fields = ['last_name', 'first_name', 'patronymic', 'snils',
                  'service_type', 'description', 'passport_scan', 'snils_scan', 'additional_docs']
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Опишите вашу ситуацию подробно...'}),
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
        # Простая валидация СНИЛС
        if snils:
            # Удаляем пробелы и дефисы
            snils_clean = snils.replace(' ', '').replace('-', '')
            if not snils_clean.isdigit() or len(snils_clean) != 11:
                raise forms.ValidationError('СНИЛС должен содержать 11 цифр')
        return snils