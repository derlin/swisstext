import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()


setuptools.setup(
    name="swisstext_alswiki",
    version="0.0.1",
    author="Lucy Linder",
    author_email="lucy.derlin@gmail.com",
    description="SwissText: Swiss German Corpus Generator",
    license='Apache License 2.0',
    long_description="TODO",
    url="https://github.com/derlin/swisstext",

    packages=setuptools.find_packages(),
    package_data={'': ['*.yaml', '*.pickle']},  # include yaml and pickle from any module
    entry_points={
        'console_scripts': [
            'st_alswiki = swisstext.alswiki.__main__:main'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Creative Commons (CC BY-NC 4.0)",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "swisstext_cmd",
        "smart-open>=1.8.1",
        "gensim>=3.7.1"
    ]
)
