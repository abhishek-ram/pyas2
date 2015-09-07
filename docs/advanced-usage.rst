Advanced Usage
==============

Now that we have completed installation and configuration of pyAS2 we are ready to start tranferring files.

pyAS2 provides a set of management commands:

To start the AS2 server, run the command `python manage.py runas2server`.
The server frontend will now be accessible at http://127.0.0.1:8080/pyas2/ and can be used to monitor messages and create partners, organizations ...

Messages from your partners can be receieved at http://127.0.0.1:8080/pyas2/as2receive, so this is the link they need to post to for sending messages to you.

To start the AS2 send daemon, run the command `python manage.py runas2daemon`.
This daemon process monitors the outbox folder for each partner and when file is available then it triggers a file transfer to the partner.

To send pending asynchronous MDNs requested by your partners, run the command `python manage.py sendasyncmdn`.

To retry failed as2 communications, run the command `python manage.py retryfailedas2comms`.
Please note that this only retires those outbound messages that failed due to HTTP transmission issues.

