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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'consultation__form_input'
