from decimal import Decimal

from django.forms.models import modelform_factory
from django.test import TestCase

from money import Money

from moneyfield.exceptions import *
from moneyfield.fields import MoneyFormField
from moneyfield import MoneyField, MoneyModelForm

from testapp.models import (DummyModel, FixedCurrencyModel, FreeCurrencyModel,
                            ChoicesCurrencyModel, SomeMoney)


class TestMoneyModelFormOrdering(TestCase):
    def test_field_natural_order(self):
        form = modelform_factory(SomeMoney, form=MoneyModelForm)()
        self.assertEqual(list(form.fields.keys()), ['field1', 'field2', 'field3'])


class TestMoneyModelFormValidation(TestCase):
    def test_model_without_moneyfields(self):
        with self.assertRaises(MoneyModelFormError):
            Form = modelform_factory(DummyModel, form=MoneyModelForm)
    
    def test_excluded_all_moneyfield_parts(self):
        Form = modelform_factory(FixedCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_amount', 'price_currency'])
        form = Form()
    
    def test_excluded_amount_fixed_currency(self):
        Form = modelform_factory(FixedCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_amount'])
        form = Form()
    
    def test_excluded_amount_free_currency(self):
        Form = modelform_factory(FreeCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_amount'])
        with self.assertRaises(MoneyModelFormError):
            form = Form()
    
    def test_excluded_amount_choices_currency(self):
        Form = modelform_factory(ChoicesCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_amount'])
        with self.assertRaises(MoneyModelFormError):
            form = Form()
    
    def test_excluded_currency_free_currency(self):
        Form = modelform_factory(FreeCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_currency'])
        with self.assertRaises(MoneyModelFormError):
            form = Form()
    
    def test_excluded_currency_choices_currency(self):
        Form = modelform_factory(ChoicesCurrencyModel, form=MoneyModelForm, 
                                 exclude=['price_currency'])
        with self.assertRaises(MoneyModelFormError):
            form = Form()


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
            'price_0': Decimal('1234.00'),
            'price_1': 'EUR',
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
    
    def test_data_compressed(self):
        form = self.Form(data={
            'price': Money('1234.00', 'EUR')
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))
    
    def test_initial(self):
        raise NotImplementedError()


class TestFixedCurrencyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(FixedCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.00', 'EUR'),
        })
        html = form.as_p()
        self.assertIn('value="1234.00"', html)
        self.assertNotIn('value="EUR"', html)
    
    def test_invalid_initial(self):
        form = self.Form(initial={
            'price': Money('1234.00', 'USD'),
        })
        with self.assertRaises(InvalidMoneyFieldCurrency):
            html = form.as_p()
    
    def test_invalid_data_decompressed(self):
        form = self.Form(data={
            'price_0': Decimal('1234.00'),
            'price_1': 'GBP',
        })
        self.assertFalse(form.is_valid())
    
    def test_invalid_data_compressed(self):
        form = self.Form(data={
            'price': Money('1234.00', 'GBP'),
        })
        self.assertFalse(form.is_valid())
    
    def test_data_decompressed_fixed_currency(self):
        form = self.Form(data={
            'price_0': Decimal('1234.00'),
        })
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.price, Money('1234.00', 'EUR'))


class TestFreeCurrencyMoneyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(FreeCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.00', 'USD'),
        })
        html = form.as_p()
        self.assertIn('value="1234.00"', html)
        self.assertIn('value="USD"', html)


class TestChoicesCurrencyMoneyModelForm(MoneyModelFormMixin, TestCase):
    def setUp(self):
        self.Form = modelform_factory(ChoicesCurrencyModel, form=MoneyModelForm)
    
    def test_initial(self):
        form = self.Form(initial={
            'price': Money('1234.00', 'USD'),
        })
        html = form.as_p()
        self.assertIn('value="1234.00"', html)
        self.assertIn('value="USD" selected="selected"', html)
    
    def test_currency_initial_different_than_default(self):
        form = self.Form(initial={
            'price': Money('1234.00', 'EUR'),
        })
        html = form.as_p()
        self.assertIn('value="1234.00"', html)
        self.assertIn('value="EUR" selected="selected"', html)
    
    def test_currency_initial_from_default(self):
        form = self.Form()
        self.assertEqual(ChoicesCurrencyModel.CURRENCY_DEFAULT, 'EUR')
        self.assertEqual(form.fields['price'].fields[1].initial, 'EUR')
        self.assertEqual(form['price'].field.initial, [None, 'EUR'])
        self.assertEqual(form.instance.price_currency, 'EUR')
    
    def test_currency_widget_choices(self):
        form = self.Form()
        self.assertEqual(form.fields['price'].fields[1].choices,
                         [('EUR', 'EUR'), ('USD', 'USD'), ('CNY', 'CNY')])




