Organziations
=============
Organizations in ``pyAS2`` mean the host of the pyAS2 server, i.e. it is the sender when sending messages and the 
receiver when receiving the messages. Organizations can be managed from the web UI at ``Configuration->Organizations``.
The following screen lists the existing organizations and also you gives the option to create new ones. Each
organization is characterised by the following fields:

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
