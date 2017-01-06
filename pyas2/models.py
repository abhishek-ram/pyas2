from django.db import models
from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from pyas2 import pyas2init
from pyas2 import as2utils
import os


# Initialize the pyas2 settings and loggers
pyas2init.initialize()
pyas2init.initserverlogging('pyas2')

# Set default entry for selects
DEFAULT_ENTRY = ('', "---------")

# Set the storage directory for certificates
upload_storage = FileSystemStorage(location=pyas2init.gsettings['root_dir'], base_url='/pyas2')


class PrivateCertificate(models.Model):
    certificate = models.FileField(upload_to='certificates', storage=upload_storage)
    ca_cert = models.FileField(upload_to='certificates', storage=upload_storage, verbose_name=_('Local CA Store'),
                               null=True, blank=True)
    certificate_passphrase = models.CharField(max_length=100)

    def __str__(self):
        return os.path.basename(self.certificate.name)


class PublicCertificate(models.Model):
    certificate = models.FileField(upload_to='certificates', storage=upload_storage)
    ca_cert = models.FileField(upload_to='certificates', storage=upload_storage, verbose_name=_('Local CA Store'),
                               null=True, blank=True)
    verify_cert = models.BooleanField(verbose_name=_('Verify Certificate'), default=True,
                                      help_text=_('Uncheck this option to disable certificate verification.'))

    def __str__(self):
        return os.path.basename(self.certificate.name)


class Organization(models.Model):
    name = models.CharField(verbose_name=_('Organization Name'), max_length=100)
    as2_name = models.CharField(verbose_name=_('AS2 Identifier'), max_length=100, primary_key=True)
    email_address = models.EmailField(null=True, blank=True)
    encryption_key = models.ForeignKey(PrivateCertificate, related_name='enc_org', null=True, blank=True)
    signature_key = models.ForeignKey(PrivateCertificate, related_name='sign_org', null=True, blank=True)
    confirmation_message = models.CharField(
        verbose_name=_('Confirmation Message'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('Use this field to send a customized message in the MDN Confirmations for this Organization')
    )

    def __str__(self):
        return self.name


class Partner(models.Model):
    CONTENT_TYPE_CHOICES = (
        ('application/EDI-X12', 'application/EDI-X12'),
        ('application/EDIFACT', 'application/EDIFACT'),
        ('application/edi-consent', 'application/edi-consent'),
        ('application/XML', 'application/XML'),
    )
    ENCRYPT_ALG_CHOICES = (
        ('des_ede3_cbc', '3DES'),
        ('des_cbc', 'DES'),
        ('aes_128_cbc', 'AES-128'),
        ('aes_192_cbc', 'AES-192'),
        ('aes_256_cbc', 'AES-256'),
        ('rc2_40_cbc', 'RC2-40'),
    )
    SIGN_ALG_CHOICES = (
        ('sha1', 'SHA-1'),
    )
    MDN_TYPE_CHOICES = (
        ('SYNC', 'Synchronous'),
        ('ASYNC', 'Asynchronous'),
    )
    confirmation_message = models.CharField(
        verbose_name=_('Confirmation Message'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('Use this field to send a customized message in the MDN Confirmations for this Partner')
    )
    name = models.CharField(verbose_name=_('Partner Name'), max_length=100)
    as2_name = models.CharField(verbose_name=_('AS2 Identifier'), max_length=100, primary_key=True)
    email_address = models.EmailField(null=True, blank=True)
    http_auth = models.BooleanField(verbose_name=_('Enable Authentication'), default=False)
    http_auth_user = models.CharField(max_length=100, null=True, blank=True)
    http_auth_pass = models.CharField(max_length=100, null=True, blank=True)
    https_ca_cert = models.FileField(upload_to='certificates', verbose_name=_('HTTPS Local CA Store'),
                                     storage=upload_storage, null=True, blank=True)
    target_url = models.URLField()
    subject = models.CharField(max_length=255, default=_('EDI Message sent using pyas2'))
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPE_CHOICES, default='application/edi-consent')
    compress = models.BooleanField(verbose_name=_('Compress Message'), default=True)
    encryption = models.CharField(max_length=20, verbose_name=_('Encrypt Message'), choices=ENCRYPT_ALG_CHOICES,
                                  null=True, blank=True)
    encryption_key = models.ForeignKey(PublicCertificate, related_name='enc_partner', null=True, blank=True)
    signature = models.CharField(max_length=20, verbose_name=_('Sign Message'), choices=SIGN_ALG_CHOICES, null=True,
                                 blank=True)
    signature_key = models.ForeignKey(PublicCertificate, related_name='sign_partner', null=True, blank=True)
    mdn = models.BooleanField(verbose_name=_('Request MDN'), default=True)
    mdn_mode = models.CharField(max_length=20, choices=MDN_TYPE_CHOICES, null=True, blank=True)
    mdn_sign = models.CharField(max_length=20, verbose_name=_('Request Signed MDN'), choices=SIGN_ALG_CHOICES,
                                null=True, blank=True)
    keep_filename = models.BooleanField(
        verbose_name=_('Keep Original Filename'),
        default=False,
        help_text=_(
            'Use Original Filename to to store file on receipt, use this option'
            ' only if you are sure partner sends unique names')
    )
    cmd_send = models.TextField(
        verbose_name=_('Command on Message Send'),
        null=True,
        blank=True,
        help_text=_(
            'Command executed after successful message send, replacements are $filename, $sender, '
            '$recevier, $messageid and any message header such as $Subject')
    )
    cmd_receive = models.TextField(
        verbose_name=_('Command on Message Receipt'),
        null=True,
        blank=True,
        help_text=_(
            'Command executed after successful message receipt, replacements are $filename, $fullfilename, '
            '$sender, $recevier, $messageid and any message header such as $Subject')
    )

    def __str__(self):
        return self.name


class Message(models.Model):
    DIRECTION_CHOICES = (
        ('IN', _('Inbound')),
        ('OUT', _('Outbound')),
    )
    STATUS_CHOICES = (
        ('S', _('Success')),
        ('E', _('Error')),
        ('W', _('Warning')),
        ('P', _('Pending')),
        ('R', _('Retry')),
        ('IP', _('In Process')),
    )
    MODE_CHOICES = (
        ('SYNC', _('Synchronous')),
        ('ASYNC', _('Asynchronous')),
    )
    # TODO: Create composite key (message_id, organization, partner)
    message_id = models.CharField(max_length=100, primary_key=True)
    headers = models.TextField(null=True)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    adv_status = models.CharField(max_length=255, null=True)
    organization = models.ForeignKey(Organization, null=True)
    partner = models.ForeignKey(Partner, null=True)
    payload = models.OneToOneField(
        'Payload', null=True, related_name='message')
    compressed = models.BooleanField(default=False)
    encrypted = models.BooleanField(default=False)
    signed = models.BooleanField(default=False)
    mdn = models.OneToOneField('MDN', null=True, related_name='omessage')
    mic = models.CharField(max_length=100, null=True)
    mdn_mode = models.CharField(max_length=5, choices=MODE_CHOICES, null=True)
    retries = models.IntegerField(null=True)

    def __str__(self):
        return self.message_id


class Payload(models.Model):
    name = models.CharField(max_length=100)
    content_type = models.CharField(max_length=255)
    file = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Log(models.Model):
    STATUS_CHOICES = (
        ('S', _('Success')),
        ('E', _('Error')),
        ('W', _('Warning')),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    message = models.ForeignKey(Message, related_name='logs')
    text = models.CharField(max_length=255)


class MDN(models.Model):
    STATUS_CHOICES = (
        ('S', _('Sent')),
        ('R', _('Received')),
        ('P', _('Pending')),
    )
    message_id = models.CharField(max_length=100, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    file = models.CharField(max_length=255)
    headers = models.TextField(null=True)
    return_url = models.URLField(null=True)
    signed = models.BooleanField(default=False)

    def __str__(self):
        return self.message_id


def getorganizations():
    return [DEFAULT_ENTRY] + [(l, '%s (%s)' % (l, n)) for (l, n) in
                              Organization.objects.values_list('as2_name', 'name')]


def getpartners():
    return [DEFAULT_ENTRY] + [(l, '%s (%s)' % (l, n)) for (l, n) in Partner.objects.values_list('as2_name', 'name')]


@receiver(post_save, sender=Organization)
def check_odirs(sender, instance, created, **kwargs):
    partners = Partner.objects.all()
    for partner in partners:
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', instance.as2_name, 'inbox', partner.as2_name))
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', partner.as2_name, 'outbox', instance.as2_name))


@receiver(post_save, sender=Partner)
def check_pdirs(sender, instance, created, **kwargs):
    orgs = Organization.objects.all()
    for org in orgs:
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', org.as2_name, 'inbox', instance.as2_name))
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', instance.as2_name, 'outbox', org.as2_name))


def update_dirs():
    partners = Partner.objects.all()
    orgs = Organization.objects.all()
    for partner in partners:
        for org in orgs:
            as2utils.dirshouldbethere(
                as2utils.join(pyas2init.gsettings['root_dir'], 'messages', org.as2_name, 'inbox', partner.as2_name))
    for org in orgs:
        for partner in partners:
            as2utils.dirshouldbethere(
                as2utils.join(pyas2init.gsettings['root_dir'], 'messages', partner.as2_name, 'outbox', org.as2_name))
