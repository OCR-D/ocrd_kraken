# -*- coding: utf-8 -*-
"""
Installs one binary:

    - ocrd_kraken_binarize
"""
import codecs

from setuptools import setup, find_packages

with codecs.open('README.md', encoding='utf-8') as f:
    README = f.read()

with codecs.open('LICENSE', encoding='utf-8') as f:
    LICENSE = f.read().encode('utf-8')

setup(
    name='ocrd_kraken',
    version='0.0.1',
    description='kraken bindings',
    long_description=README,
    author='Konstantin Baierer, Kay-Michael Würzner',
    author_email='unixprog@gmail.com, wuerzner@gmail.com',
    url='https://github.com/OCR-D/ocrd_kraken',
    license=LICENSE,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'ocrd_kraken_binarize=ocrd_kraken.cli:ocrd_kraken_binarize',
        ]
    },
)
