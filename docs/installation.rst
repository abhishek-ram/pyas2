Installation
============
Install using ``pip``...

.. code-block:: console

    $ pip install pyas2

Create a new ``django`` project

.. code-block:: console

    $ django-admin.py startproject django_pyas2

Add ``pyas2`` to your ``INSTALLED_APPS`` setting, ensure that ``pyas2`` is placed above ``django.contrib.admin`` as we are overriding the admin templates.

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'pyas2',
    )

Include the pyAS2 URLconf in your project urls.py.

.. code-block:: python

  url(r'^pyas2/', include('pyas2.urls')),
  
Run the following commands to complete the installation and start the server.

.. code-block:: console

    $ python manage.py migrate
    $ python manage.py createsuperuser
    $ python manage.py runas2server 

The server should now be available at http://localhost:8080/pyas2/

Configuration
-------------
