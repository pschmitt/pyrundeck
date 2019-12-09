#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='pyrundeck',
    version='0.9.7',
    description='Python REST API client for Rundeck 2.6+',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    author='Philipp Schmitt',
    author_email='philipp.schmitt@post.lu',
    url='https://github.com/pschmitt/pyrundeck',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests']
)
