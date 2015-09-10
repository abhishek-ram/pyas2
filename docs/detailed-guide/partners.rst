Partners
========
Partners in ``pyAS2`` mean all your trading partners with whom you will exchanges messages, i.e. they are the receivers 
when you send messages and the senders when you receivemessages. Partners can be managed from the web UI at ``Configuration->Partners``.
The following screen lists the existing partners and also you gives the option to search them and create new ones. Each
partner is characterised by the following fields:

General Settings
----------------

==================  ==========================================  =========
Field Name          Description                                 Mandatory
==================  ==========================================  =========
``Name``            The descriptive name of the partner.        Yes
``As2 Name``        The as2 identifies for this partner as      Yes
                    communicated by the partner.
``Email Address``   The email address for the partner.          No
``Target Url``      The HTTP/S endpoint of the partner to       Yes
                    which files need to be posted.
``Subject``         The MIME subject header to be sent along    Yes 
                    with the file.
``Content Type``    The content type of the message being       Yes
                    transmitted, can be XML, X12 or EDIFACT.
==================  ==========================================  =========

Authentication Settings
-----------------------
Use these settings if basic authentication has been enabled for the partners AS2 server.

==========================  ==========================================  =========
Field Name                  Description                                 Mandatory
==========================  ==========================================  =========
``Enable Authentication``   Check this option to enable basic AUTH.     No
``Http auth user``          Username to access the partners server.     No
``Http auth pass``          Password to access the partners server.     No 
``HTTPS Local CA Store``    Use this for HTTPS endpoints where the      No
                            partnes SSL certificate cannot be verified
==========================  ==========================================  =========

Security Settings
-----------------

==================  ==========================================  =========
Field Name          Description                                 Mandatory
==================  ==========================================  =========
``Name``            The descriptive name of the organization.   Yes
``As2 Name``        The as2 identifies for this organization,   Yes
                    must be a unique value as it identifies
                    the as2 host.
``Email Address``   The email address for the organization.     No
``Encryption Key``  The ``Private Key`` used for decrypting     Yes
                    incoming messages from trading partners.
``Signature Key``   The ``Private Key`` used to sign outgoing   Yes
                    messages to trading partners
==================  ==========================================  =========

MDN Settings
------------

==================  ==========================================  =========
Field Name          Description                                 Mandatory
==================  ==========================================  =========
``Name``            The descriptive name of the organization.   Yes
``As2 Name``        The as2 identifies for this organization,   Yes
                    must be a unique value as it identifies
                    the as2 host.
``Email Address``   The email address for the organization.     No
``Encryption Key``  The ``Private Key`` used for decrypting     Yes
                    incoming messages from trading partners.
``Signature Key``   The ``Private Key`` used to sign outgoing   Yes
                    messages to trading partners
==================  ==========================================  =========

Advanced Settings
-----------------

==================  ==========================================  =========
Field Name          Description                                 Mandatory
==================  ==========================================  =========
``Name``            The descriptive name of the organization.   Yes
``As2 Name``        The as2 identifies for this organization,   Yes
                    must be a unique value as it identifies
                    the as2 host.
``Email Address``   The email address for the organization.     No
``Encryption Key``  The ``Private Key`` used for decrypting     Yes
                    incoming messages from trading partners.
``Signature Key``   The ``Private Key`` used to sign outgoing   Yes
                    messages to trading partners
==================  ==========================================  =========

