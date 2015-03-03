from django.core.management.base import BaseCommand, CommandError
from pyas2 import models
from pyas2 import as2lib
from email.parser import HeaderParser
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import email.utils
import os

class Command(BaseCommand):
    help = 'Send all pending asynchronous mdns to your trading partners'

    def handle(self, *args, **options):
	time_threshold = timezone.now() - timedelta(hours=1)
	pending_mdns = models.MDN.objects.filter(status='P', timestamp__gt=time_threshold)
	for pending_mdn in pending_mdns:
	    hparser = HeaderParser()
	    mdn_headers = hparser.parsestr(pending_mdn.headers)    
	    try:
		auth = None
		if pending_mdn.omessage.partner and pending_mdn.omessage.partner.http_auth:
		    auth = (pending_mdn.omessage.partner.http_auth_user, pending_mdn.omessage.partner.http_auth_pass)
		with open(pending_mdn.file,'rb') as payload:
		    requests.post(pending_mdn.return_url, auth=auth, headers = dict(mdn_headers.items()), data = payload)
		pending_mdn.status = 'S'
		models.Log.objects.create(message=pending_mdn.omessage, status='S', text='Successfully sent asynchrous mdn to partner')	
	    except Exception,e:
		models.Log.objects.create(message=pending_mdn.omessage, status='S', text='Failed to send asynchrous mdn to partner, error is %s' %e)
	    finally:
		pending_mdn.save()
	self.stdout.write('Successfully processed all pending mdns') 
