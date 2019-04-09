About this documentation
========================

This documentation was generated using Sphinx:

.. code-block:: bash

    pip install sphinx
    sphinx-quickstart

To bootstrap the autodoc, I used the following command at the root of the docs folder:

.. code-block:: bash

    sphinx-apidoc -f -M -o . ../backend
    sphinx-apidoc -f -M -o . ../mongo

This was really just for bootstrap, don't use it now as it will
override all the documentation...

To **update the documentation**, simply run ``make html`` at the root of the docs folder.

.. note::

    In case the autodoc complains about not finding modules (e.g. ``mongoengine``), it might be because you are not using the sphinx tool from the current virtualenv.

    `Fix <https://stackoverflow.com/a/11382587>`_: run ``vim $(which sphinx)`` and change the shebang (i.e. first line of the file) to ``#!/usr/bin/env python``.

Deploying on github-pages
--------------------------

The ``gh-pages`` branch contains the content of the ``_build`` directory. For the whole things to work:

* add a `.nojekyll` file at the root, so the folders beginning with an underscore will be deployed,
* add the following ``index.html`` at the root, to redirect to the ``html`` folder:

    .. code-block:: html

        <!DOCTYPE html>
            <html>
            <head><meta http-equiv="refresh" content="0; url=./html/index.html" /></head>
            <body></body>
        </html>

Then, just push/deploy the above two files and the content of the html folder. that's it.

.. note::

    Since the _build folder is ignored, it is possible to clone the *gh-pages* branch inside the _build folder:

    .. code-block:: bash

        cd docs/_build
        git clone --single-branch -b gh-pages git@github.com:derlin/swisstext.git .
