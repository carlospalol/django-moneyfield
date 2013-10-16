#!/usr/bin/env python

import os
import sys

from django.conf import settings
from django.core import management

# test_settings = {
#     'DATABASES': {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#         }
#     },
#     'USE_L10N': True,
#     'SECRET_KEY': "justthetestapp",
#     'INSTALLED_APPS': (
#         'testapp',
#     ),
#     'MONEY_CURRENCY_CHOICES': (
#             ('AAA', 'AAA'),
#             ('BBB', 'BBB'),
#             ('CCC', 'CCC'),
#         )
# }

def main():
    testing_dir = os.path.abspath(os.path.dirname(__file__))
    package_dir = os.path.normpath(os.path.join(testing_dir, os.pardir))
    sys.path.append(testing_dir)
    sys.path.append(package_dir)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    management.call_command('test', 'testapp')

if __name__ == "__main__":
    main()