import logging
import os
import sys
from django.conf import settings
from pyas2 import as2utils

# Declare global variables
gsettings = {}
logger = None
convertini2logger = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
    'STARTINFO': 25
}


def initialize():
    """ Function initializes the global variables for pyAS2 """

    global gsettings
    pyas2_settings = {}
    if hasattr(settings, 'PYAS2'):
        pyas2_settings = settings.PYAS2
    if not gsettings:
        gsettings['environment'] = pyas2_settings.get('ENVIRONMENT', 'production')
        gsettings['port'] = pyas2_settings.get('PORT', 8080)
        gsettings['ssl_certificate'] = pyas2_settings.get('SSLCERTIFICATE', None)
        gsettings['ssl_private_key'] = pyas2_settings.get('SSLPRIVATEKEY', None)
        gsettings['environment_text'] = pyas2_settings.get('ENVIRONMENTTEXT', 'Production')
        gsettings['environment_text_color'] = pyas2_settings.get('ENVIRONMENTTEXTCOLOR', 'Black')
        gsettings['root_dir'] = settings.BASE_DIR
        gsettings['python_path'] = pyas2_settings.get('PYTHONPATH', sys.executable)
        gsettings['managepy_path'] = as2utils.join(settings.BASE_DIR, 'manage.py')
        gsettings['daemon_port'] = pyas2_settings.get('DAEMONPORT', 16388)
        if pyas2_settings.get('DATADIR') and os.path.isdir(pyas2_settings.get('DATADIR')):
            gsettings['root_dir'] = pyas2_settings.get('DATADIR')
        gsettings['payload_receive_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'payload',
                                                           'received')
        gsettings['payload_send_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'payload', 'sent')
        gsettings['mdn_receive_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'mdn', 'received')
        gsettings['mdn_send_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'mdn', 'sent')
        gsettings['log_dir'] = as2utils.join(gsettings['root_dir'], 'logging')
        for sett in ['payload_receive_store', 'payload_send_store', 'mdn_receive_store', 'mdn_send_store', 'log_dir']:
            as2utils.dirshouldbethere(gsettings[sett])
        gsettings['log_level'] = pyas2_settings.get('LOGLEVEL', 'INFO')
        gsettings['log_console'] = pyas2_settings.get('LOGCONSOLE', True)
        gsettings['log_console_level'] = pyas2_settings.get('LOGCONSOLELEVEL', 'STARTINFO')
        gsettings['max_retries'] = pyas2_settings.get('MAXRETRIES', 30)
        gsettings['mdn_url'] = pyas2_settings.get('MDNURL', 'http://localhost:8080/pyas2/as2receive')
        gsettings['async_mdn_wait'] = pyas2_settings.get('ASYNCMDNWAIT', 30)
        gsettings['max_arch_days'] = pyas2_settings.get('MAXARCHDAYS', 30)
        gsettings['minDate'] = 0 - gsettings['max_arch_days']


def initserverlogging(logname):
    # initialise file logging
    global logger
    logger = logging.getLogger(logname)
    logger.setLevel(convertini2logger[gsettings['log_level']])
    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(gsettings['log_dir'], logname + '.log'),
                                                        when='midnight', backupCount=10)
    fileformat = logging.Formatter("%(asctime)s %(levelname)-9s: %(message)s", '%Y%m%d %H:%M:%S')
    handler.setFormatter(fileformat)
    logger.addHandler(handler)
    # initialise console/screen logging
    if gsettings['log_console']:
        console = logging.StreamHandler()
        console.setLevel(convertini2logger[gsettings['log_console_level']])
        consoleformat = logging.Formatter("%(asctime)s %(levelname)-9s: %(message)s", '%Y%m%d %H:%M:%S')
        console.setFormatter(consoleformat)  # add formatter to console
        logger.addHandler(console)  # add console to logger
    return logger
