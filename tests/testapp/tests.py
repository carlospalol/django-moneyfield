from decimal import Decimal

from django.core.exceptions import FieldError
from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.test import TestCase

from money import Money

from moneyfield import MoneyField

from testapp.models import Book, Translator, Transaction
from testapp.forms import TransactionModelForm


class TestAppConfiguration(TestCase):
    def test_currency_choices(self):
        import test_settings
        from moneyfield import conf
        self.assertEqual(
            test_settings.MONEY_CURRENCY_CHOICES, 
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
        self.table_name = Book._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        Book.objects.all().delete()
    
    def create_instance(self):
        return Book.objects.create(price_amount=Decimal('9.99'))
    
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
            book = Book.objects.create(price=Money('9.99', 'EUR'))
    
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
        book = Book()
        book.price = Money('9.99', 'EUR')
        book.save()
        self.assertEqual(book.price, Money('9.99', 'EUR'))
    
    def test_instance_retrieval(self):
        book = self.create_instance()
        book_retrieved = Book.objects.all()[0]
        self.assertEqual(book_retrieved.price, Money('9.99', 'EUR'))
    
    def test_query_money(self):
        book = self.create_instance()
        with self.assertRaises(FieldError):
            results = Book.objects.filter(price=Money('9.99', 'EUR'))
    
    def test_query_amount(self):
        book = self.create_instance()
        results = Book.objects.filter(price_amount=Decimal('9.99'))
        self.assertEqual(book.price, results[0].price)


class TestVariableCurrencyField(TestCase):
    def setUp(self):
        self.table_name = Translator._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        Translator.objects.all().delete()
    
    def create_instance(self):
        return Translator.objects.create(
            fee_amount=Decimal('45.00'), 
            fee_currency='USD'
        )
    
    def test_db_schema_no_plain_field_name(self):
        # SQL error "no such column: fee" might vary
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT fee from {}'.format(self.table_name))
    
    def test_db_schema_amount_field(self):
        self.cursor.execute('SELECT fee_amount from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_db_schema_currency_field(self):
        self.cursor.execute('SELECT fee_currency from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_manager_create_with_money(self):
        with self.assertRaises(TypeError):
            translator = Translator.objects.create(fee=Money('45.00', 'USD'))
    
    def test_manager_create_with_values(self):
        translator = self.create_instance()
        self.assertEqual(translator.fee_amount, Decimal('45.00'))
        self.assertEqual(translator.fee_currency, 'USD')
    
    def test_instance_descriptor_get(self):
        translator = self.create_instance()
        self.assertEqual(translator.fee, Money('45.00', 'USD'))
    
    def test_instance_descriptor_set(self):
        translator = self.create_instance()
        self.assertEqual(translator.fee, Money('45.00', 'USD'))
        translator.fee = Money('25.00', 'USD')
        self.assertEqual(translator.fee, Money('25.00', 'USD'))
        translator.save()
        self.assertEqual(translator.fee, Money('25.00', 'USD'))
    
    def test_instance_create(self):
        translator = Translator()
        translator.fee = Money('45.00', 'USD')
        translator.save()
        self.assertEqual(translator.fee, Money('45.00', 'USD'))
    
    def test_instance_retrieval(self):
        translator = self.create_instance()
        translator_retrieved = Translator.objects.all()[0]
        self.assertEqual(translator_retrieved.fee, Money('45.00', 'USD'))
    
    def test_query_money(self):
        translator = self.create_instance()
        with self.assertRaises(FieldError):
            results = Translator.objects.filter(fee=Money('45.00', 'USD'))
    
    def test_query_amount(self):
        translator = self.create_instance()
        results = Translator.objects.filter(fee_amount=Decimal('45.00'))
        self.assertEqual(translator.fee, results[0].fee)
    
    def test_query_currency(self):
        translator = self.create_instance()
        results = Translator.objects.filter(fee_currency='USD')
        self.assertEqual(translator.fee, results[0].fee)


class TestCurrencyChoices(TestCase):
    def tearDown(self):
        Transaction.objects.all().delete()
    
    def test_default_currency(self):
        transaction = Transaction.objects.create(
            value_amount=Decimal('1234567.89')
        )
        self.assertEqual(transaction.value, Money('1234567.89', 'USD'))
    
    def test_valid_currency(self):
        form = TransactionModelForm(data={
            'value_amount': Decimal('1234567.89'),
            'value_currency': 'USD',
        })
        self.assertTrue(form.is_valid())
    
    def test_invalid_currency(self):
        form = TransactionModelForm(data={
            'value_amount': Decimal('1234567.89'),
            'value_currency': 'XXX',
        })
        self.assertFalse(form.is_valid())








