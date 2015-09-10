Quickstart Guide
================

Now that we have completed installation and configuration of pyAS2, we are ready to start tranferring files.

Let's get started by sending a signed and encrypted file from one pyAS2 server ``P1`` 
to another pyAS2 server ``P2``. Do note that these two are seperate installations of pyAS2.

Installing the Servers
----------------------
Create a django project called ``P1`` and follow the :doc:`installation guide <installation>` 
and run ``python manage.py runas2server`` to start ``P1`` at http://localhost:8080/pyas2/

.. image:: images/P1_Home.png

Create one more django project called ``P2`` and follow the same installations instructions, 
however now we will need to change the pyAS2 port as ``P1`` is using the default port. 
To do this update the port to 8081 in the :doc:`global settings <configuration>` 
and run ``python manage.py runas2server`` to start ``P2`` at http://localhost:8081/pyas2/

.. image:: images/P2_Home.png

Creating the certificates
-------------------------
We need to generate a Public and Private key pair each for the two servers. ``P1`` uses its private key 
to sign the message which is verified by ``P2`` using ``P1's`` publuc key. ``P1`` uses the ``P2's`` public key 
to encrypt the message which is decrypted by ``P2`` using its private key.

To generate the public and private keypair use the below commands

.. code-block:: console

    $ openssl req -x509 -newkey rsa:2048 -keyout P1_private.pem -out P1_public.pem -days 365 
    $ cat P1_public.pem >> P1_private.pem
    $ openssl req -x509 -newkey rsa:2048 -keyout P2_private.pem -out P2_public.pem -days 365
    $ cat P2_public.pem >> P2_private.pem

Configure P1
------------
``P1`` needs to be configured before it can start sending files, open the web UI and follow these instructions:

* Navigate to ``Configuration->Private Certificates->Add private certifcate``.
* Choose the file ``P1_private.pem`` in the **certificate** field, enter the passphrase and save the Private Certificate. 
* Next navigate to ``Configuration->Public Certificates->Add public certifcate``.
* Choose the file ``P2_public.pem`` in the **certificate** field and save the Public Certificate.
* Now navigate to ``Configuration->Organization->Add organization``.
* Set **Name** to ``P1``, **As2 Name** to ``p1as2`` and set the **Signature** and **Encryption** keys to ``P1_private.pem`` and save the Organization.
* Next navigate to ``Configuration->Partner->Add partner``.
* Set **Name** to ``P2``, **As2 Name** to ``p2as2`` and **Target url** to ``http://localhost:8081/pyas2/as2receive``
* Under security settings set **Encrypt Message** to ``3des``, **Sign Message** to ``SHA-1``, **Signature** and **Encryption** keys to ``P2_public.pem``.
* Under MDN settings set **MDN mode** to ``Synchronous`` and **Request Signed MDN** to ``SHA-1``.
* Save the partner to complete the configuration.

Configure P2
------------
``P2`` needs to be configured before it can start receiving files, open the web UI and follow these instructions:

* Navigate to ``Configuration->Private Certificates->Add private certifcate``.
* Choose the file ``P2_private.pem`` in the **certificate** field, enter the passphrase and save the Private Certificate.
* Next navigate to ``Configuration->Public Certificates->Add public certifcate``.
* Choose the file ``P1_public.pem`` in the **certificate** field and save the Public Certificate.
* Now navigate to ``Configuration->Organization->Add organization``.
* Set **Name** to ``P2``, **As2 Name** to ``p2as2`` and set the **Signature** and **Encryption** keys to ``P2_private.pem`` and save the Organization.
* Next navigate to ``Configuration->Partner->Add partner``.
* Set **Name** to ``P1``, **As2 Name** to ``p1as2`` and **Target url** to ``http://localhost:8080/pyas2/as2receive``
* Under security settings set **Encrypt Message** to ``3des``, **Sign Message** to ``SHA-1``, **Signature** and **Encryption** keys to ``P1_public.pem``.
* Under MDN settings set **MDN mode** to ``Synchronous`` and **Request Signed MDN** to ``SHA-1``.
* Save the partner to complete the configuration.

Send a File
-----------
We are now read to send a file from ``P1`` to ``P2``, to do so follow these steps:

* Open the ``P1`` web UI and navigate to ``Run->Send Message``.
* Select the Organization as ``p1as2(P1)`` and Partner as ``p2as2(P2)``.
* Now select the file to send and click ``Send File``.
* The status of the file transfer can be viewed at ``Messages->All Messages``.
* Once file transfer is completed you will a green tick in the status column.

.. image:: images/P1_SendFile.png

* We will also see a similar entry in the web UI of ``P2``.

.. image:: images/P2_SendFile.png

* We can see basic information on this screen such as Partner, Organization, Message ID and MDN.
* We can als view the MDN/Payload by clicking on the respective links.

Conclusion
----------
We have successfully demonstrated the core functionality of ``pyAS2`` i.e. sending files from one system to another using
the AS2 protocol. For a more detailed overview of all its functionlity do go through the :doc:`detailed documentation <configuration>`. 
