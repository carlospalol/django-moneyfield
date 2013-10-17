import logging
from decimal import Decimal

from django import forms
from django.forms.models import ModelFormMetaclass
from django.db import models
from django.db.models import NOT_PROVIDED

from money import Money


logger = logging.getLogger(__name__)


class MoneyModelFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if name == 'MoneyModelForm':
            return new_class
        model_attrs = new_class._meta.model.__dict__
        for name, field in model_attrs.items():
            if isinstance(field, AbstractMoneyProxy):
                new_class.base_fields.update({
                    name: MoneyFormField()
                })
                if field._amount_attr:
                    del new_class.base_fields[field._amount_attr]
                if field._currency_attr:
                    del new_class.base_fields[field._currency_attr]
        
        return new_class


class MoneyModelForm(forms.ModelForm, metaclass=MoneyModelFormMetaclass):
    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        instance = kwargs.pop('instance', None)
        
        if instance:
            model_attrs = self._meta.model.__dict__
            for name, field in model_attrs.items():
                if isinstance(field, AbstractMoneyProxy):
                    initial.update({
                        name: getattr(instance, name)
                    })
        super().__init__(*args, initial=initial, instance=instance, **kwargs)
    
    def clean(self):
        logger.debug("MoneyModelForm.clean()")
        logger.debug(self.cleaned_data)
        model_attrs = self._meta.model.__dict__
        for name, field in model_attrs.items():
            if isinstance(field, AbstractMoneyProxy):
                logger.debug(self.cleaned_data)
                # FIXME: keyerror on validation error
                value = self.cleaned_data[name]
                if value:
                    setattr(self.instance, name, value)
        return super().clean()


class MoneyWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.TextInput(attrs=attrs),
            forms.TextInput(attrs=attrs,),
        )
        super().__init__(widgets, attrs)
    
    def decompress(self, value):
        if value:
            return [value.amount, value.currency]
        return [None, None]
    
    def format_output(self, rendered_widgets):
        return ' '.join(rendered_widgets)


class MoneyFormField(forms.MultiValueField):
    widget = MoneyWidget
    
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DecimalField(),
            forms.CharField(),
        )
        super().__init__(fields, *args, **kwargs)
    
    def compress(self, data_list):
        return Money(data_list[0], data_list[1])


class AbstractMoneyProxy(object):
    """Object descriptor for MoneyFields"""
    def __init__(self, field, amount_attr, currency_attr):
        self.field = field
        self._amount_attr = amount_attr
        self._currency_attr = currency_attr
    
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
        return (obj.__dict__[self._amount_attr], self.field.fixed_currency)
    
    def _set_values(self, obj, amount, currency=None):
        if not currency is None:
            if currency != self.field.fixed_currency:
                raise TypeError('Field "{}" is {}-only.'.format(self.field.name, self.field.fixed_currency))
        obj.__dict__[self._amount_attr] = amount


class CompositeMoneyProxy(AbstractMoneyProxy):
    """Descriptor for MoneyFields with variable currency via additional column"""
    def _get_values(self, obj):
        return (obj.__dict__[self._amount_attr], obj.__dict__[self._currency_attr])
    
    def _set_values(self, obj, amount, currency):
        obj.__dict__[self._amount_attr] = amount
        obj.__dict__[self._currency_attr] = currency


class MoneyField(models.Field):
    description = "Money"
    
    def __init__(self, verbose_name=None, name=None,  max_digits=None,
                 decimal_places=None, currency=None, currency_choices=None,
                 currency_default=NOT_PROVIDED, **kwargs):
        super().__init__(verbose_name, name, **kwargs)
        self.fixed_currency = currency
        
        self.amount_field = models.DecimalField(
            decimal_places=decimal_places,
            max_digits=max_digits,
            **kwargs
        )
        if not self.fixed_currency:
            self.currency_field = models.CharField(
                max_length=3,
                default=currency_default,
                choices=currency_choices,
                **kwargs
            )
    
    def contribute_to_class(self, cls, name):
        self.name = name
        
        
        
        amount_attr = '{}_amount'.format(name)
        cls.add_to_class(amount_attr, self.amount_field)
        
        if not self.fixed_currency:
            currency_attr = '{}_currency'.format(name)
            cls.add_to_class(currency_attr, self.currency_field)
            setattr(cls, name, CompositeMoneyProxy(self, amount_attr, currency_attr))
        else:
            setattr(cls, name, SimpleMoneyProxy(self, amount_attr, None))






