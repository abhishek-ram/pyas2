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
The next method for sending messages uses the ``pyAS2`` admin command ``sendas2message``. The command is invoked 
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
The last method for sending messagess used the ``pyAS2`` daemon process ``runas2daemon``. The daemon process once started in the background
monitors the data directory and when a file is avaialble in a partner's outbox folder then the tranfer is inititated for that file. 


Receive Messages
----------------
