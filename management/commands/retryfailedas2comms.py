from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from pyas2 import models
from pyas2 import pyas2init
from pyas2 import as2lib
from pyas2 import as2utils
from email.parser import HeaderParser
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import email.utils
import os

class Command(BaseCommand):
    help = _(u'Retrying all failed outbound communications')

    def handle(self, *args, **options):
        pyas2init.logger.info(_(u'Retrying all failed outbound messages'))
        failed_msgs = models.Message.objects.filter(status='R',direction='OUT')
        for failed_msg in failed_msgs:
            if not failed_msg.retries:
                failed_msg.retries = 1
            else:
                failed_msg.retries = failed_msg.retries + 1
            if failed_msg.retries > pyas2init.gsettings['max_retries']:
                failed_msg.status = 'E'
                models.Log.objects.create(message=failed_msg, status='E', text = _(u'Message exceeded maximum retries, marked as error'))
                failed_msg.save()
                continue
            pyas2init.logger.info(_(u'Retrying send of message with ID %s'%failed_msg))
            try:
                payload = as2lib.build_message(failed_msg)
                as2lib.send_message(failed_msg,payload)
            except Exception,e:
                failed_msg.status = 'E'
                models.Log.objects.create(message=failed_msg, status='E', text = _(u'Failed to send message, error is %s' %e))
                failed_msg.save()
                ### Send mail here 
                as2utils.sendpyas2errorreport(failed_msg,_(u'Failed to send message, error is %s' %e))
        pyas2init.logger.info(_(u'Successfully processed all failed outbound messages'))
