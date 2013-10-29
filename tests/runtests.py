#!/usr/bin/env python
import os
import sys

from django.conf import settings
from django.core import management


def runtests():
    pkg_path = os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir)
    )
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    management.call_command('test', 'testapp')


if __name__ == '__main__':
    runtests()