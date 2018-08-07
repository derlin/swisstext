import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()


setuptools.setup(
    name="swisstext_frontend",
    version="0.0.1",
    author="Lucy Linder",
    author_email="lucy.derlin@gmail.com",
    description="SwissText Frontend: Swiss German Corpus Generator",
    long_description="TODO",
    url="https://gitlab.com/LucyLinder/swisstext-st1-frontend",

    packages=setuptools.find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'st_frontend = swisstext.frontend.__main__:main'
        ]
    },

    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ),

    install_requires=[
        'Flask==1.0.2',
        'swisstext-mongo==0.0.1',
        'Bootstrap-Flask==1.0.4',
        'Flask-WTF==0.14.2',
        'Flask-Login==0.4.1',
        'flask-mongoengine==0.9.5',
        'cityhash==0.2.3.post9'
    ]
)
