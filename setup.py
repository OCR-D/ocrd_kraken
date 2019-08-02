# -*- coding: utf-8 -*-
"""
Installs two binaries:

    - ocrd-kraken-binarize
    - ocrd-kraken-segment
"""
import codecs

from setuptools import setup, find_packages

setup(
    name='ocrd_kraken',
    version='0.1.1',
    description='kraken bindings',
    long_description=codecs.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Konstantin Baierer, Kay-Michael Würzner',
    author_email='unixprog@gmail.com, wuerzner@gmail.com',
    url='https://github.com/OCR-D/ocrd_kraken',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'ocrd >= 1.0.0a4',
        'kraken == 0.9.16',
        'click >= 7',
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
