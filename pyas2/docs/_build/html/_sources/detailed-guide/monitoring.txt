Monitoring
==========
``pyAS2`` maintains a log of all inbound and outbound messages exchanged with your trading partners. The logs 
can be accessed from the web UI ``Messages`` menu. The menu has options to list messages, search messages and MDNs.
``pyAS2`` saves message details such as status, message ID, sender, receiver, payload; and MDN details such as message ID, 
original message ID and mode.  

List Messages
-------------
The list of all sent and received messages can be viewed from the web UI at ``Messages->All Messages``. The screen lists 
all messages ordered by timestamp so that the latest message is first on the list. We can further list only inbound messages 
at ``Messages->Inbound Messages`` and outbound messages at ``Messages->Outbound Messages``.


Search Messages
---------------
``pyAS2`` lets you search for messages based on a number of criteria. The search screen can be accessed at ``Messages->Search Messages``. 
The following filter criteria are available:

==================  ==========================================================================
Field Name          Description                               
==================  ==========================================================================
``Datefrom``        Messages processed after this date will be included in the search results. 
``Dateuntil``       Messages processed before this date will be included in the search results. 
``Organization``    Messages that belong to this organization will be included. 
``Partner``         Messages that belong to this partner will be included. 
``Direction``       Filter by the direction of the AS2 message, can be inbound or outbound. 
``Status``          Filter by the status of the AS2 message. 
``Message ID``      Filter by the AS2 message ID of the message.
``Payload Name``    Filter by the file name of the sent/received message. 
==================  ==========================================================================

Search MDNs
-----------
``pyAS2`` also lets you search for MDNs for messages based on a number of criteria. The search screen can be 
accessed at ``Messages->MDNs``. The following filter criteria are available:

==========================  ==========================================================================
Field Name                  Description
==========================  ==========================================================================
``Datefrom``                MDNs processed after this date will be included in the search results.
``Dateuntil``               MDNs processed before this date will be included in the search results.
``Organization``            MDNs that belong to this organization will be included.
``Partner``                 MDNs that belong to this partner will be included.
``MDN mode``                Filter by the MDN mode, can be synchronous or asynchronous.
``Status``                  Filter by the status of the MDN.
``MDN Message ID``          Filter by the message ID of the MDN.
``Original Message ID``     Filter by the message ID of the original message for which it is an MDN. 
==========================  ==========================================================================

