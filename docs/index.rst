.. pyAS2 documentation master file, created by
   sphinx-quickstart on Sat Sep  5 15:03:49 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ``pyAS2's`` documentation!
=====================================

``pyAS2`` is an AS2 server/client written in python and built on the django framework.
The application supports AS2 version 1.2 as defined in the `RFC 4130`_. Our goal is to 
provide a native python library for implementing the AS2 protocol. It supports Python 2.6-2.7.

The application includes a server for receiving files from partners,  a front-end web interface for 
configuraton and monitoring, a set of ``django-admin`` commands that serves as a client 
for sending messages, asynchronous MDNs and a daemon process that monitors directories 
and sends files to partners when they are placed in the partner's watched directory.

Features
--------

* Technical

    * Asyncronous and syncronous MDN
    * Partner and Organization management
    * Digital signatures
    * Message encryption
    * Secure transport (SSL)
    * Support for SSL client authentication
    * System task to auto clear old log entries
    * Data compression (AS2 1.1)
    * Multinational support: Uses Django's internationalization feature

* Integration

    * Easy integration to existing systems, using a partner based file system interface
    * Daemon Process picks up data from directories when it becomes available
    * Message post processing (scripting on receipt)

* Monitoring

    * Web interface for transaction monitoring
    * Email event notification

* The following encryption algorithms are supported:

    * Triple DES
    * DES
    * RC2-40
    * AES-128
    * AES-192
    * AES-256
    
* The following hash algorithms are supported:

    * SHA-1

Dependencies
------------
* Python (2.6.5+, 2.7+)
* Django (1.7+)
* m2crypto (This is dependent on openssl, which will need to be insatalled seperately in case it is absent.)
* requests
* pyasn1
* cherrypy (Optional if you want to run server using management command runas2server)
* pyinotify on \*nix (Optional for using the send daemon)
* Python for Windows extensions (pywin) for windows (Optional for using the send daemon)


Installation
------------
You can install ``pyAS2`` with ``pip``:

.. code-block:: console

    $ pip install pyas2

See :doc:`Installation <installation>` for more information.

Table of Contents:
------------------
.. toctree::
   :maxdepth: 2

   installation
   configuration
   quick-start-guide
   detailed-guide/index
   changelog

.. _`RFC 4130`: https://www.ietf.org/rfc/rfc4130.txt
