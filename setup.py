#!/usr/bin/env python3
"""
setup.py
Boucher, Govedič, Saowakon, Swanson 2019

Setup script for installation.

"""
import setuptools


with open('README.md') as f:
    long_description = f.read()


setuptools.setup(
    name='damgard-jurik',
    version='0.0.3',
    author='Nicholas Boucher, Luka Govedič, Pasapol Saowakon, Kyle Swanson',
    author_email='swansonk.14@gmail.com',
    description='Homomorphic encryption using the threshold variant of the Damgard-Jurik cryptosystem.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cryptovoting/damgard-jurik',
    packages=setuptools.find_packages(),
    install_requires=[
        'pycryptodomex'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
