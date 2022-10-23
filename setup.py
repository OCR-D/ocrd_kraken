# -*- coding: utf-8 -*-
"""
Installs two binaries:

    - ocrd-kraken-binarize
    - ocrd-kraken-segment
"""
import codecs
from json import load

with open('ocrd-tool.json', 'r') as f_tool:
    version = load(f_tool)['version']
with open('requirements.txt', 'r', encoding='utf-8') as f_require:
    install_requires = f_require.readlines()

from setuptools import setup, find_packages

setup(
    name='ocrd_kraken',
    version=version,
    description='kraken bindings',
    long_description=codecs.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Konstantin Baierer, Kay-Michael Würzner',
    author_email='unixprog@gmail.com, wuerzner@gmail.com',
    url='https://github.com/OCR-D/ocrd_kraken',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=install_requires,
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
