from django import forms


class Login(forms.Form):
    username = forms.CharField(
        label='', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'consultation__form_input',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'consultation__form_input',
            'placeholder': 'Введите пароль'
        })
    )
