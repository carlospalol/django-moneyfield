from django.db import models
from moneyfield import MoneyField


class Book(models.Model):
    name = models.CharField(max_length=100)
    price = MoneyField(decimal_places=2, max_digits=8, currency='EUR')

class Translator(models.Model):
    name = models.CharField(max_length=100)
    fee = MoneyField(decimal_places=2, max_digits=8)
