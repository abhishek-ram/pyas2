PyAS2
============

.. image:: https://readthedocs.org/projects/pyas2/?version=latest
    :target: http://pyas2.readthedocs.org/en/latest/
    :alt: Latest Docs

``PyAS2`` is an AS2 server/client written in python and built on the django framework. 
The application supports AS2 version 1.2 as defined in the `RFC 4130`_. Our goal is to provide a native 
python library for implementing the AS2 protocol. It supports Python 2.6-2.7.

``PyAS2`` includes a set of django-admin commands that can be used to start the server, send files as 
a client, send asynchronous MDNs and so on. It also has a web based front end interface for
configuring partners and organizations, monitoring message transfers and also initiating new transfers.

Documentation
~~~~~~~~~~~~~

You can find more information in the `documentation`_.

Discussion
~~~~~~~~~~

If you run into bugs, you can file them in our `issue tracker`_.

Contribute
~~~~~~~~~~

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
#. Fork `the repository`_ on GitHub to start making your changes to the **master** branch (or branch off of it).
#. Create your feature branch: `git checkout -b my-new-feature`
#. Commit your changes: `git commit -am 'Add some feature'`
#. Push to the branch: `git push origin my-new-feature`
#. Send a pull request and bug the maintainer until it gets merged and published. :) Make sure to add yourself to AUTHORS_. 

.. _`RFC 4130`: https://www.ietf.org/rfc/rfc4130.txt
.. _`documentation`: http://pyas2.readthedocs.org/en/latest/
.. _`the repository`: http://github.com/abhishek-ram/pyas2
.. _AUTHORS: https://github.com/abhishek-ram/pyas2/blob/master/AUTHORS.rst
.. _`issue tracker`: https://github.com/abhishek-ram/pyas2/issues 
