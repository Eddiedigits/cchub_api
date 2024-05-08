from setuptools import setup, find_packages

setup(
    name='cchub_api',
    version='1.0.0',
    description='A basic API client for the Daktela/CCHub API.',
    author='Paul Ellis',
    author_email='paulellis.de@gmail.com',
    packages=find_packages(),
    install_requires=[
        'php',
        'requests',
    ],
)