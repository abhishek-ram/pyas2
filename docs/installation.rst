Installation
============
Fisrt Install M2Crypto separately following `these instructions <https://gitlab.com/m2crypto/m2crypto/blob/master/INSTALL.rst>`_

Install using ``pip``...

.. code-block:: console

    $ pip install pyas2

Create a new ``django`` project

.. code-block:: console

    $ django-admin.py startproject django_pyas2

Add ``pyas2`` to your ``INSTALLED_APPS`` setting, ensure that ``pyas2`` is placed at the top of this list. 

.. code-block:: python

    INSTALLED_APPS = (
        'pyas2',
        ...
    )

Include the pyAS2 URL configuration in your project's ``urls.py``.

.. code-block:: python
  
  from django.conf.urls import include #add only if django version >= 1.9
  url(r'^pyas2/', include('pyas2.urls')),


Run the following commands to complete the installation and start the server.

.. code-block:: console

    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: pyas2, admin, contenttypes, auth, sessions
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying auth.0001_initial... OK
      Applying admin.0001_initial... OK
      Applying admin.0002_logentry_remove_auto_add... OK
      Applying contenttypes.0002_remove_content_type_name... OK
      Applying auth.0002_alter_permission_name_max_length... OK
      Applying auth.0003_alter_user_email_max_length... OK
      Applying auth.0004_alter_user_username_opts... OK
      Applying auth.0005_alter_user_last_login_null... OK
      Applying auth.0006_require_contenttypes_0002... OK
      Applying auth.0007_alter_validators_add_error_messages... OK
      Applying auth.0008_alter_user_username_max_length... OK
      Applying pyas2.0001_initial... OK
      Applying pyas2.0002_partner_compress... OK
      Applying pyas2.0003_auto_20150311_1141... OK
      Applying pyas2.0004_auto_20150311_1258... OK
      Applying pyas2.0005_message_compressed... OK
      Applying pyas2.0006_auto_20150313_0548... OK
      Applying pyas2.0007_auto_20150313_0707... OK
      Applying pyas2.0008_auto_20150317_0450... OK
      Applying pyas2.0009_auto_20150317_1324... OK
      Applying pyas2.0010_auto_20150416_0745... OK
      Applying pyas2.0011_auto_20150427_1029... OK
      Applying pyas2.0012_auto_20151006_0526... OK
      Applying pyas2.0013_auto_20160307_0233... OK
      Applying pyas2.0014_auto_20160420_0515... OK
      Applying pyas2.0015_auto_20160615_0409... OK
      Applying pyas2.0016_auto_20161004_0543... OK
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

Upgrading ``pyAS2``
-------------------
Upgrading to the latest version of ``pyAS2`` is a straight forward procedure. We will use ``pip`` to update the 
package to the latest version and `django's migrations <https://docs.djangoproject.com/en/1.8/topics/migrations/>`_ 
framework to migrate the database to reflect any changes made to the models.

Run the following commands to upgrade to the latest version:

.. code-block:: console

    $ pip install -U pyas2
    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: admin, pyas2, contenttypes, auth, sessions
    Running migrations:
      Applying pyas2.0017_auto_20170404_0730... OK

.. warning::
    A major change has been made to ``pyAS2``, starting version 0.3.4 the migrations are included in the repo so if you are upgrading from an older version you need to fake till the last migration done and then finally do migrations. So suppose you were at 0.3.2 you would follow these steps:
    
    .. code-block:: console

        $ python manage.py migrate --fake pyas2 0016
        Operations to perform:
          Target specific migration: 0016_auto_20161004_0543, from pyas2
        Running migrations:
          Applying pyas2.0002_partner_compress... FAKED
          Applying pyas2.0003_auto_20150311_1141... FAKED
          Applying pyas2.0004_auto_20150311_1258... FAKED
          Applying pyas2.0005_message_compressed... FAKED
          Applying pyas2.0006_auto_20150313_0548... FAKED
          Applying pyas2.0007_auto_20150313_0707... FAKED
          Applying pyas2.0008_auto_20150317_0450... FAKED
          Applying pyas2.0009_auto_20150317_1324... FAKED
          Applying pyas2.0010_auto_20150416_0745... FAKED
          Applying pyas2.0011_auto_20150427_1029... FAKED
          Applying pyas2.0012_auto_20151006_0526... FAKED
          Applying pyas2.0013_auto_20160307_0233... FAKED
          Applying pyas2.0014_auto_20160420_0515... FAKED
          Applying pyas2.0015_auto_20160615_0409... FAKED
          Applying pyas2.0016_auto_20161004_0543... FAKED
        $ python manage.py migrate pyas2
        Operations to perform:
          Apply all migrations: pyas2
        Running migrations:
          Applying pyas2.0017_auto_20170404_0730... OK
