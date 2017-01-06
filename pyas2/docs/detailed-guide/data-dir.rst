The Data Directory
==================
The ``Data Directory`` is a file system directory that stores certificates, logs, archives, sent and received files. 
The location of this directory is set to the ``Django`` project folder by default. We can also change this directory 
by updating the ``DATADIR`` setting in the ``pyAS2`` :doc:`global settings <../configuration>`. The structure of the 
directory is below:

.. code-block:: console

    {DATA DIRECTORY}
    ├── certificates
    │   ├── P1_public.pem
    │   └── P2_private.pem
    ├── logging
    │   ├── cherrypy_error.log
    │   ├── pyas2.log
    │   └── pyas2.log.2015-09-08
    └── messages
        ├── __store
        │   ├── mdn
        │   │   ├── received
        │   │   └── sent
        │   │       ├── 20150908
        │   │       │   ├── 20150908115337.7244.44635@Abhisheks-MacBook-Air.local.mdn
        │   │       │   └── 20150908121942.7244.71894@Abhisheks-MacBook-Air.local.mdn
        │   │       └── 20150913
        │   │           ├── 20150913071324.20065.47671@Abhisheks-MacBook-Air.local.mdn
        │   │           └── 20150913083125.20403.32480@Abhisheks-MacBook-Air.local.mdn
        │   └── payload
        │       ├── received
        │       │   ├── 20150908
        │       │   │   ├── 20150908115458.7255.98107@Abhisheks-MacBook-Air.local
        │       │   │   └── 20150908121933.7343.83150@Abhisheks-MacBook-Air.local
        │       │   └── 20150913
        │       │       ├── 20150913071323.20074.48016@Abhisheks-MacBook-Air.local
        │       │       └── 20150913083125.20475.14667@Abhisheks-MacBook-Air.local
        │       └── sent
        ├── p1as2
        │   └── outbox
        │       └── p2as2
        └── p2as2
            └── inbox
                └── p1as2
                    ├── 20150908115458.7255.98107@Abhisheks-MacBook-Air.local.msg
                    └── 20150913083125.20475.14667@Abhisheks-MacBook-Air.local.msg

certificates
------------
The ``certificates`` directory stores all the ``PEM`` encoded public and private key files.

logging
-------
The ``logging`` directory stores the server error logs and application logs. The server error logs are saved as ``cherrypy_error.log`` 
and the application logs are saved as ``pyas2.log``.

__store
-------
The ``__store`` directory under the ``messages`` directory archives the payloads and MDNs. The ``payloads`` directory saves the 
sent and received files in the corresponding sub-folders  and the ``mdn`` directory also does the same for sent and received MDNs.
The payloads and MDNs in the sent or received folders are further saved under sub-folders for each day named as ``YYYYMMDD``.

inbox
-----
The inbox directory stores files received from your partners. The path of this directory is ``{DATA DIRECTORY}/{ORG AS2 ID}/inbox/{PARTNER AS2 ID}``.
We need to take this location into account when integrating ``pyAS2`` with other applications. 

outbox
------
The outbox folder works in conjecture with the ``send-daemon`` process. The daemon process monitors all the outbox 
folder and will trigger a transfer when a file becomes available. The path of this  directory is ``{DATA DIRECTORY}/{PARTNER AS2 ID}/outbox/{ORG AS2 ID}``. 
