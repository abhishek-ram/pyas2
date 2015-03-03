from django.db import models
from pyas2 import init
from pyas2 import as2utils
import os
# Create your models here.

DEFAULT_ENTRY = ('',"---------")
init.initialize()
init.initserverlogging('pyas2')

class PrivateCertificate(models.Model):
    certificate = models.FileField(upload_to=as2utils.join(init.gsettings['root_dir'],'certificates'))
    ca_cert = models.FileField(upload_to=as2utils.join(init.gsettings['root_dir'],'certificates'), null=True, blank=True)
    certificate_passphrase = models.CharField(max_length=100)
    def __str__(self):
        return os.path.basename(self.certificate.name)
   
class PublicCertificate(models.Model):
    certificate = models.FileField(upload_to=as2utils.join(init.gsettings['root_dir'],'certificates'))
    ca_cert = models.FileField(upload_to=as2utils.join(init.gsettings['root_dir'],'certificates'), null=True, blank=True)
    def __str__(self):
        return os.path.basename(self.certificate.name)

class Organization(models.Model):
    name = models.CharField(max_length=100)
    as2_name = models.CharField(max_length=100, primary_key=True)
    email_address = models.EmailField(null=True, blank=True)
    encryption_key = models.ForeignKey(PrivateCertificate, related_name='enc_org', null=True, blank=True) 
    signature_key = models.ForeignKey(PrivateCertificate,related_name='sign_org',null=True, blank=True) 
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
	update_dirs()
        super(Organization,self).save(*args,**kwargs)

class Partner(models.Model):
    CONTENT_TYPE_CHOICES = (
        ('application/EDI-X12', 'application/EDI-X12'),
        ('application/EDIFACT', 'application/EDIFACT'),
        ('application/edi-consent', 'application/edi-consent'),
        ('application/XML', 'application/XML'),
    )
    ENCRYPT_ALG_CHOICES = (
        ('des_ede3_cbc', '3DES'),
        ('des_ede_cbc', 'DES'),
        ('rc2_40_cbc', 'RC2-40'),
        ('rc4', 'RC4-40'),
        ('aes_128_cbc', 'AES-128'),
        ('aes_192_cbc', 'AES-192'),
        ('aes_256_cbc', 'AES-256'),
    ) 
    SIGN_ALG_CHOICES = (
        ('sha1', 'SHA-1'),
    )
    MDN_TYPE_CHOICES = (
        ('SYNC', 'Synchronous'),
        ('ASYNC', 'Asynchronous'),
    )
    name = models.CharField(max_length=100)
    as2_name = models.CharField(max_length=100, primary_key=True)
    http_auth = models.BooleanField(verbose_name='HTTP Authentication', default=False)
    http_auth_user = models.CharField(max_length=100, null=True, blank=True)
    http_auth_pass = models.CharField(max_length=100, null=True, blank=True)
    target_url = models.URLField()
    subject = models.CharField(max_length=255, default='EDI Message sent using pyas2')
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPE_CHOICES, default='application/edi-consent')    
    encryption = models.CharField(max_length=20, choices=ENCRYPT_ALG_CHOICES, null=True, blank=True)
    encryption_key = models.ForeignKey(PublicCertificate,related_name='enc_partner',null=True, blank=True)
    signature = models.CharField(max_length=20, choices=SIGN_ALG_CHOICES, null=True, blank=True)
    signature_key = models.ForeignKey(PublicCertificate,related_name='sign_partner',null=True, blank=True)
    mdn = models.BooleanField(verbose_name='Request MDN', default=True)
    mdn_mode = models.CharField(max_length=20, choices=MDN_TYPE_CHOICES, default='SYNC')
    mdn_sign = models.BooleanField(verbose_name='Request Signed MDN', default=True) 
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
	update_dirs()
	super(Partner,self).save(*args,**kwargs)

class Message(models.Model):
    DIRECTION_CHOICES = (
        ('IN', 'Inbound'),
        ('OUT', 'Outbound'),
    )
    STATUS_CHOICES = (
        ('S', 'Success'),
        ('E', 'Error'),
        ('W', 'Warning'),
        ('P', 'Pending'),
        ('IP', 'In Process'),
    )
    MODE_CHOICES = (
        ('SYNC', 'Synchronous'),
        ('ASYNC', 'Asynchronous'),
    )
    message_id = models.CharField(max_length=100, primary_key=True)
    headers = models.TextField(null=True)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    adv_status = models.CharField(max_length=255, null=True)
    organization = models.ForeignKey(Organization, null=True) 
    partner = models.ForeignKey(Partner, null=True)
    payload = models.OneToOneField('Payload', null=True, related_name='message')
    mdn = models.OneToOneField('MDN', null=True, related_name='omessage')
    mic = models.CharField(max_length=100, null=True)
    mdn_mode = models.CharField(max_length=2, choices=MODE_CHOICES, null=True)
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
        ('S', 'Success'),
        ('E', 'Error'),
        ('W', 'Warning'),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    message = models.ForeignKey(Message)
    text = models.CharField(max_length=255)

class MDN(models.Model):
    STATUS_CHOICES = (
        ('S', 'Sent'),
        ('R', 'Received'),
        ('P', 'Pending'),
    )
    message_id = models.CharField(max_length=100, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True) 
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    file = models.CharField(max_length=255)
    headers = models.TextField(null=True)
    return_url = models.URLField(null=True)
    def __str__(self):
        return self.message_id


def getorganizations():
    return [DEFAULT_ENTRY]+[(l,'%s (%s)'%(l,n)) for (l,n) in Organization.objects.values_list('as2_name','name')]

def getpartners():
    return [DEFAULT_ENTRY]+[(l,'%s (%s)'%(l,n)) for (l,n) in Partner.objects.values_list('as2_name','name')]

def update_dirs():
    partners = Partner.objects.all()
    orgs = Organization.objects.all()
    for partner in partners:
	for org in orgs:
	    as2utils.dirshouldbethere(as2utils.join(init.gsettings['root_dir'], 'messages', org.as2_name, 'inbox', partner.as2_name))
    for org in orgs:
	for partner in partners:
	    as2utils.dirshouldbethere(as2utils.join(init.gsettings['root_dir'], 'messages', partner.as2_name, 'outbox', org.as2_name))

