from django.db import models
from moneyfield import MoneyField


class Book(models.Model):
    price = MoneyField(decimal_places=2, max_digits=8, currency='EUR')

class Translator(models.Model):
    fee = MoneyField(decimal_places=2, max_digits=8)
