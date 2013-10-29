from decimal import Decimal

from django.db import connection
from django.db.utils import DatabaseError
from django.core.exceptions import FieldError, ValidationError
from django.conf import settings
from django.test import TestCase

from money import Money

from moneyfield import MoneyField
from moneyfield import conf

from testapp.models import (FixedCurrencyModel, FreeCurrencyModel,
                            ChoicesCurrencyModel, SomeMoney)


class TestAppConfiguration(TestCase):
    def test_currency_choices(self):
        self.assertEqual(
            settings.MONEY_CURRENCY_CHOICES, 
            conf.CURRENCY_CHOICES
        )


class TestFieldValidation(TestCase):
    def test_missing_decimal_places(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(name='testfield', max_digits=8)
        self.assertIn('decimal_places', cm.exception.args[0])
    
    def test_missing_max_digits(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(name='testfield', decimal_places=2)
        self.assertIn('max_digits', cm.exception.args[0])
    
    def test_invalid_option_currency_default(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency='USD',
                currency_default='USD',
            )
        self.assertIn('has fixed currency', cm.exception.args[0])
    
    def test_invalid_option_currency_choices(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency='USD',
                currency_choices=(('USD', 'USD'),),
            )
        self.assertIn('has fixed currency', cm.exception.args[0])


class TestFixedCurrencyField(TestCase):
    def setUp(self):
        self.table_name = FixedCurrencyModel._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        FixedCurrencyModel.objects.all().delete()
    
    def create_instance(self):
        return FixedCurrencyModel.objects.create(price_amount=Decimal('9.99'))
    
    def test_db_schema_no_plain_field_name(self):
        # SQL error "no such column: price" might vary
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT price from {}'.format(self.table_name))
    
    def test_db_schema_amount_field(self):
        self.cursor.execute('SELECT price_amount from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_db_schema_no_currency_field(self):
        # SQL error "no such column: price_currency" might vary
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT price_currency from {}'.format(self.table_name))
    
    def test_manager_create_with_money(self):
        with self.assertRaises(TypeError):
            book = FixedCurrencyModel.objects.create(price=Money('9.99', 'EUR'))
    
    def test_manager_create_with_amount(self):
        book = self.create_instance()
        self.assertEqual(book.price_amount, Decimal('9.99'))
    
    def test_instance_descriptor_get(self):
        book = self.create_instance()
        self.assertEqual(book.price, Money('9.99', 'EUR'))
    
    def test_instance_descriptor_set(self):
        book = self.create_instance()
        self.assertEqual(book.price, Money('9.99', 'EUR'))
        book.price = Money('19.99', 'EUR')
        self.assertEqual(book.price, Money('19.99', 'EUR'))
        book.save()
        self.assertEqual(book.price, Money('19.99', 'EUR'))
    
    def test_instance_create(self):
        book = FixedCurrencyModel()
        book.price = Money('9.99', 'EUR')
        book.save()
        self.assertEqual(book.price, Money('9.99', 'EUR'))
    
    def test_instance_retrieval(self):
        book = self.create_instance()
        book_retrieved = FixedCurrencyModel.objects.all()[0]
        self.assertEqual(book_retrieved.price, Money('9.99', 'EUR'))
    
    def test_query_money(self):
        book = self.create_instance()
        with self.assertRaises(FieldError):
            results = FixedCurrencyModel.objects.filter(price=Money('9.99', 'EUR'))
    
    def test_query_amount(self):
        book = self.create_instance()
        results = FixedCurrencyModel.objects.filter(price_amount=Decimal('9.99'))
        self.assertEqual(book.price, results[0].price)


class TestVariableCurrencyField(TestCase):
    def setUp(self):
        self.table_name = FreeCurrencyModel._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        FreeCurrencyModel.objects.all().delete()
    
    def create_instance(self):
        return FreeCurrencyModel.objects.create(
            price_amount=Decimal('1234.00'), 
            price_currency='USD'
        )
    
    def test_db_schema_no_plain_field_name(self):
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT price from {}'.format(self.table_name))
    
    def test_db_schema_amount_field(self):
        self.cursor.execute('SELECT price_amount from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_db_schema_currency_field(self):
        self.cursor.execute('SELECT price_currency from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_manager_create_with_money(self):
        with self.assertRaises(TypeError):
            obj = FreeCurrencyModel.objects.create(price=Money('1234.00', 'USD'))
    
    def test_manager_create_with_prices(self):
        obj = self.create_instance()
        self.assertEqual(obj.price_amount, Decimal('1234.00'))
        self.assertEqual(obj.price_currency, 'USD')
    
    def test_instance_descriptor_get(self):
        obj = self.create_instance()
        self.assertEqual(obj.price, Money('1234.00', 'USD'))
    
    def test_instance_descriptor_set(self):
        obj = self.create_instance()
        self.assertEqual(obj.price, Money('1234.00', 'USD'))
        obj.price = Money('25.00', 'USD')
        self.assertEqual(obj.price, Money('25.00', 'USD'))
        obj.save()
        self.assertEqual(obj.price, Money('25.00', 'USD'))
    
    def test_instance_create(self):
        obj = FreeCurrencyModel()
        obj.price = Money('1', 'USD')
        obj.save()
        self.assertEqual(obj.price, Money('1', 'USD'))
    
    def test_instance_retrieval(self):
        obj = self.create_instance()
        obj_retrieved = FreeCurrencyModel.objects.all()[0]
        self.assertEqual(obj_retrieved.price, Money('1234.00', 'USD'))
    
    def test_query_money(self):
        obj = self.create_instance()
        with self.assertRaises(FieldError):
            results = FreeCurrencyModel.objects.filter(price=Money('1234.00', 'USD'))
    
    def test_query_amount(self):
        obj = self.create_instance()
        results = FreeCurrencyModel.objects.filter(price_amount=Decimal('1234.00'))
        self.assertEqual(obj.price, results[0].price)
    
    def test_query_currency(self):
        obj = self.create_instance()
        results = FreeCurrencyModel.objects.filter(price_currency='USD')
        self.assertEqual(obj.price, results[0].price)


class TestCurrencyChoices(TestCase):
    def tearDown(self):
        ChoicesCurrencyModel.objects.all().delete()
    
    def test_default_currency(self):
        obj = ChoicesCurrencyModel.objects.create(
            price_amount=Decimal('1234.00')
        )
        self.assertEqual(obj.price, Money('1234.00', 'USD'))
    
    def test_valid_currency(self):
        obj = ChoicesCurrencyModel.objects.create(
            price_amount=Decimal('1234.00'),
            price_currency='EUR',
        )
        obj.full_clean()
    
    def test_invalid_currency(self):
        obj = ChoicesCurrencyModel.objects.create(
            price_amount=Decimal('1234.00'),
            price_currency='XXX',
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()






