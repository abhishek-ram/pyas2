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

    $ python manage.py makemigrations pyas2
    Migrations for 'pyas2':
      0001_initial.py:
        - Create model Log
        - Create model MDN
        - Create model Message
        - Create model Organization
        - Create model Partner
        - Create model Payload
        - Create model PrivateCertificate
        - Create model PublicCertificate
        - Add field encryption_key to partner
        - Add field signature_key to partner
        - Add field encryption_key to organization
        - Add field signature_key to organization
        - Add field organization to message
        - Add field partner to message
        - Add field payload to message
        - Add field message to log
    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: pyas2, admin, contenttypes, auth, sessions
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying auth.0001_initial... OK
      Applying admin.0001_initial... OK
      Applying sessions.0001_initial... OK
      Applying pyas2.0001_initial... DONE
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
    $ python manage.py makemigrations
    Migrations for 'pyas2':
      0012_auto_20151011_1612.py:
        - Add field verify_cert to publiccertificate
        - Alter field mdn_mode on message
        - Alter field as2_name on organization
        - Alter field name on organization
        - Alter field as2_name on partner
        - Alter field cmd_receive on partner
        - Alter field cmd_send on partner
        - Alter field https_ca_cert on partner
        - Alter field name on partner
        - Alter field ca_cert on privatecertificate
        - Alter field certificate on privatecertificate
        - Alter field ca_cert on publiccertificate
        - Alter field certificate on publiccertificate
    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: admin, pyas2, contenttypes, auth, sessions
    Running migrations:
      Applying pyas2.0012_auto_20151011_1612... OK

.. warning::
    If you did not run makemigrations when you intially installed ``pyAS2`` then follow these steps to initialize migrations:

    .. code-block:: console

        $ python manage.py makemigrations pyas2
        Migrations for 'pyas2':
          0001_initial.py:
            - Create model Log
            - Create model MDN
            - Create model Message
            - Create model Organization
            - Create model Partner
            - Create model Payload
            - Create model PrivateCertificate
            - Create model PublicCertificate
            - Add field encryption_key to partner
            - Add field signature_key to partner
            - Add field encryption_key to organization
            - Add field signature_key to organization
            - Add field organization to message
            - Add field partner to message
            - Add field payload to message
            - Add field message to log
        $ python manage.py migrate --fake-initial pyas2
        Operations to perform:
          Apply all migrations: pyas2
        Running migrations:
          Rendering model states... DONE
          Applying pyas2.0001_initial... FAKED
