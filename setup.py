# -*- coding: utf-8 -*-
"""
Installs the following command-line executables:

    - ocrd-kraken-binarize
    - ocrd-kraken-segment
    - ocrd-kraken-recognize
"""
import codecs
from json import load

with open('ocrd-tool.json', 'r') as f_tool:
    version = load(f_tool)['version']

from setuptools import setup, find_packages

setup(
    name='ocrd_kraken',
    version=version,
    description='Kraken bindings',
    long_description=codecs.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Konstantin Baierer, Robert Sachunsky',
    author_email='unixprog@gmail.com, sachunsky@informatik.uni-leipzig.de',
    url='https://github.com/OCR-D/ocrd_kraken',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=open('requirements.txt').read().split('\n'),
    package_data={
        '': ['*.json', '*.yml', '*.yaml'],
    },
    entry_points={
        'console_scripts': [
            'ocrd-kraken-binarize=ocrd_kraken.cli.binarize:cli',
            'ocrd-kraken-segment=ocrd_kraken.cli.segment:cli',
            'ocrd-kraken-recognize=ocrd_kraken.cli.recognize:cli',
        ]
    },
)
