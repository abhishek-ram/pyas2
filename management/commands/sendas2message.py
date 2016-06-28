from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from pyas2 import models
from pyas2 import as2lib
from pyas2 import as2utils
from pyas2 import pyas2init 
from optparse import make_option
import email.utils
import shutil
import time
import os
import sys


class Command(BaseCommand):
    help = _(u'Send an as2 message to your trading partner')
    args = '<organization_as2name partner_as2name path_to_payload>'

    def add_arguments(self, parser):
        parser.add_argument('organization_as2name', type=str)
        parser.add_argument('partner_as2name', type=str)
        parser.add_argument('path_to_payload', type=str)

        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help=_(u'Delete source file after processing')
        )

    def handle(self, *args, **options):
        # Check if organization and partner exists
        try:
            org = models.Organization.objects.get(as2_name=options['organization_as2name'])
        except models.Organization.DoesNotExist:
            raise CommandError(_(u'Organization "%s" does not exist' % options['organization_as2name']))
        try:
            partner = models.Partner.objects.get(as2_name=options['partner_as2name'])
        except models.Partner.DoesNotExist:
            raise CommandError(_(u'Partner "%s" does not exist' % options['partner_as2name']))

        # Check if file exists and we have the right permissions
        if not os.path.isfile(options['path_to_payload']):
            raise CommandError(_(u'Payload at location "%s" does not exist' % options['path_to_payload']))
        if options['delete'] and not os.access(options['path_to_payload'], os.W_OK):
            raise CommandError('Insufficient file permission for payload %s' % options['path_to_payload'])

        # Copy the file to the store
        output_dir = as2utils.join(pyas2init.gsettings['payload_send_store'], time.strftime('%Y%m%d'))
        as2utils.dirshouldbethere(output_dir)
        outfile = as2utils.join(output_dir, os.path.basename(options['path_to_payload']))
        shutil.copy2(options['path_to_payload'], outfile)

        # Delete original file if option is set
        if options['delete']:
            os.remove(options['path_to_payload'])

        # Create the payload and message objects
        payload = models.Payload.objects.create(name=os.path.basename(options['path_to_payload']),
                                                file=outfile,
                                                content_type=partner.content_type)
        message = models.Message.objects.create(message_id=email.utils.make_msgid().strip('<>'),
                                                partner=partner,
                                                organization=org,
                                                direction='OUT',
                                                status='IP',
                                                payload=payload)

        # Build and send the AS2 message
        try:
            payload = as2lib.build_message(message)
            as2lib.send_message(message, payload)	
        except Exception, e:
            pyas2init.logger.error(_(u'Failed to send message, error:\n%(txt)s') % {'txt': as2utils.txtexc()})
            message.status = 'E'
            models.Log.objects.create(message=message, status='E', text=_(u'Failed to send message, error is %s' % e))
            message.save()

            # Send mail here
            as2utils.senderrorreport(message, _(u'Failed to send message, error is %s' % e))
            sys.exit(2)

        sys.exit(0)
