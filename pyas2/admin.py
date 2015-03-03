from django.contrib import admin
from pyas2.forms import PrivateCertificateForm
from pyas2 import models 

# Register your models here.

class PrivateCertificateAdmin(admin.ModelAdmin):
    form = PrivateCertificateForm

class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'as2_name', 'target_url', 'encryption', 'encryption_key', 'signature', 'signature_key', 'mdn', 'mdn_mode']
    list_filter = ('name','as2_name')

admin.site.register(models.PrivateCertificate, PrivateCertificateAdmin)
admin.site.register(models.PublicCertificate)
admin.site.register(models.Organization)
admin.site.register(models.Partner, PartnerAdmin)
admin.site.register(models.Message)
admin.site.register(models.MDN)
