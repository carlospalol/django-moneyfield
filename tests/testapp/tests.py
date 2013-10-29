from decimal import Decimal

from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.core.exceptions import FieldError, ValidationError
from django.forms.models import modelform_factory
from django.conf import settings
from django.test import TestCase

from money import Money

from moneyfield import MoneyField, MoneyModelForm
from moneyfield.fields import MoneyFormField
from moneyfield import conf

from testapp.models import Book, Translator, Transaction, SomeMoney


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
        self.table_name = Transaction._meta.db_table
        self.cursor = connection.cursor()
    
    def tearDown(self):
        Transaction.objects.all().delete()
    
    def create_instance(self):
        return Transaction.objects.create(
            value_amount=Decimal('12345.67'), 
            value_currency='USD'
        )
    
    def test_db_schema_no_plain_field_name(self):
        with self.assertRaises(DatabaseError):
            self.cursor.execute('SELECT value from {}'.format(self.table_name))
    
    def test_db_schema_amount_field(self):
        self.cursor.execute('SELECT value_amount from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_db_schema_currency_field(self):
        self.cursor.execute('SELECT value_currency from {}'.format(self.table_name))
        self.assertEqual(self.cursor.fetchall(), [])
    
    def test_manager_create_with_money(self):
        with self.assertRaises(TypeError):
            transaction = Transaction.objects.create(value=Money('12345.67', 'USD'))
    
    def test_manager_create_with_values(self):
        transaction = self.create_instance()
        self.assertEqual(transaction.value_amount, Decimal('12345.67'))
        self.assertEqual(transaction.value_currency, 'USD')
    
    def test_instance_descriptor_get(self):
        transaction = self.create_instance()
        self.assertEqual(transaction.value, Money('12345.67', 'USD'))
    
    def test_instance_descriptor_set(self):
        transaction = self.create_instance()
        self.assertEqual(transaction.value, Money('12345.67', 'USD'))
        transaction.value = Money('25.00', 'USD')
        self.assertEqual(transaction.value, Money('25.00', 'USD'))
        transaction.save()
        self.assertEqual(transaction.value, Money('25.00', 'USD'))
    
    def test_instance_create(self):
        transaction = Transaction()
        transaction.value = Money('1', 'USD')
        transaction.save()
        self.assertEqual(transaction.value, Money('1', 'USD'))
    
    def test_instance_retrieval(self):
        transaction = self.create_instance()
        transaction_retrieved = Transaction.objects.all()[0]
        self.assertEqual(transaction_retrieved.value, Money('12345.67', 'USD'))
    
    def test_query_money(self):
        transaction = self.create_instance()
        with self.assertRaises(FieldError):
            results = Transaction.objects.filter(value=Money('12345.67', 'USD'))
    
    def test_query_amount(self):
        transaction = self.create_instance()
        results = Transaction.objects.filter(value_amount=Decimal('12345.67'))
        self.assertEqual(transaction.value, results[0].value)
    
    def test_query_currency(self):
        transaction = self.create_instance()
        results = Transaction.objects.filter(value_currency='USD')
        self.assertEqual(transaction.value, results[0].value)


class TestCurrencyChoices(TestCase):
    def setUp(self):
        self.Form = modelform_factory(Translator, form=MoneyModelForm)
    
    def tearDown(self):
        Translator.objects.all().delete()
    
    def test_default_currency(self):
        translator = Translator.objects.create(
            fee_amount=Decimal('45.67')
        )
        self.assertEqual(translator.fee, Money('45.67', 'USD'))
    
    def test_valid_currency(self):
        translator = Translator.objects.create(
            fee_amount=Decimal('45.67'),
            fee_currency='EUR',
        )
        translator.full_clean()
    
    def test_invalid_currency(self):
        translator = Translator.objects.create(
            fee_amount=Decimal('45.67'),
            fee_currency='XXX',
        )
        with self.assertRaises(ValidationError):
            translator.full_clean()


class TestMoneyModelFormBasics(TestCase):
    def test_field_natural_order(self):
        form = modelform_factory(SomeMoney, form=MoneyModelForm)()
        self.assertEqual(list(form.fields.keys()), ['field1', 'field2', 'field3'])
    
    def test_moneyfield_only(self):
        TransactionForm = modelform_factory(Transaction, form=MoneyModelForm)
        form = TransactionForm()
        names = form.fields.keys()
        self.assertIn('value', names)
        self.assertEqual(type(form.fields['value']), MoneyFormField)
        self.assertNotIn('value_amount', names)
        self.assertNotIn('value_currency', names)


class TestFreeCurrencyMoneyModelForm(TestCase):
    def setUp(self):
        self.Form = modelform_factory(Transaction, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'value': Money('1000.00', 'CHF'),
        })
        html = form.as_p()
        self.assertIn('value="1000.00"', html)
        self.assertIn('value="CHF"', html)
    
    def test_create_object(self):
        form = self.Form({
            'value_0': Decimal('123.99'),
            'value_1': 'GBP',
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.value, Money('123.99', 'GBP'))


class TestCurrencyChoicesMoneyModelForm(TestCase):
    def setUp(self):
        self.Form = modelform_factory(Translator, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'fee': Money('1.00', 'EUR'),
        })
        html = form.as_p()
        self.assertIn('value="1.00"', html)
        self.assertIn('value="EUR" selected="selected"', html)
    
    def test_create_object(self):
        form = self.Form({
            'fee_0': Decimal('33.44'),
            'fee_1': 'USD',
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.fee, Money('33.44', 'USD'))
    
    def test_currency_initial_from_default(self):
        form = self.Form()
        self.assertEqual(Translator.CURRENCY_DEFAULT, 'USD')
        self.assertEqual(form.fields['fee'].fields[1].initial, 'USD')
        self.assertEqual(form['fee'].field.initial, [None, 'USD'])
        self.assertEqual(form.instance.fee_currency, 'USD')
    
    def test_currency_widget_choices(self):
        form = self.Form()
        self.assertEqual(form.fields['fee'].fields[1].choices,
                         [('EUR', 'EUR'), ('USD', 'USD'), ('CNY', 'CNY')])

# class TestFixedCurrencyModelForm(TestCase):
#     def setUp(self):
#         self.BookForm = modelform_factory(Book, form=MoneyModelForm)
#     
#     def test_initial(self):
#         form = self.BookForm(initial={
#             'name': 'Neo',
#             'fee': Money('1.00', 'EUR'),
#         })
#         html = form.as_p()
#         self.assertIn('value="Neo"', html)
#         self.assertIn('value="1.00"', html)







