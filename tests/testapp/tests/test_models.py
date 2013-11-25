from decimal import Decimal

from django.db import connection
from django.db.utils import DatabaseError
from django.core.exceptions import FieldError, ValidationError
from django.test import TestCase

from money import Money

from moneyfield import MoneyField

from testapp.models import *


class TestFieldValidation(TestCase):
    def test_missing_decimal_places(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(name='testfield', max_digits=8)
        self.assertIn('decimal_places', cm.exception.args[0])
    
    def test_missing_max_digits(self):
        with self.assertRaises(FieldError) as cm:
            testfield = MoneyField(name='testfield', decimal_places=2)
        self.assertIn('max_digits', cm.exception.args[0])
    
    def test_both_fixed_currency_and_currency_default(self):
        with self.assertRaises(FieldError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency='USD',
                currency_default='USD',
            )
    
    def test_both_fixed_currency_and_currency_choices(self):
        with self.assertRaises(FieldError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency='USD',
                currency_choices=(('USD', 'USD'),),
            )
    
    def test_both_fixed_currency_and_default_valid(self):
        testfield = MoneyField(
            name='testfield',
            decimal_places=2,
            max_digits=8,
            currency='USD',
            default=Money('1234.00', 'USD'),
        )
    
    def test_both_fixed_currency_and_default_invalid(self):
        with self.assertRaises(FieldError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency='USD',
                default=Money('1234.00', 'EUR'),
            )
    
    def test_both_default_and_amount_default(self):
        with self.assertRaises(FieldError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                amount_default=Decimal('1234.00'),
                default=Money('1234.00', 'EUR'),
            )
    
    def test_both_default_and_currency_default(self):
        with self.assertRaises(FieldError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                currency_default='EUR',
                default=Money('1234.00', 'EUR'),
            )
    
    def test_invalid_default(self):
        with self.assertRaises(TypeError):
            testfield = MoneyField(
                name='testfield',
                decimal_places=2,
                max_digits=8,
                default="1234.00 EUR",
            )


class TestMoneyFieldMixin(object):
    def setUp(self):
        self.table_name = self.model._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        self.model.objects.all().delete()
    
    def manager_create_instance(self):
        raise NotImplementedError()
    
    def test_manager_create(self):
        obj = self.manager_create_instance()
    
    def test_instance_create(self):
        obj = self.model()
        obj.price = Money('1234.00', 'EUR')
        obj.save()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
    
    def test_instance_amount(self):
        obj = self.manager_create_instance()
        self.assertEqual(obj.price_amount, Decimal('1234.00'))
    
    def test_db_schema_no_plain_field_name(self):
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT price from {}'.format(self.table_name))
    
    def test_db_schema_amount_field(self):
        self.cursor.execute('SELECT price_amount from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_manager_create_with_money(self):
        with self.assertRaises(TypeError):
            obj = self.model.objects.create(price=Money('1234.00', 'EUR'))
    
    def test_instance_descriptor_get(self):
        obj = self.manager_create_instance()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
    
    def test_instance_descriptor_set(self):
        obj = self.manager_create_instance()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
        obj.price = Money('0.99', 'EUR')
        self.assertEqual(obj.price, Money('0.99', 'EUR'))
        obj.save()
        self.assertEqual(obj.price, Money('0.99', 'EUR'))
    
    def test_instance_descriptor_incomplete_only_amount(self):
        obj = self.model()
        obj.price_amount = Decimal('1234.00')
        obj.price_currency = None
        self.assertIsNone(obj.price)
    
    def test_instance_descriptor_incomplete_only_currency(self):
        obj = self.model()
        obj.price_amount = None
        obj.price_currency = 'EUR'
        self.assertIsNone(obj.price)
    
    def test_instance_retrieval(self):
        obj = self.manager_create_instance()
        obj_retrieved = self.model.objects.all()[0]
        self.assertEqual(obj_retrieved.price, obj.price)
    
    def test_query_money(self):
        obj = self.manager_create_instance()
        with self.assertRaises(FieldError):
            results = FixedCurrencyModel.objects.filter(price=Money('1234.00', 'EUR'))
    
    def test_query_amount(self):
        obj = self.manager_create_instance()
        results = self.model.objects.filter(price_amount=Decimal('1234.00'))
        self.assertEqual(results.count(), 1)
        self.assertEqual(obj, results[0])
        self.assertEqual(obj.price, results[0].price)


class TestFixedCurrencyMoneyField(TestMoneyFieldMixin, TestCase):
    model = FixedCurrencyModel
    
    def manager_create_instance(self):
        return self.model.objects.create(price_amount=Decimal('1234.00'))
    
    def test_db_schema_no_currency_field(self):
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT price_currency from {}'.format(self.table_name))
    
    def test_instance_descriptor_incomplete_only_amount(self):
        # Fixed currency field always has currency
        pass
    
    def test_invalid_manager_create_argument(self):
        with self.assertRaises(TypeError):
            obj = self.model.objects.create(price_amount=Decimal('1234.00'), price_currency='USD')
    
    def test_invalid_currency_assignation(self):
        obj = self.model()
        with self.assertRaises(TypeError):
            obj.price = Money('1234.00', 'USD')


class TestFixedCurrencyDefaultAmountMoneyField(TestFixedCurrencyMoneyField):
    model = FixedCurrencyDefaultAmountModel
    
    def manager_create_instance(self):
        return self.model.objects.create()


class TestFreeCurrencyMoneyField(TestMoneyFieldMixin, TestCase):
    model = FreeCurrencyModel
    
    def manager_create_instance(self):
        return self.model.objects.create(price_amount=Decimal('1234.00'), price_currency='EUR')
    
    def test_db_schema_currency_field(self):
        self.cursor.execute('SELECT price_currency from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_instance_currency(self):
        obj = self.manager_create_instance()
        self.assertEqual(obj.price_currency, 'EUR')
    
    def test_query_currency(self):
        obj = self.manager_create_instance()
        results = self.model.objects.filter(price_currency='EUR')
        self.assertEqual(results.count(), 1)
        self.assertEqual(obj, results[0])
        self.assertEqual(obj.price, results[0].price)
    
    def test_invalid_currency_code(self):
        obj = self.manager_create_instance()
        obj.price_currency = "AA"
        with self.assertRaises(ValidationError):
            obj.full_clean()
        obj.price_currency = "123"
        with self.assertRaises(ValidationError):
            obj.full_clean()


class TestFreeCurrencyDefaultAmountMoneyField(TestFreeCurrencyMoneyField):
    model = FreeCurrencyDefaultAmountModel
    
    def manager_create_instance(self):
        return self.model.objects.create(price_currency='EUR')


class TestChoicesCurrencyMoneyField(TestMoneyFieldMixin, TestCase):
    model = ChoicesCurrencyModel
    
    def manager_create_instance(self):
        return self.model.objects.create(price_amount=Decimal('1234.00'), price_currency='EUR')
    
    def test_instance_currency(self):
        obj = self.manager_create_instance()
        self.assertEqual(obj.price_currency, 'EUR')
    
    def test_default_currency(self):
        obj = self.model.objects.create(price_amount=Decimal('1234.00'))
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
    
    def test_non_default_currency(self):
        obj = self.model.objects.create(price_amount=Decimal('1234.00'), price_currency='USD')
        self.assertEqual(obj.price, Money('1234.00', 'USD'))
    
    def test_valid_currency(self):
        obj = self.manager_create_instance()
        obj.full_clean()
    
    def test_invalid_currency(self):
        obj = self.model.objects.create(price_amount=Decimal('1234.00'), price_currency='XXX')
        with self.assertRaises(ValidationError):
            obj.full_clean()


class TestChoicesCurrencyDefaultAmountMoneyField(TestChoicesCurrencyMoneyField):
    model = ChoicesCurrencyDefaultAmounModel
    
    def manager_create_instance(self):
        return self.model.objects.create()



