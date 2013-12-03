from distutils.core import setup


DESCRIPTION="""
"""

setup(
    name="django-moneyfield",
    description="Django Money Model Field",
    long_description=DESCRIPTION,
    version="0.2.1",
    author="Carlos Palol",
    author_email="carlos.palol@awarepixel.com",
    url="https://github.com/carlospalol/django-moneyfield",
    packages=[
        'moneyfield'
    ],
    requires=[
        'django (>=1.5)',
        'money',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries',
    ]
)
