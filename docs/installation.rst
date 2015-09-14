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

Include the pyAS2 URL configuration in your project's ``urls.py``.

.. code-block:: python

  url(r'^pyas2/', include('pyas2.urls')),
  
Run the following commands to complete the installation and start the server.

.. code-block:: console

    $ python manage.py migrate
    Operations to perform:
      Synchronize unmigrated apps: pyas2
      Apply all migrations: admin, contenttypes, auth, sessions
    Synchronizing apps without migrations:
      Creating tables...
        Creating table pyas2_privatecertificate
        Creating table pyas2_publiccertificate
        Creating table pyas2_organization
        Creating table pyas2_partner
        Creating table pyas2_message
        Creating table pyas2_payload
        Creating table pyas2_log
        Creating table pyas2_mdn
      Installing custom SQL...
      Installing indexes...
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying auth.0001_initial... OK
      Applying admin.0001_initial... OK
      Applying sessions.0001_initial... OK
    $ python manage.py createsuperuser
    Username (leave blank to use 'abhishekram'): admin
    Email address: admin@domain.com  
    Password: 
    Password (again): 
    Superuser created successfully.
    $ python manage.py runas2server
    20150908 07:14:32 Level 25 : PyAS2 server running at port: "8080".
    20150908 07:14:32 Level 25 : PyAS2 server uses plain http (no ssl). 

The ``pyAS2`` server is now up and running, the web UI for configuration and monitoring can be accessed at 
``http://{hostname}:8080/pyas2/`` and the endpoint for receiving AS2 messages from your partners will be at
``http://{hostname}:8080/pyas2/as2receive`` 
