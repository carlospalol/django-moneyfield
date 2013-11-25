DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

USE_L10N = True

SECRET_KEY = "justthetestapp"

INSTALLED_APPS = (
    'testapp',
)

MONEY_CURRENCY_CHOICES = (
    ('AAA', 'AAA'),
    ('BBB', 'BBB'),
    ('CCC', 'CCC'),
)