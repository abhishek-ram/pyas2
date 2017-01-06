Send & Receive Messages 
=======================
We have so far covered all the topics related to configuration of the ``pyAS2`` server. Now we will see how 
to use these configurations to send messages to your trading partners using the AS2 protocol. We can send files
using any of the following techniques:

Send Messages From the Web UI
-----------------------------
The simplest method for sending messages to your trading partner is by using the Web UI. This method is generally used 
for testing the AS2 connection with your trading partner. The steps are as follows:

* Navigate to ``Run->Send Message``.
* Select the sender(Organization), the receiver(Partner) and choose the file to be transmitted.
* Click on ``Send File`` to initiate the file transfer and monitor the transfers at ``Messages->Outbound Messages``.

.. image:: ../images/SendFile1.png 
.. image:: ../images/SendFile2.png

Send Messages From the Command-Line
-----------------------------------
The next method for sending messages involves the ``pyAS2`` admin command ``sendas2message``. The command is invoked 
from the shell prompt and can be used by other applications to invoke an AS2 file transfer. The command usage is
as follows:

.. code-block:: console

    $ python manage.py sendas2message --help
    Usage: python manage.py sendas2message [options] <organization_as2name partner_as2name path_to_payload>

    Send an as2 message to your trading partner

    Options:
      --delete              Delete source file after processing
      -h, --help            show this help message and exit

The mandatory arguments to be passed to the command include ``organization_as2name`` i.e. the AS2 Identifier of this organization, 
``partner_as2name`` i.e. the AS2 Identifier of your trading partner and ``path_to_payload`` the full path to the file to be transmitted. 
The command also lets you set the ``--delete`` option to delete the file once it is begins the transfer. A sample usage of the command:

.. code-block:: console

    $ python manage.py sendas2message p1as2 p2as2 /Users/abhishekram/Downloads/updateInvoice.txt

Send Messages Using the Send-Daemon
-----------------------------------
The last method for sending messages involves the ``pyAS2`` admin command ``runas2daemon``. The command once started in the background
monitors the data directory and when a file is available in a partner's `outbox <data-dir.html#outbox>`__ folder 
then the transfer is initiated for that file. 

.. code-block:: console

    $ python manage.py runas2daemon
    20150915 04:23:37 INFO     : Starting PYAS2 send daemon.
    20150915 04:23:37 INFO     : Process exisitng files in the directory.
    20150915 04:23:37 INFO     : PYAS2 send daemon started started.
    20150915 04:23:37 INFO     : Watching directory /opt/pyapp/djproject/messages/MTSAS2Tst/outbox/pyas2test
    20150915 04:23:37 INFO     : Watching directory /opt/pyapp/djproject/messages/likemindsas2/outbox/pyas2test

The above example runs the admin command in the foreground, however in a production environment it should be started in the background 
and also OS specific configuration should be added to start this process on system startup.

Receive Messages
----------------
In order to receive files from your trading partners they need to post the AS2 message to the URL 
``http://{hostname}:{port}/pyas2/as2receive``. The configuration of the :doc:`Organization <organizations>`, 
:doc:`Partner <partners>` and :doc:`Certificates <certificates>` need to be completed for successfully receiving
messages from your trading partner. Once the message has been received it will be placed in the organizations
`inbox <data-dir.html#inbox>`__ folder.
