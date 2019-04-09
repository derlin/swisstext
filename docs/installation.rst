Installation
=============

.. warning::

    This project requires **Python 3.6** or above.

The three modules of SwissText are packaged using *setuptools*. Thus, you just need to run:

.. code-block:: bash

    python setup.py install

at the root of the three directories ``mongo``, ``backend`` and ``frontend``. Just ensure that you start with
mongo first, as it is a dependency to the others.


Example: full install on a Linux server
---------------------------------------

This are the steps to install the system in Ubuntu 18.04:

.. code-block:: bash

    # clone the repo
    git clone
    cd swisstext

    # create and activate a new virtualenv (called venv)
    python3 -m venv venv
    source venv/bin/activate

    # install the mongo package
    apt install gcc g++ libdpkg-perl python3-dev # required deps to compile CityHash
    cd mongo
    python setup.py install
    cd ..

    # install the backend
    cd backend
    python setup.py
    cd ..

    # install the frontend
    cd frontend
    python setup.py
    cd ..

Once all that is setup, you should have the commands `st_scrape`, `st_search` and `st_frontend` available.

Installation on MacOS
----------------------

The same intallation steps should work on Mac. Common troubles include:

- error installing ``sklearn``: in this case, try using python 3.6
- error installing ``CityHash``: I personnally got troubles with GCC not able to find the header ``<utility>``... I found the answer `here <https://stackoverflow.com/a/33988190>`_. Hence, the solution is to export ``MACOSX_DEPLOYMENT_TARGET=10.9`` before running ``setup.py``.
