Release History
===============

0.4.5 - 2019-03-20
~~~~~~~~~~~~~~~

* Use uuid for filenames and not message id
* More verbose logging of exceptions

0.4.4 - 2019-03-15
~~~~~~~~~~~~~~~

* Increase the length of string fields


0.4.3 - 2018-06-09
~~~~~~~~~~~~~~~

* Send encrypted content as binary data instead of base64

0.4.2 - 2018-06-07
~~~~~~~~~~~~~~~

* Also look for `application/x-pkcs7-signature` when verifying MDN signatures
* Limit size of exception logged to database
* Handle case where Sync MDN does not have a Message ID

0.4.1 - 2018-05-07
~~~~~~~~~~~~~~~

* Also look for `application/x-pkcs7-signature` when verifying signatures

0.4.0 - 2018-01-27
~~~~~~~~~~~~~~~

* Cleaner handling of signature verifications
* Added test cases for sterling b2b integrator message and mdn
* Set `max_length` for file fields to manage long folder names.

0.3.8 - 2018-01-09
~~~~~~~~~~~~~~~~~~

* Give option to download certs from the admin.


0.3.7 - 2018-01-09
~~~~~~~~~~~~~~~~~~

* Use a function to get the certificate upload_to.

0.3.6 - 2018-01-05
~~~~~~~~~~~~~~~~~~

* Added view for downloading certificates from the admin.

0.3.5 - 2017-12-20
~~~~~~~~~~~~~~~~~~

* Renewed the certificates used in the django tests.

0.3.4 - 2017-08-17
~~~~~~~~~~~~~~~~~~

* Add migration to the distribution.

0.3.3 - 2017-04-04
~~~~~~~~~~~~~~~~~~

* Use pagination when listing messages in the GUI, also do not use Datatables.
* Set the request MDN field default value to False.

0.3.2 - 2017-03-07
~~~~~~~~~~~~~~~~~~

* Freeze versions of django and CherryPy in setup.py.

0.3.1 - 2016-10-03
~~~~~~~~~~~~~~~~~~

* Fixed pagination issue where it was showing only 25 messages and mdns.
* Added the admin command cleanas2server for deleting old data and logs.

0.3.0 - 2016-06-28
~~~~~~~~~~~~~~~~~~

* Added django test cases for testing each of the permutations as defined in RFC 4130 Section 2.4.2
* Code now follows the pep-8 standard
* Django admin commands now use argparse instead or optparse

0.2.3 - 2016-04-20
~~~~~~~~~~~~~~~~~~

* Added functionality to customize MDN messages at organization and partner levels.

0.2.2 - 2015-10-12
~~~~~~~~~~~~~~~~~~

* Fixes to take care of changes in Django 1.9.x

0.2.1 - 2015-10-12
~~~~~~~~~~~~~~~~~~

* Updated installation and upgrade documentation.

0.2 - 2015-10-11
~~~~~~~~~~~~~~~~

* Added option to disable verification of public certificates at the time of signature verification.
* Fixed bug in the send daemon.
* Added debug log statements.
* Added some internationlization to model fields.

0.1.2 - 2015-09-07
~~~~~~~~~~~~~~~~~~

* Created readthedocs documentation.
* Fixed bug where inbox and outbox folders were not created on saving partners and orgs.
* Fixed bug where MDN search was failing due to orphaned MDNs.

0.1.1 - 2015-09-04
~~~~~~~~~~~~~~~~~~

* Increased the max length of MODE_CHOICES model field.
* Detect Signature Algorithm from the MIME message for outbound messages.

0.1 - 2015-04-29
~~~~~~~~~~~~~~~~

* Initial release.

.. _`master`: https://github.com/abhishek-ram/pyas2 
