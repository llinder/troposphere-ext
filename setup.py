# vi: set ts=4 expandtab:
#
#    Copyright (C) 2015 Lance Linder
#

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name='troposphere-ext',
    version='0.1.0',
    author='Lance Linder',
    author_email='llinder@gmail.com',
    description='Troposphere Extensions',
    long_description=read('README.md'),
    license='Apache 2.0',
    keywords='troposphere troposphere-ext cloud-formation',
    url='https://github.com/llinder/troposphere-ext',
    package_data={},
    packages=find_packages(exclude=['tests', 'tests.*']),
    test_suite='tests',
    install_requires=['boto', 'troposphere', 'awacs', 'pyyaml']
)
