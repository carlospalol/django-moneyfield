#!/usr/bin/env python

import os
import sys

from django.conf import settings
from django.core import management

def main():
    testing_dir = os.path.abspath(os.path.dirname(__file__))
    package_dir = os.path.normpath(testing_dir + '/../')
    sys.path.append(testing_dir)
    sys.path.append(package_dir)
    
    settings.configure(**{
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        'USE_L10N': True,
        'SECRET_KEY': "justthetestapp",
        'INSTALLED_APPS': (
            'testapp',
        ),
    })
    management.call_command('test', 'testapp')

if __name__ == "__main__":
    main()