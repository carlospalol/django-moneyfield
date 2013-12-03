

==================
Django Money Field
==================


Django model field for monetary amounts.


Installation
============

::

    pip install django-moneyfield

Moneyfield requires:

+ Python ==3.3
+ Django ==1.5 (still working on 1.6 compatibility)
+ `Money <https://pypi.python.org/pypi/money>`_
+ `Babel <https://pypi.python.org/pypi/Babel>`_ (if you need currency formatting)

Basic usage
===========

.. code:: python
    
    from django.db import Models
    from moneyfield import MoneyField
    
    class Book(models.Model):
        name = models.CharField(blank=True, max_length=100)
        price = MoneyField(decimal_places=2, max_digits=8)

The field ``price`` will be created in the database as two columns: ``price_amount``, and ``price_currency``. You may use any name ``<fieldname>``, resulting in columns ``<fieldname>_amount`` and ``<fieldname>_currency``.

.. code:: sql

    CREATE TABLE "myapp_book" (
        "id" integer NOT NULL PRIMARY KEY,
        "name" varchar(100) NOT NULL,
        "price_amount" decimal NOT NULL,
        "price_currency" varchar(3) NOT NULL
    );

The attribute ``price`` is only a convenience python descriptor that accepts and returns Money objects, and will be available only when working with a model instance.

.. code:: python

    >>> book = Book.objects.get(id=1)
    >>> book.price
    USD 19.99
    >>> book.price = Money("9.99", "USD")
    >>> book.save()
    >>> book.price
    USD 9.99

For any operation using Managers and QuerySets, the amount and the currency must be addressed separately, using ``price_amount`` and ``price_currency`` in this case. This allows for maximum flexibility and unambiguity.

.. code:: python

    new_book = Book.objects.create(
        name="The new book",
        price_amount=Decimal("29.99"),
        price_currency="USD"
    )
    
    books_in_usd = Book.objects.filter(price_currency="USD")
    
    cheap_books = Book.objects.filter(price_amount__lt=Decimal('2'))
    
    cheap_books_eur = Book.objects.filter(
        price_amount__lt=Decimal('2'),
        price_currency="EUR"
    )


Defaults and choices
--------------------

You can provide separate defaults for the amount and the currency as Decimal and the three letter currency code string, respectively:

.. code:: python
    
    class Book(models.Model):
        name = models.CharField(blank=True, max_length=100)
        price = MoneyField(decimal_places=2, max_digits=8, 
                           amount_default=Decimal("0"),
                           currency_default="USD")


or a default Money value:

.. code:: python
    
    class Book(models.Model):
        name = models.CharField(blank=True, max_length=100)
        price = MoneyField(decimal_places=2, max_digits=8, 
                           default=Money("0", "USD"))

You can also set currency choices with ``currency_choices`` and a currency default with ``currency_default``:

.. code:: python
    
    class Book(models.Model):
        CURRENCY_CHOICES = (
            ('EUR', 'EUR'),
            ('USD', 'USD')
        )
        CURRENCY_DEFAULT = 'EUR'
        
        name = models.CharField(blank=True, max_length=100)
        price = MoneyField(decimal_places=2, max_digits=8, 
                           currency_choices=CURRENCY_CHOICES,
                           currency_default=CURRENCY_DEFAULT)


Fixed currency
--------------

If you don't need to handle different currencies but want to benefit from using the Money class instead of just Decimals, you may want to set a fixed currency for your monetary field:

.. code:: python

    class Book(models.Model):
        name = models.CharField(blank=True, max_length=100)
        price = MoneyField(decimal_places=2, max_digits=12, currency='USD')

In this case, the attribute ``price`` will only accept and return Money objects with currency "USD". **The database representation of this field will be** ``price_amount``, **with no currency column**. This is consistent with the multi-currency case, and allows for maximum flexibility while making schema migrations.


MoneyField options
==================

MoneyField.max_digits
    Same as DecimalField: The maximum number of digits allowed in the number. Note that this number must be greater than or equal to ``decimal_places``.

MoneyField.decimal_places
    Same as DecimalField: The number of decimal places to store with the number.

MoneyField.currency
    Fixed currency for this field. This will omit the creation of a ``<name>_currency`` column in the database.

MoneyField.default
    Default Money value for this field (both amount and currency).

MoneyField.currency_default
    Default currency value.

MoneyField.amount_default
    Default amount value.

MoneyField.currency_choices
    Regular Django choices iterable, e.g.::
    
        CURRENCY_CHOICES = (
            ('EUR', 'Euros'),
            ('USD', 'US Dollars')
        )


Forms
=====

A base model form class ``MoneyModelForm`` is included to show the monetary fields as just one field in forms, instead of separate amount and currency fields.

.. code:: python

    from django.contrib import admin
    from moneyfield import MoneyModelForm
    from myapp.models import Book

    class BookAdmin(admin.ModelAdmin):
        list_display = ['id', 'name', 'price']
        form = MoneyModelForm
    
    admin.site.register(Book, BookAdmin)


Using ``MoneyModelForm`` is optional. You may also include it in the base classes of your custom model form class.



.. figure:: https://raw.github.com/carlospalol/django-moneyfield/master/docs/static/img/form-choices.png
    
    **Using currency choices**

.. figure:: https://raw.github.com/carlospalol/django-moneyfield/master/docs/static/img/form-fixed.png
        
    **Using fixed currency**

.. figure:: https://raw.github.com/carlospalol/django-moneyfield/master/docs/static/img/form-free.png
    
    **Using free currency**


Contributions
=============

Contributions are welcome. You can use the `regular github mechanisms <https://help.github.com/>`_.

To run the tests, sit on the package root (by setup.py) and run:

::

    python tests/runtests.py


License
=======

django-moneyfield is released under the **MIT license**, which can be found in the file ``LICENSE``.



