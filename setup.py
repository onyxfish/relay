#!/usr/bin/env python

from setuptools import setup

setup(
    name='relay',
    version='0.0.9',
    description='Meta-magical SSH tunnels for remote developers behind firewalls.',
    long_description=open('README.rst').read(),
    author='Christopher Groskopf',
    author_email='staringmonkey@gmail.com',
    url='http://blog.apps.npr.org/',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ],
    py_modules = [
        'relay'
    ],
    entry_points = {
        'console_scripts': [
            'relay = relay:_main'
        ]
    },
    install_requires = [
        'paramiko>=1.1.0'
    ]
)
