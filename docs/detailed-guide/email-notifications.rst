Email Notifications
===================
We can configure ``pyAS2`` to send email reports in case of errors encountered while sending 
or receiving AS2 messages with your trading partner. To use this feature just set the relevent information 
in your `project's settings.py <https://docs.djangoproject.com/en/1.8/ref/settings/>`_ module:

.. code-block:: python

    MANAGERS = (    #bots will send error reports to the MANAGERS
        ('name_manager', 'myemailaddress@gmail'),
        )
    EMAIL_HOST = 'smtp.gmail.com'             #Default: 'localhost'
    EMAIL_PORT = '587'             #Default: 25
    EMAIL_USE_TLS = True       #Default: False
    EMAIL_HOST_USER = 'username'        #Default: ''. Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won't attempt authentication.
    EMAIL_HOST_PASSWORD = '*******'    #Default: ''. PASSWORD to use for the SMTP server defined in EMAIL_HOST. If empty, Django won't attempt authentication.
    SERVER_EMAIL = 'botserrors@gmail.com'           #Sender of bots error reports. Default: 'root@localhost'
    EMAIL_SUBJECT_PREFIX = ''   #This is prepended on email subject.
