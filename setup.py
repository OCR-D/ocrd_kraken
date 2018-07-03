# -*- coding: utf-8 -*-
"""
Installs two binaries:

    - ocrd-kraken-binarize
    - ocrd-kraken-segment
"""
import codecs

from setuptools import setup, find_packages

with codecs.open('README.rst', encoding='utf-8') as f:
    README = f.read()

setup(
    name='ocrd_kraken',
    version='0.0.1',
    description='kraken bindings',
    long_description=README,
    author='Konstantin Baierer, Kay-Michael Würzner',
    author_email='unixprog@gmail.com, wuerzner@gmail.com',
    url='https://github.com/OCR-D/ocrd_kraken',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'ocrd >= 0.4.4',
        'kraken',
        'click',
    ],
    package_data={
        '': ['*.json', '*.yml', '*.yaml'],
    },
    entry_points={
        'console_scripts': [
            'ocrd-kraken-binarize=ocrd_kraken.cli:ocrd_kraken_binarize',
            'ocrd-kraken-segment=ocrd_kraken.cli:ocrd_kraken_segment',
        ]
    },
)
