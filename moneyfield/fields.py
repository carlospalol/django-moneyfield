import logging
from decimal import Decimal

from django.db import models

from money import Money


logger = logging.getLogger(__name__)


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
        return Money(*self._get_values(obj))
    
    def __set__(self, obj, value):
        """Set amount and currency attributes in the model instance"""
        if isinstance(value, Money):
            self._set_values(obj, value.amount, value.currency)
        elif isinstance(value, None):
            self._set_values(obj, None, None)
        else:
            raise TypeError('Cannot assign "{}" to MoneyField "{}".'.format(type(value), self.field.name))


class SimpleMoneyProxy(AbstractMoneyProxy):
    """Descriptor for MoneyFields with fixed currency"""
    def _get_values(self, obj):
        return (obj.__dict__[self.field.amount_attr], self.field.fixed_currency)
    
    def _set_values(self, obj, amount, currency=None):
        if not currency is None:
            if currency != self.field.fixed_currency:
                raise TypeError('Field "{}" is {}-only.'.format(self.field.name, self.field.fixed_currency))
        obj.__dict__[self.field.amount_attr] = amount


class CompositeMoneyProxy(AbstractMoneyProxy):
    """Descriptor for MoneyFields with variable currency via additional column"""
    def _get_values(self, obj):
        return (obj.__dict__[self.field.amount_attr], obj.__dict__[self.field.currency_attr])
    
    def _set_values(self, obj, amount, currency):
        obj.__dict__[self.field.amount_attr] = amount
        obj.__dict__[self.field.currency_attr] = currency


class MoneyField(models.Field):
    description = "Money"
    
    def __init__(self, verbose_name=None, name=None, max_digits=None,
                 decimal_places=None, currency=None, **kwargs):
        super().__init__(verbose_name, name, **kwargs)
        self.fixed_currency = currency
        
        self.amount_field = models.DecimalField(decimal_places=decimal_places, max_digits=max_digits, **kwargs)
        if not self.fixed_currency:
            self.currency_field = models.CharField(max_length=3, **kwargs)
    
    def contribute_to_class(self, cls, name):
        self.name = name
        self.amount_attr = '{}_amount'.format(name)
        cls.add_to_class(self.amount_attr, self.amount_field)
        
        if not self.fixed_currency:
            self.currency_attr = '{}_currency'.format(name)
            cls.add_to_class(self.currency_attr, self.currency_field)
            setattr(cls, name, CompositeMoneyProxy(self))
        else:
            setattr(cls, name, SimpleMoneyProxy(self))






