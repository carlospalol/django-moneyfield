from django.db import models
from moneyfield import MoneyField


CURRENCY_CHOICES = (
    ('EUR', 'EUR'),
    ('USD', 'USD'),
    ('CNY', 'CNY'),
)
CURRENCY_DEFAULT = 'USD'


class Book(models.Model):
    price = MoneyField(decimal_places=2, max_digits=8, currency='EUR')


class Translator(models.Model):
    fee = MoneyField(decimal_places=2, max_digits=8)


class Transaction(models.Model):
    value = MoneyField(decimal_places=2, max_digits=12,
                       currency_choices=CURRENCY_CHOICES,
                       currency_default=CURRENCY_DEFAULT)