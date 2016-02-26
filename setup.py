#coding: UTF-8
'''
Created on 2016/02/08

@author: _
'''
from distutils.core import setup

from setuptools import find_packages


setup(
    name = "pyth2",
    version = "0.0.2",
    description = "Python Utilities",
    author = "_",
    author_email = "_@_.jp",
    license = "MIT",
    packages = find_packages(where = "src"),
    package_dir = {"": "src"},
    install_requires = ())