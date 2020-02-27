import setuptools
from os import path

with open(path.join(path.dirname(path.realpath(__file__)), 'README.md'), 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='swisstext_mongo',
    version='0.0.1',
    author='Lucy Linder',
    author_email='lucy.derlin@gmail.com',
    license='CC BY-NC 4.0',
    description='SwissText common MongoEngine schemas',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/derlin/swisstext',

    packages=setuptools.find_packages(),

    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: Creative Commons (CC BY-NC 4.0)',
        'Operating System :: OS Independent',
    ),
    install_requires=[
        'mongoengine<0.19,>=0.18',
    ],
)