from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from datetime import timedelta
from django.utils import timezone
from pyas2 import models
from pyas2 import pyas2init
import os
import glob


class Command(BaseCommand):
    help = _(u'Automatic maintenance for the AS2 server. '
             u'Cleans up all the old logs, messages and archived files.')

    def handle(self, *args, **options):
        pyas2init.logger.info(_(u'Automatic maintenance process started'))
        max_archive_dt = timezone.now() - timedelta(
            pyas2init.gsettings['max_arch_days'])
        max_archive_ts = int(max_archive_dt.strftime("%s"))

        pyas2init.logger.info(
            _(u'Delete all DB Objects older than max archive days'))
        old_message = models.Message.objects.filter(
            timestamp__lt=max_archive_dt).order_by('timestamp')
        for message in old_message:
            pyas2init.logger.debug(
                _(u'Delete Message {} and all related '
                  u'objects'.format(message)))
            if message.payload:
                message.payload.delete()
            if message.mdn:
                message.mdn.delete()
            message.delete()

        pyas2init.logger.info(
            _(u'Delete all logs older than max archive days'))
        log_folder = os.path.join(pyas2init.gsettings['log_dir'], 'pyas2*')
        for logfile in glob.iglob(log_folder):
            filename = os.path.join(
                pyas2init.gsettings['log_dir'], logfile)
            if os.path.getmtime(filename) < max_archive_ts:
                pyas2init.logger.debug(
                    _(u'Delete Log file {}'.format(filename)))
                os.remove(filename)

        pyas2init.logger.info(
            _(u'Delete all Archive Files older than max archive days'))
        archive_folders = [
            pyas2init.gsettings['payload_send_store'],
            pyas2init.gsettings['payload_receive_store'],
            pyas2init.gsettings['mdn_send_store'],
            pyas2init.gsettings['mdn_receive_store']
        ]
        for archive_folder in archive_folders:
            for (dir_path, dir_names, arch_files) in os.walk(archive_folder):
                if len(arch_files) > 0:
                    for arch_file in arch_files:
                        filename = os.path.join(dir_path, arch_file)
                        if os.path.getmtime(filename) < max_archive_ts:
                            pyas2init.logger.debug(_(u'Delete Archive file '
                                                     u'{}'.format(filename)))
                            os.remove(filename)

                    # Delete the folder if it is empty
                    try:
                        os.rmdir(dir_path)
                        pyas2init.logger.debug(_(u'Delete Empty Archive folder'
                                                 u' {}'.format(dir_path)))
                    except OSError:
                        pass
        pyas2init.logger.info(_(u'Automatic maintenance process completed'))
