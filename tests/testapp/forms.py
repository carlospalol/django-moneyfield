from django import forms
from testapp.models import Transaction


class TransactionModelForm(forms.ModelForm):
    class Meta:
        model = Transaction