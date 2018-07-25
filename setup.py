import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()


setuptools.setup(
    name="swisstext",
    version="0.0.1",
    author="Lucy Linder",
    author_email="lucy.derlin@gmail.com",
    description="SwissText: Swiss German Corpus Generator",
    long_description="TODO",
    url="https://gitlab.com/LucyLinder/swisstext-st1",

    packages=setuptools.find_packages(),
    package_data={'': ['*.yaml', '*.pickle']}, # include yaml and pickle from any module
    scripts=['bin/st_scrape', 'bin/st_search'],

    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "beautifulsoup4==4.6.0",
        "bs4==0.0.1",
        "certifi==2018.4.16",
        "chardet==3.0.4",
        "cityhash==0.2.3.post9",
        "click==6.7",
        "idna==2.7",
        "mongoengine==0.15.0",
        "nltk==3.3",
        "numpy==1.14.5",
        "ordered-set==3.0.0",
        "pyaml==17.12.1",
        "pymongo==3.7.0",
        "pytimeparse==1.1.8",
        "PyYAML==3.13",
        "requests==2.19.1",
        "scikit-learn==0.19.1",
        "scipy==1.1.0",
        "six==1.11.0",
        "sklearn==0.0",
        "urllib3==1.23"
    ]
)
