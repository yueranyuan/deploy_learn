import os
import re
from setuptools import find_packages
from setuptools import setup

"""
based on setup.py of https://github.com/Lasagne/Lasagne
"""

here = os.path.abspath(os.path.dirname(__file__))
try:
    # obtain version string from __init__.py
    init_py = open(os.path.join(here, 'deploy_learn', '__init__.py')).read()
    version = re.search('__version__ = "(.*)"', init_py).groups()[0]
except Exception:
    version = ''
try:
    # obtain long description from README
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''

install_requires = [
    'numpy',
    'scipy',
    'fabric',
    ]

setup(
    name="deploy_learn",
    version=version,
    description="deploy with parameter search and analyze parameters",
    long_description=README,
    keywords="",
    author="Yueran Yuan",
    #url="https://github.com/",
    license="MIT",
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    install_requires=install_requires,
    )
