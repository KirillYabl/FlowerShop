from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import RegionalPhoneNumberWidget

from .models import Consultation


class ConsultationForm(forms.ModelForm):
    client_name = forms.CharField(max_length=200, label='',
                                  widget=forms.TextInput(attrs={'placeholder': 'Введите Имя'}))
    phone = PhoneNumberField(region='RU', label='',
                             widget=RegionalPhoneNumberWidget(attrs={'placeholder': '+ 7(999) 000 00 00'}))

    class Meta:
        model = Consultation
        fields = ['client_name', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'consultation__form_input'


class OrderForm(forms.Form):
    CHOICES = [
        ('1', 'Как можно скорее'),
        ('2', 'с 10:00 до 12:00'),
        ('3', 'с 12:00 до 14:00'),
        ('4', 'с 14:00 до 16:00'),
        ('5', 'с 16:00 до 18:00'),
        ('6', 'с 18:00 до 20:00')
    ]
    title = forms.CharField(max_length=200)
    name = forms.CharField(max_length=200, label='', 
                            widget=forms.TextInput(attrs={'placeholder': 'Введите Имя'}))
    phone = PhoneNumberField(region='RU', label='',
                             widget=RegionalPhoneNumberWidget(attrs={'placeholder': '+ 7(999) 000 00 00'}))
    delivery_address = forms.CharField(max_length=200, label='', 
                            widget=forms.TextInput(attrs={'placeholder': 'Адрес доставки'}))
    delivery_window = forms.ChoiceField(widget=forms.RadioSelect(), choices=CHOICES)
