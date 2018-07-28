import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()


setuptools.setup(
    name="swisstext_mongo",
    version="0.0.1",
    author="Lucy Linder",
    author_email="lucy.derlin@gmail.com",
    description="SwissText: Swiss German Corpus Generator",
    long_description="TODO",
    url="https://gitlab.com/LucyLinder/swisstext-st1",

    packages=setuptools.find_packages(),

    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "mongoengine==0.15.0",
    ]
)
