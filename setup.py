#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name='makevalid',
    version='0.1.0',
    packages=['makevalid'],
    install_requires=['shapely>=5.1.0'],
    author='Forrest Williams',
    author_email='forrest.williams@gmail.com',
    url='https://github.com/ftwillms/makevalid',
    description='Using the Shapely module, function to make a geometry valid.',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
