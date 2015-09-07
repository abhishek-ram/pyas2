.. PyAS2 documentation master file, created by
   sphinx-quickstart on Sat Sep  5 15:03:49 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ``PyAS2's`` documentation!
=====================================

``PyAS2`` is an AS2 server/client written in python and built on the django framework. The application supports AS2 version 1.2 as defined in the RFC 4130.

Dependencies
------------
* Python (2.6.5+, 2.7)
* Django (1.7, 1.8)
* m2crypto (This is dependent on openssl, which will need to be insatalled seperately in case it is absent.)
* requests
* pyasn1
* cherrypy (Optional if you want to run server using management command runas2server)
* pyinotify on \*nix (Optional for using the send daemon)
* Python for Windows extensions (pywin) for windows (Optional for using the send daemon)


Installation
------------
You can install ``PyAS2`` with ``pip``:

.. code-block:: console

    $ pip install pyas2

See :doc:`Installation <installation>` for more information.

Table of Contents:
------------------
.. toctree::
   :maxdepth: 2

   installation
   quick-start-guide
   advanced-usage
   changelog

