from decimal import Decimal

from django.forms.models import modelform_factory
from django.test import TestCase

from money import Money

from moneyfield import MoneyField, MoneyModelForm
from moneyfield.fields import MoneyFormField
from moneyfield import conf

from testapp.models import (FixedCurrencyModel, FreeCurrencyModel,
                            ChoicesCurrencyModel, SomeMoney)


class TestMoneyModelFormOrdering(TestCase):
    def test_field_natural_order(self):
        form = modelform_factory(SomeMoney, form=MoneyModelForm)()
        self.assertEqual(list(form.fields.keys()), ['field1', 'field2', 'field3'])


class MoneyModelFormMixin(object):
    def test_moneyfield_only(self):
        form = self.Form()
        names = form.fields.keys()
        self.assertIn('price', names)
        self.assertEqual(type(form.fields['price']), MoneyFormField)
        self.assertNotIn('price_amount', names)
        self.assertNotIn('price_currency', names)
    
    def test_data_decompressed(self):
        form = self.Form(data={
            'price_0': Decimal('1234.99'),
            'price_1': 'EUR',
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.price, Money('1234.99', 'EUR'))
    
    def test_data_compressed(self):
        form = self.Form(data={
            'price': Money('1234.99', 'EUR')
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.price, Money('1234.99', 'EUR'))
    
    def test_initial(self):
        raise NotImplementedError()


class TestFixedCurrencyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(FixedCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.99', 'EUR'),
        })
        html = form.as_p()
        self.assertIn('value="1234.99"', html)
        self.assertNotIn('value="EUR"', html)


class TestFreeCurrencyMoneyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(FreeCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.99', 'USD'),
        })
        html = form.as_p()
        self.assertIn('value="1234.99"', html)
        self.assertIn('value="USD"', html)


class TestChoicesCurrencyMoneyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(ChoicesCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.99', 'USD'),
        })
        html = form.as_p()
        self.assertIn('value="1234.99"', html)
        self.assertIn('value="USD" selected="selected"', html)
    
    def test_currency_initial_different_than_default(self):
        form = self.Form(initial={
            'price': Money('1234.99', 'EUR'),
        })
        html = form.as_p()
        self.assertIn('value="1234.99"', html)
        self.assertIn('value="EUR" selected="selected"', html)
    
    def test_currency_initial_from_default(self):
        form = self.Form()
        self.assertEqual(ChoicesCurrencyModel.CURRENCY_DEFAULT, 'USD')
        self.assertEqual(form.fields['price'].fields[1].initial, 'USD')
        self.assertEqual(form['price'].field.initial, [None, 'USD'])
        self.assertEqual(form.instance.price_currency, 'USD')
    
    def test_currency_widget_choices(self):
        form = self.Form()
        self.assertEqual(form.fields['price'].fields[1].choices,
                         [('EUR', 'EUR'), ('USD', 'USD'), ('CNY', 'CNY')])




