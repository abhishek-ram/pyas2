# PyAS2

Pyas2 is an AS2 server/client written in python and built on the django framework. The application supports AS2 version 1.2 as defined in the RFC 4130.

# Requirements

* Python (2.6.5+, 2.7)
* Django (1.7, 1.8)
* m2crypto
* requests
* pyasn1
* pyinotify on *nix (Optional for using the send daemon)
* Python for Windows extensions (pywin) for windows (Optional for using the send daemon)

# Installation

Install using `pip`...

    pip install pyas2

Add `'pyas2'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'pyas2',
    )
Ensure that pyas2 is placed above 'django.contrib.admin' as we are overriding the admin templates.

Include the pyAS2 URLconf in your project urls.py like this::

  `url(r'^pyas2/', include('pyas2.urls')),`
  
Run `python manage.py migrate` to create the pyas2 models and `python manage.py createsuperuser` to create an admin user.

We can also configure a couple of settings for our API, this is not mandartory.
Add the following to your `settings.py` module:
```python
PYAS2 = {
    'ENVIRONMENT' : 'production', ## as2 server in development or production. default is production
    'PORT' : 8888, ## port the as2 server listens. default is 8080
    ## Specift in order to enable ssl/https for the as2 server:
    'SSLCERTIFICATE' : '/path_to_cert/server_cert.pem', 
    'SSLPRIVATEKEY' : '/path_to_cert/server_privkey.pem',
    'ROOTDIR' : '/path_to_datadir/data', ## Full path to the base directory for storing files, logs ... 
    'PYTHONPATH' : '/path_to_python/python', ## Path to the python executable, neccessary with virtual environments
    'ENVIRONMENTTEXT' : 'BETA',  #environment_text: text displayed on right of the logo. Useful to indicate different environments.
    'ENVIRONMENTTEXTCOLOR' : 'Yellow', ## environment_text_color: Use HTML valid "color name" or #RGB values. Default: Black (#000000)
    'LOGLEVEL' : 'DEBUG', ## level for logging to log file. Values: DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL. Default: INFO
    'LOGCONSOLE' : True, ## console logging on (True) or off (False); default is True.
    'LOGCONSOLELEVEL' : 'DEBUG', # level for logging to console/screen. Values: DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL. Default: STARTINFO  
    'MAXRETRIES': 5,    # Maximum number of retries for failed outgoing messages, defaule is 10
    'MDNURL' : 'https://192.168.1.115:8888/pyas2/as2receive', # Return url for receiving async MDNs from partners
    'ASYNCMDNWAIT' : 30, # Maximum wait time in minutes for asyn MDNs from partner, post which message will be marked as failed
    'MAXARCHDAYS' : 30, # number of days files and messages are kept in storage; default is 30
}
```
## Usage

Now that we have completed installation and configuration of pyAS2 we are ready to start tranferring files.

pyAS2 provides a set of management commands:

To start the AS2 server, run the command `python manage.py runas2server`.
The server will now be accessible at http://127.0.0.1:8080/pyas2/

To start the AS2 send daemon, run the command `python manage.py runas2daemon`.
This daemon process monitors the outbox folder for each partner and when file is available then it triggers a file transfer to the partner.

To send pending asynchronous MDNs requested by your partners, run the command `python manage.py sendasyncmdn`.

To retry failed as2 communications, run the command `python manage.py retryfailedas2comms`.
Please note that this only retires those outbound messages that failed due to HTTP transmission issues.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## License

GNU GENERAL PUBLIC LICENSE
                       Version 2, June 1991

 Copyright (C) 1989, 1991 Free Software Foundation, Inc., <http://fsf.org/>
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
