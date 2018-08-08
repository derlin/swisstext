Usage
======

Running MongoDB
----------------

To run the system, you need **MongoDB** available. The easiest way is to use docker:

.. code-block:: bash

    # get the latest mongodb image
    docker pull mongo:latest

    # create a directory for persisting the database
    mkdir mongodir

    # launch a mongodb container called st-mongo
    docker run -d --name st-mongo -p 27017:27017 -v $(pwd)/mongodir:/data/db mongo

MongoDB is now running.


Running the frontend
---------------------

The easiest way to run the frontend is by calling the ``st_frontend`` script. Use the ``--help`` option for usage.
This will run Flask, but as clearly stated in their documentation, this should be avoided in a real environment.

To launch the frontend in a **production-like** fashion, the one way is to use `gunicon <http://gunicorn.org/>`_:

.. code-block:: bash

    # install gunicorn and its dependencies
    pip install gevent greenlet gunicorn

    # run the frontend using gunicorn (instead of st_frontend)
    # note that the actual port is setup with the gunicorn --bind option
    gunicorn --preload --log-level=info --bind=:80 "swisstext.frontend.server:init_app()"

    # You can also pass parameters to the app through the init_app call. Here is an example:
    gunicorn --preload --log-level=info --bind=:80 \
        "swisstext.frontend.server:init_app(debug=True, mongo_host='192.131.23.10', mongo_port=27000, db='st1')"

Running the backend
--------------------

To run the **backend**, just call the ``st_scrape`` and ``st_search`` scripts.

If you want to customize how the system works, you can do it via a YAML configuration file. Note that
you can use one single file for both scrape and search as options don't clash with one another and no error
is thrown if unknown options are set.


.. seealso::

    :mod:`swisstext.cmd`
        For usage examples