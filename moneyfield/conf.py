
CURRENCY_CHOICES = (
    ('EUR', 'EUR'),
)
CURRENCY_DEFAULT = 'EUR'



# App Settings Override 0.3
# https://gist.github.com/1925449
# Overrides any constant (uppercase attribute) in this module
# with the prefixed version from settings.py, if available.
# Place this script after constants and before calculated settings.
prefix = 'MONEY_'
import sys; from django.conf import settings
for n, cn, v in [(k, prefix+k, v) for k,v in vars().items() if k.isupper()]:
    setattr(sys.modules[__name__], n, getattr(settings, cn, v))
