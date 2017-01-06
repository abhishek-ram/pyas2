Admin Commands
==============
``pyAS2`` provides a set of Django ``manage.py`` admin commands that perform various functions. We have 
already seen the usage of some of these commands in the previous sections. Let us now go through the list 
of available commands:

runas2server
------------
The ``runas2server`` command starts the AS2 server which includes both the web UI and the AS2 receiver. 
The command does not take any arguments. The command should be started in the background and also a 
schedule should be added to run the command on system startup.

runas2daemon
------------
The ``runas2daemon`` command starts the directory monitoring process. The process monitors all the partner inbox 
folders and triggers a file transfer when file becomes available. The command should be started in the background and also a 
schedule should be added to run the command on system startup. The process needs to be restarted when a new 
partner is created so that its inbox can be added to the monitored directory list. 

sendas2message
--------------
The ``sendas2message`` command triggers a file transfer, it takes the mandatory arguments organization id, partner id and 
the full path to the file to be transferred. The command can be used by other applications to integrate with ``pyAS2``.

sendasyncmdn
------------
The ``sendasyncmdn`` command performs two functions; it sends asynchronous MDNs for messages received from your partners and 
also checks if we have received asynchronous MDNs for sent messages so that the message status can be updated appropriately. 
The command does not take any arguments and should be run on a repeating schedule.

retryfailedas2comms
-------------------
The ``retryfailedas2comms`` command checks for any messages that have been set for retries and then retriggers the transfer 
for these messages. The command does not take any arguments and should be run on a repeating schedule.

cleanas2server
--------------
The ``cleanas2server`` command is a maintenance command and it deletes all DB objects, logs and files older that the ``MAXARCHDAYS``
setting. It is recommended to run this command once a day using cron or windows scheduler.
