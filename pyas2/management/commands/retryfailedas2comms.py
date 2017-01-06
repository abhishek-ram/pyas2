from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from pyas2 import models
from pyas2 import pyas2init
from pyas2 import as2lib
from pyas2 import as2utils


class Command(BaseCommand):
    help = _(u'Retrying all failed outbound communications')

    def handle(self, *args, **options):
        pyas2init.logger.info(_(u'Retrying all failed outbound messages'))

        # Get the list of all messages with status retry
        failed_msgs = models.Message.objects.filter(status='R', direction='OUT')

        for failed_msg in failed_msgs:
            # Increase the retry count
            if not failed_msg.retries:
                failed_msg.retries = 1
            else:
                failed_msg.retries += failed_msg.retries

            # if max retries has exceeded then mark message status as error
            if failed_msg.retries > pyas2init.gsettings['max_retries']:
                failed_msg.status = 'E'
                models.Log.objects.create(message=failed_msg,
                                          status='E',
                                          text=_(u'Message exceeded maximum retries, marked as error'))
                failed_msg.save()
                continue

            pyas2init.logger.info(_(u'Retrying send of message with ID %s' % failed_msg))
            try:
                # Build and resend the AS2 message
                payload = as2lib.build_message(failed_msg)
                as2lib.send_message(failed_msg, payload)
            except Exception, e:
                # In case of any errors mark message as failed and send email if enabled
                failed_msg.status = 'E'
                models.Log.objects.create(message=failed_msg,
                                          status='E',
                                          text=_(u'Failed to send message, error is %s' % e))
                failed_msg.save()
                # Send mail here
                as2utils.senderrorreport(failed_msg, _(u'Failed to send message, error is %s' % e))
        pyas2init.logger.info(_(u'Successfully processed all failed outbound messages'))
