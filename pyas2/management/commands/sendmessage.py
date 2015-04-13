from django.core.management.base import BaseCommand, CommandError
from pyas2 import models
from pyas2 import as2lib
from pyas2 import as2utils
from pyas2 import init 
from optparse import make_option
import email.utils
import shutil
import os 
import traceback
import sys

class Command(BaseCommand):
    help = 'Send an as2 message to your trading partner'
    args = '<organization_as2name partner_as2name path_to_payload>'
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete source file after processing'),
        )
    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError('Insufficient number of arguments specified, please check help for correct usage')
        try:
            org = models.Organization.objects.get(as2_name=args[0])
        except models.Organization.DoesNotExist:
            raise CommandError('Organization "%s" does not exist' % args[0])
        try:
            partner = models.Partner.objects.get(as2_name=args[1])
        except models.Partner.DoesNotExist:
            raise CommandError('Partner "%s" does not exist' % args[1])
        if not os.path.isfile(args[2]):
            raise CommandError('Payload at location "%s" does not exist' % args[2])
        #if not os.access(args[2],os.W_OK):
            #raise CommandError('Insufficient file permission for payload %s' % args[2])
        outfile = as2utils.join(init.gsettings['payload_send_store'], os.path.basename(args[2]))
        shutil.copy2(args[2], outfile)
        if options['delete']:
            os.remove(args[2])
        payload = models.Payload.objects.create(name=os.path.basename(args[2]), file=outfile, content_type=partner.content_type)
        message = models.Message.objects.create(message_id=email.utils.make_msgid().strip('<>'), partner=partner, organization=org, direction='OUT', status='IP', payload=payload)
        try:
            payload = as2lib.build_message(message)
            as2lib.send_message(message, payload)	
        except Exception,e:
            message.status = 'E'
            message.adv_status = 'Failed to send message, error is %s' %e
            models.Log.objects.create(message=message, status='E', text = message.adv_status)
            message.save()	
            sys.exit(2)
    sys.exit(0)
#	self.stdout.write('Processed message "%s"' % args[2]) 
