#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name='makevalid',
    version='0.1.1',
    packages=['makevalid'],
    install_requires=['shapely>=1.3.0', 'rtree>=0.7.0'],
    author='Forrest Williams',
    author_email='forrest.williams@gmail.com',
    url='https://github.com/ftwillms/makevalid',
    description='Using the Shapely module, function to make a polygon valid based on PostGIS ST_MakeValid.',
    license='GPLv2+',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
