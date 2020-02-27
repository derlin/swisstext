import setuptools

# with open('README.md', 'r') as fh:
#     long_description = fh.read()


setuptools.setup(
    name='swisstext_cmd',
    version='0.0.1',
    author='Lucy Linder',
    author_email='lucy.derlin@gmail.com',
    description='SwissText: Swiss German Corpus Generator',
    license='CC BY-NC 4.0',
    long_description='TODO',
    url='https://github.com/derlin/swisstext',

    packages=setuptools.find_packages(),
    package_data={'': ['*.yaml', '*.pickle', '*.txt']},  # include yaml and pickle from any module
    entry_points={
        'console_scripts': [
            'st_scrape = swisstext.cmd.scraping.__main__:main',
            'st_search = swisstext.cmd.searching.__main__:main'
        ]
    },
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: Creative Commons (CC BY-NC 4.0)',
        'Operating System :: OS Independent',
    ),
    install_requires=[
        'swisstext_mongo',  # TODO
        'beautifulsoup4>=4.6.0',
        'requests>=2.20.0',
        'bs4>=0.0.1',
        'pyyaml>=5.1',
        'cityhash>=0.2.3.post9',
        'nltk>=3.3',
        'pytimeparse>=1.1.8',
        'scikit-learn>=0.19.1',
        'regex',
        'click>=6.7',
        'jusText==2.2.0',
        'ftfy'
    ]
)