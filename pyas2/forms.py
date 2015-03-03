from pyas2 import models
from django import forms
from pyas2 import viewlib

HIDDENINPUT = forms.widgets.HiddenInput

class Select(forms.Form):
    datefrom = forms.DateTimeField(initial=viewlib.datetimefrom)
    dateuntil = forms.DateTimeField(initial=viewlib.datetimeuntil)
    page = forms.IntegerField(required=False,initial=1,widget=HIDDENINPUT())
    #sortedby = forms.CharField(initial='ts',widget=HIDDENINPUT())
    #sortedasc = forms.BooleanField(initial=False,required=False,widget=HIDDENINPUT())

class PrivateCertificateForm(forms.ModelForm):
    certificate_passphrase = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = models.PrivateCertificate
	fields = ['certificate', 'ca_cert', 'certificate_passphrase']

class MessageSearchForm(Select):
    organization = forms.ChoiceField([],required=False)
    partner = forms.ChoiceField([],required=False)
    direction = forms.ChoiceField([],required=False)
    status = forms.ChoiceField([],required=False)
    message_id = forms.CharField(required=False,label='Message ID',max_length=255)
    filename = forms.CharField(required=False,label='Payload Name',max_length=100)
    def __init__(self, *args, **kwargs):
        super(MessageSearchForm, self).__init__(*args, **kwargs)
        self.fields['organization'].choices = models.getorganizations()
        self.fields['partner'].choices = models.getpartners()	
	self.fields['direction'].choices = [models.DEFAULT_ENTRY] + list(models.Message.DIRECTION_CHOICES)
	self.fields['status'].choices = [models.DEFAULT_ENTRY] + list(models.Message.STATUS_CHOICES)

class MDNSearchForm(Select):
    organization = forms.ChoiceField([],required=False)
    partner = forms.ChoiceField([],required=False)
    mdn_mode = forms.ChoiceField([],required=False)
    status = forms.ChoiceField([],required=False)
    message_id = forms.CharField(required=False,label='MDN Message ID',max_length=255)
    omessage_id = forms.CharField(required=False,label='Original Message ID',max_length=255)
    def __init__(self, *args, **kwargs):
        super(MDNSearchForm, self).__init__(*args, **kwargs)
	self.fields['organization'].choices = models.getorganizations()
	self.fields['partner'].choices = models.getpartners()
	self.fields['status'].choices = [models.DEFAULT_ENTRY] + list(models.MDN.STATUS_CHOICES)
	self.fields['mdn_mode'].choices = [models.DEFAULT_ENTRY] + list(models.Message.MODE_CHOICES)

class SendMessageForm(forms.Form):
    organization = forms.ChoiceField([],required=True)
    partner = forms.ChoiceField([],required=True)
    file = forms.FileField(required=True,allow_empty_file=False)
    def __init__(self, *args, **kwargs):
        super(SendMessageForm, self).__init__(*args, **kwargs)
        self.fields['organization'].choices = models.getorganizations()
        self.fields['partner'].choices = models.getpartners()

