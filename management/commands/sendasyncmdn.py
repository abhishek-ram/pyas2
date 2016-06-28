from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from pyas2 import models
from pyas2 import pyas2init
from email.parser import HeaderParser
from django.utils import timezone
from datetime import timedelta
import requests


class Command(BaseCommand):
    help = _(u'Send all pending asynchronous mdns to your trading partners')

    def handle(self, *args, **options):
        # First part of script sends asynchronous MDNs for inbound messages received from partners
        # Fetch all the pending asynchronous MDN objects
        pyas2init.logger.info(_(u'Sending all pending asynchronous MDNs'))
        in_pending_mdns = models.MDN.objects.filter(status='P')  # , timestamp__gt=time_threshold) --> why do this?

        for pending_mdn in in_pending_mdns:
            # Parse the MDN headers from text
            header_parser = HeaderParser()
            mdn_headers = header_parser.parsestr(pending_mdn.headers)
            try:
                # Set http basic auth if enabled in the partner profile
                auth = None
                if pending_mdn.omessage.partner and pending_mdn.omessage.partner.http_auth:
                    auth = (pending_mdn.omessage.partner.http_auth_user, pending_mdn.omessage.partner.http_auth_pass)

                # Set the ca cert if given in the partner profile
                verify = True
                if pending_mdn.omessage.partner.https_ca_cert:
                    verify = pending_mdn.omessage.partner.https_ca_cert.path

                # Post the MDN message to the url provided on the original as2 message
                with open(pending_mdn.file, 'rb') as payload:
                    requests.post(pending_mdn.return_url,
                                  auth=auth,
                                  verify=verify,
                                  headers=dict(mdn_headers.items()),
                                  data=payload)
                pending_mdn.status = 'S'
                models.Log.objects.create(message=pending_mdn.omessage,
                                          status='S',
                                          text=_(u'Successfully sent asynchronous mdn to partner'))
            except Exception, e:
                models.Log.objects.create(message=pending_mdn.omessage,
                                          status='E',
                                          text=_(
                                              u'Failed to send asynchronous mdn to partner, error is {0:s}'.format(e)))
            finally:
                pending_mdn.save()

        # Second Part of script checks if MDNs have been received for outbound messages to partners
        pyas2init.logger.info(_(u'Marking messages waiting for MDNs for more than {0:d} minutes'.format(
            pyas2init.gsettings['async_mdn_wait'])))

        # Find all messages waiting MDNs for more than the set async mdn wait time
        time_threshold = timezone.now() - timedelta(minutes=pyas2init.gsettings['async_mdn_wait'])
        out_pending_msgs = models.Message.objects.filter(status='P', direction='OUT', timestamp__lt=time_threshold)

        # Mark these messages as erred
        for pending_msg in out_pending_msgs:
            status_txt = _(u'Failed to receive asynchronous MDN within the threshold limit')
            pending_msg.status = 'E'
            pending_msg.adv_status = status_txt
            models.Log.objects.create(message=pending_msg, status='E', text=status_txt)
            pending_msg.save()

        pyas2init.logger.info(_(u'Successfully processed all pending mdns'))
