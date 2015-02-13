#
#    Copyright (C) 2015 Lance Linder
#

import os
from setuptools import setup, find_packages
from troposphere_ext.version import __version__


# Utility function to read the README file.
def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r') as f:
        return f.read()

required = read('requirements.txt').splitlines()
dev_required = read('dev-requirements.txt').splitlines()

ldesc = read('README.md')
ldesc += "\n\n" + read('CHANGES')

setup(
    name='troposphere-ext',
    version=__version__,
    author='Lance Linder',
    author_email='llinder@gmail.com',
    description='Troposphere Extensions',
    long_description=ldesc,
    license='Apache 2.0',
    keywords='troposphere troposphere-ext cloud-formation',
    url='https://github.com/llinder/troposphere-ext',
    package_data={},
    packages=find_packages(exclude=['tests', 'tests.*']),
    test_suite='tests',
    install_requires=required,
    setup_requires=dev_required,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: Other/Proprietary License',
        'Programming Language :: Python',
        'Topic :: System :: System Administration'
    ]
)
