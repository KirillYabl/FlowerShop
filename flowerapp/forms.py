from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from .models import Consultation


class ConsultationForm(forms.ModelForm):
    client_name = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Введите Имя'}),
        error_messages={
            'required': 'Поле "Имя" не должно быть пустым'
        }
    )
    phone = PhoneNumberField(
        region='RU',
        label='',
        widget=RegionalPhoneNumberWidget(attrs={'placeholder': '+ 7(999) 000-00-00'}),
        error_messages={
            'invalid': 'Поле "Телефон" должно быть в формате + 7(999) 000-00-00'
        }
    )

    class Meta:
        model = Consultation
        fields = ['client_name', 'phone']

    def __init__(self, *args, class_name, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if class_name:
                visible.field.widget.attrs['class'] = class_name


class CustomEventForm(forms.Form):
    event = forms.CharField(
        max_length=100,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Введите свой повод'}),
        error_messages={
            'required': 'Поле "Повод" не должно быть пустым'
        }
    )
    client_name = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Введите Имя'}),
        error_messages={
            'required': 'Поле "Имя" не должно быть пустым'
        }
    )
    phone = PhoneNumberField(
        region='RU',
        label='',
        widget=RegionalPhoneNumberWidget(attrs={'placeholder': '+ 7(999) 000-00-00'}),
        error_messages={
            'invalid': 'Поле "Телефон" должно быть в формате + 7(999) 000-00-00'
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'quiz__form_input'


class OrderForm(forms.Form):
    CHOICES = [
        ('1', 'Как можно скорее'),
        ('2', 'с 10:00 до 12:00'),
        ('3', 'с 12:00 до 14:00'),
        ('4', 'с 14:00 до 16:00'),
        ('5', 'с 16:00 до 18:00'),
        ('6', 'с 18:00 до 20:00')
    ]
    name = forms.CharField(max_length=200, label='', 
                            widget=forms.TextInput(attrs={
                                'name': 'fname',
                                'class': 'order__form_input',
                                'placeholder': 'Введите Имя'
                            }))
    phone = PhoneNumberField(region='RU', label='',
                             widget=RegionalPhoneNumberWidget(attrs={
                                'name': 'tel',
                                'class': 'order__form_input',
                                'placeholder': '+ 7(999) 000 00 00'
                            }))
    delivery_address = forms.CharField(max_length=200, label='', 
                            widget=forms.TextInput(attrs={
                                'name': 'adres',
                                'class': 'order__form_input',
                                'placeholder': 'Адрес доставки'
                            }))
    delivery_window = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'order__form_radio'}), choices=CHOICES)
