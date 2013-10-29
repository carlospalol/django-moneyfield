from django.db import models
from moneyfield import MoneyField


class FixedCurrencyModel(models.Model):
    name = models.CharField(blank=True, max_length=100)
    price = MoneyField(decimal_places=2, max_digits=12, currency='EUR')


class FreeCurrencyModel(models.Model):
    name = models.CharField(blank=True, max_length=100)
    price = MoneyField(decimal_places=2, max_digits=12)


class ChoicesCurrencyModel(models.Model):
    CURRENCY_CHOICES = (
        ('EUR', 'EUR'),
        ('USD', 'USD'),
        ('CNY', 'CNY'),
    )
    CURRENCY_DEFAULT = 'USD'
    
    name = models.CharField(blank=True, max_length=100)
    price = MoneyField(decimal_places=2, max_digits=12, 
                       currency_choices=CURRENCY_CHOICES,
                       currency_default=CURRENCY_DEFAULT)


class SomeMoney(models.Model):
    field1 = models.CharField(blank=True, max_length=100)
    field2 = MoneyField(decimal_places=2, max_digits=12)
    field3 = models.CharField(blank=True, max_length=100)