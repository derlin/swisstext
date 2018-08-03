import setuptools
from os import path

with open(path.join(path.dirname(path.realpath(__file__)), 'README.md'), "r") as fh:
    long_description = fh.read()

from sphinx.setup_command import BuildDoc

cmdclass = {'build_sphinx': BuildDoc}

name = 'swisstext_mongo'
version = '0.0.1'
release = version

setuptools.setup(
    name=name,
    version=version,
    author="Lucy Linder",
    author_email="lucy.derlin@gmail.com",
    license='Apache License 2.0',
    description="SwissText common MongoEngine schemas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/LucyLinder/swisstext-st1",

    packages=setuptools.find_packages(),

    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "mongoengine==0.15.0",
    ],
    # these are optional and override conf.py settings
    command_options={
        'build_sphinx': {
            'version': ('setup.py', version),
            'release': ('setup.py', release),
            'build_dir': ('setup.py', 'docs/_build')
        },
    }
)
