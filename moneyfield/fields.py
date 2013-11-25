import logging
import re
from decimal import Decimal

from django import forms
from django.core.exceptions import FieldError, ValidationError
from django.forms.models import ModelFormMetaclass
from django.forms.util import flatatt
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.db import models
from django.db.models import NOT_PROVIDED

from money import Money

from .exceptions import *


__all__ = ['MoneyField', 'MoneyModelForm']


REGEX_CURRENCY_CODE = re.compile("^[A-Z]{3}$")
def currency_code_validator(value):
    if not REGEX_CURRENCY_CODE.match(force_text(value)):
        raise ValidationError('Invalid currency code.')


class MoneyModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if name == 'MoneyModelForm':
            return new_class
        
        modelopts = new_class._meta.model._meta
        if not hasattr(modelopts, 'moneyfields'):
            raise MoneyModelFormError("The Model used with this ModelForm "
                                      "does not contain MoneyFields")
        
        # Rebuild the dict of form fields by replacing fields derived from
        # money subfields with a specialised money multivalue form field,
        # while preserving the original ordering.
        fields = SortedDict()
        for fieldname, field in new_class.base_fields.items():
            for moneyfield in modelopts.moneyfields:
                if fieldname == moneyfield.amount_attr:
                    fields[moneyfield.name] = moneyfield.formfield()
                    break
                if fieldname == moneyfield.currency_attr:
                    break
            else:
                fields[fieldname] = field
        
        new_class.base_fields = fields
        return new_class


class MoneyModelForm(forms.ModelForm, metaclass=MoneyModelFormMetaclass):
    def __init__(self, *args, initial={}, instance=None, **kwargs):
        opts = self._meta
        modelopts = opts.model._meta
        if instance:
            # Populate the multivalue form field using the initial dict,
            # as model_to_dict() only sees the model's _meta.fields
            for moneyfield in modelopts.moneyfields:
                initial.update({
                    moneyfield.name: getattr(instance, moneyfield.name)}
                )
        
        super().__init__(*args, initial=initial, instance=instance, **kwargs)
        
        # Money "subfields" cannot be excluded separately
        if opts.exclude:
            for moneyfield in modelopts.moneyfields:
                if not moneyfield.fixed_currency:
                    if not ((moneyfield.amount_attr in opts.exclude) == 
                            (moneyfield.currency_attr in opts.exclude)):
                        msg = ('Cannot exclude only one money field '
                               'from the model form.')
                        raise MoneyModelFormError(msg)
    
    def clean(self):
        cleaned_data = super().clean()
        # Finish the work of forms.models.construct_instance() as it doesn't
        # find match between the form multivalue field (e.g. "price"), and the
        # model's _meta.fields (e.g. "price_amount" and "price_currency").
        opts = self._meta
        modelopts = opts.model._meta
        for moneyfield in modelopts.moneyfields:
            if moneyfield.name in self.cleaned_data:
                value = self.cleaned_data[moneyfield.name]
                if value:
                    setattr(self.instance, moneyfield.name, value)
        
        return cleaned_data


class MoneyWidget(forms.MultiWidget):
    def decompress(self, value):
        if isinstance(value, Money):
            return [value.amount, value.currency]
        if value is None:
            return [None, None]
        raise TypeError('MoneyWidgets accept only Money.')
    
    def format_output(self, rendered_widgets):
        return ' '.join(rendered_widgets)
    
    def value_from_datadict(self, data, files, name):
        # Enable datadict value to be compressed
        if name in data:
            return self.decompress(data[name])
        else:
            return super().value_from_datadict(data, files, name)


class MoneyFormField(forms.MultiValueField):
    def __init__(self, fields=(), *args, **kwargs):
        if not kwargs.setdefault('initial'):
            kwargs['initial'] = [f.initial for f in fields]
        super().__init__(*args, fields=fields, **kwargs)
    
    def compress(self, data_list):
        return Money(data_list[0], data_list[1])


class FixedCurrencyWidget(forms.Widget):
    def __init__(self, attrs=None, currency=None):
        assert currency
        super().__init__(attrs=attrs)
        self.currency = currency
    
    def value_from_datadict(self, data, files, name):
        # Defaults to fixed currency
        value = super().value_from_datadict(data, files, name)
        return value or self.currency
    
    def render(self, name, value, attrs=None):
        if value and not value is self.currency:
            msg = ('FixedCurrencyWidget "{}" with fixed currency "{}" '
                   'cannot be rendered with currency "{}".')
            raise TypeError(msg.format(name, self.currency, value))
        final_attrs = self.build_attrs(attrs, style='vertical-align: middle;')
        return format_html('<span{0}>{1}</span>',
                           flatatt(final_attrs),
                           self.currency)


class FixedCurrencyFormField(forms.Field):
    def __init__(self, currency=None, *args, **kwargs):
        assert currency
        self.currency = currency
        self.widget = FixedCurrencyWidget(currency=currency)
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        if not value is self.currency:
            msg = 'Invalid currency "{}" for "{}"-only FixedCurrencyFormField'
            raise ValidationError(msg.format(value, self.currency))


class AbstractMoneyProxy(object):
    """Object descriptor for MoneyFields"""
    def __init__(self, field):
        self.field = field
    
    def _get_values(self, obj):
        raise NotImplementedError()
    
    def _set_values(self, obj, amount, currency):
        raise NotImplementedError()
    
    def __get__(self, obj, model):
        """Return a Money object if called in a model instance"""
        if obj is None:
            return self.field
        amount, currency = self._get_values(obj)
        if amount is None or currency is None:
            return None
        return Money(amount, currency)
    
    def __set__(self, obj, value):
        """Set amount and currency attributes in the model instance"""
        if isinstance(value, Money):
            self._set_values(obj, value.amount, value.currency)
        elif isinstance(value, None):
            self._set_values(obj, None, None)
        else:
            msg = 'Cannot assign "{}" to MoneyField "{}".'
            raise TypeError(msg.format(type(value), self.field.name))


class SimpleMoneyProxy(AbstractMoneyProxy):
    """Descriptor for MoneyFields with fixed currency"""
    def _get_values(self, obj):
        return (obj.__dict__[self.field.amount_attr],
                self.field.fixed_currency)
    
    def _set_values(self, obj, amount, currency=None):
        if not currency is None:
            if currency != self.field.fixed_currency:
                raise TypeError('Field "{}" is {}-only.'.format(
                    self.field.name, 
                    self.field.fixed_currency
                ))
        obj.__dict__[self.field.amount_attr] = amount


class CompositeMoneyProxy(AbstractMoneyProxy):
    """Descriptor for MoneyFields with variable currency"""
    def _get_values(self, obj):
        return (obj.__dict__[self.field.amount_attr],
                obj.__dict__[self.field.currency_attr])
    
    def _set_values(self, obj, amount, currency):
        obj.__dict__[self.field.amount_attr] = amount
        obj.__dict__[self.field.currency_attr] = currency


class MoneyField(models.Field):
    description = "Money"
    
    def __init__(self, verbose_name=None, name=None,
                 max_digits=None, decimal_places=None,
                 currency=None, currency_choices=None,
                 currency_default=NOT_PROVIDED,
                 default=NOT_PROVIDED, amount_default=NOT_PROVIDED, **kwargs):
        
        super().__init__(verbose_name, name, default=default, **kwargs)
        self.fixed_currency = currency
        
        # DecimalField pre-validation
        if decimal_places is None or decimal_places < 0:
            msg = ('"{}": MoneyFields require a non-negative integer '
                   'argument "decimal_places".')
            raise FieldError(msg.format(self.name))
        if max_digits is None or max_digits <= 0:
            msg = ('"{}": MoneyFields require a positive integer '
                   'argument "max_digits".')
            raise FieldError(msg.format(self.name))
        
        # Currency must be either fixed or variable, not both.
        if currency and (currency_choices or currency_default != NOT_PROVIDED):
            msg = ('MoneyField "{}" has fixed currency "{}". '
                   'Do not use "currency_choices" or "currency_default" '
                   'at the same time.')
            raise FieldError(msg.format(self.name, currency))
        
        # Money default
        if default != NOT_PROVIDED:
            if type(default) is Money:
                # Must be compatible with fixed currency
                if currency and not (currency == default.currency):
                    msg = ('MoneyField "{}" has fixed currency "{}". '
                           'The default value "{}" is not compatible.')
                    raise FieldError(msg.format(self.name, currency, default))
                
                # Do not set other defaults at the same time
                if amount_default != NOT_PROVIDED:
                    msg = ('MoneyField "{}" has a default value "{}". Do not '
                           'use "amount_default" at the same time.')
                    raise FieldError(msg.format(self.name, default))
                
                if currency_default != NOT_PROVIDED:
                    msg = ('MoneyField "{}" has a default value "{}". '
                           'Do not use "currency_default" at the same time.')
                    raise FieldError(msg.format(self.name, default))
                
                amount_default = default.amount
                currency_default = default.currency
            else:
                msg = ('MoneyField "{}" default must be '
                       'of type Money, it is "{}".')
                raise TypeError(msg.format(self.name, type(currency)))
        
        self.amount_field = models.DecimalField(
            decimal_places=decimal_places,
            max_digits=max_digits,
            default=amount_default,
            **kwargs
        )
        if not self.fixed_currency:
            # This Moneyfield can have different currencies.
            # Add a currency column to the database
            self.currency_field = models.CharField(
                max_length=3,
                default=currency_default,
                choices=currency_choices,
                validators=[currency_code_validator],
                **kwargs
            )
    
    def contribute_to_class(self, cls, name):
        self.name = name
        
        self.amount_attr = '{}_amount'.format(name)
        cls.add_to_class(self.amount_attr, self.amount_field)
        
        if not self.fixed_currency:
            self.currency_attr = '{}_currency'.format(name)
            cls.add_to_class(self.currency_attr, self.currency_field)
            setattr(cls, name, CompositeMoneyProxy(self))
        else:
            self.currency_attr = None
            setattr(cls, name, SimpleMoneyProxy(self))
        
        # Keep a list of MoneyFields in the model's _meta
        # This will help identify which MoneyFields a model has
        if not hasattr(cls._meta, 'moneyfields'):
            cls._meta.moneyfields = []
        cls._meta.moneyfields.append(self)
    
    def formfield(self, **kwargs):
        formfield_amount = self.amount_field.formfield()
        if not self.fixed_currency:
            formfield_currency = self.currency_field.formfield(
                validators=[currency_code_validator]
            )
        else:
            formfield_currency = FixedCurrencyFormField(
                currency=self.fixed_currency
            )
        
        widget_amount = formfield_amount.widget
        widget_currency = formfield_currency.widget
        
        # Adjust currency input size
        if type(widget_currency) is forms.TextInput:
            widget_currency.attrs.update({'size': 3})
        
        config = {
            'fields': (formfield_amount, formfield_currency),
            'widget': MoneyWidget(widgets=(widget_amount, widget_currency))
        }
        config.update(kwargs)
        
        return super().formfield(form_class=MoneyFormField, **config)





