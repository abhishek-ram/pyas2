from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import View
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.core.mail import mail_managers
from email.parser import HeaderParser
from pyas2 import models
from pyas2 import forms
from pyas2 import as2lib
from pyas2 import as2utils
from pyas2 import pyas2init
from pyas2 import viewlib
import subprocess
import sys
import tempfile
import os
import traceback, email, shutil
# Create your views here.

def server_error(request, template_name='500.html'):
    ''' the 500 error handler.
        Templates: `500.html`
        Context: None
        str().decode(): bytes->unicode
    '''
    exc_info = traceback.format_exc(None).decode('utf-8','ignore')
    pyas2init.logger.error(_(u'Ran into server error: "%(error)s"'),{'error':str(exc_info)})
    temp = django.template.loader.get_template(template_name)  #You need to create a 500.html template.
    return django.http.HttpResponseServerError(temp.render(django.template.Context({'exc_info':exc_info})))

def client_error(request, template_name='400.html'):
    ''' the 400 error handler.
        Templates: `400.html`
        Context: None
        str().decode(): bytes->unicode
    '''
    exc_info = traceback.format_exc(None).decode('utf-8','ignore')
    pyas2init.logger.error(_(u'Ran into client error: "%(error)s"'),{'error':str(exc_info)})
    temp = django.template.loader.get_template(template_name)  #You need to create a 500.html template.
    return django.http.HttpResponseServerError(temp.render(django.template.Context({'exc_info':exc_info})))

def home(request,*kw,**kwargs):
    return render(request,'pyas2/about.html',{'pyas2info':pyas2init.gsettings})

class MessageList(ListView):
    model = models.Message
    paginate_by = 25
    def get_queryset(self):
        if self.request.GET:
            qstring = dict()
            for param in self.request.GET.items():
                if param[1]:
                    if param[0] == 'dateuntil':
                        qstring['timestamp__lt'] = param[1]
                    elif param[0] == 'datefrom':
                        qstring['timestamp__gte'] = param[1]
                    elif param[0] in ['organization','partner']:
                        qstring[param[0] + '__as2_name'] = param[1]
                    elif param[0] == 'filename':
                        qstring['payload__name'] = param[1]
                    elif param[0] in ['direction', 'status', 'message_id']:
                        qstring[param[0]] = param[1]
            return models.Message.objects.filter(**qstring).order_by('-timestamp')
        return models.Message.objects.all().order_by('-timestamp')

class MessageDetail(DetailView):
    model = models.Message
   
    def get_context_data(self, **kwargs):
        context = super(MessageDetail, self).get_context_data(**kwargs)
        context['logs'] = models.Log.objects.filter(message=kwargs['object']).order_by('timestamp')
        return context


class MessageSearch(View):
    form_class = forms.MessageSearchForm
    template_name = 'pyas2/message_search.html'
   
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect(viewlib.url_with_querystring(reverse('messages'), **form.cleaned_data))
        else:
            return render(request, self.template_name, {'form': form, 'confirm' : False})	

class PayloadView(View):
    template_name = 'pyas2/file_view.html'
    def get(self, request, pk, *args, **kwargs):
        try:
            message = models.Message.objects.get(message_id=pk)
            payload = message.payload
            if request.GET['action'] == 'downl':
                response = HttpResponse(content_type=payload.content_type)
                dispositiontype = 'attachment'
                response['Content-Disposition'] = dispositiontype + '; filename=' + payload.name
                response.write(as2utils.readdata(payload.file))
                return response
            elif request.GET['action'] == 'this':
                file_obj = dict()
                file_obj['name'] = payload.name
                file_obj['id'] = pk
                file_obj['content'] = as2utils.readdata(payload.file,charset='utf-8',errors='ignore')
                if payload.content_type == 'application/EDI-X12':
                    file_obj['content'] = viewlib.indent_x12(file_obj['content'])
                elif payload.content_type == 'application/EDIFACT':
                    file_obj['content'] = viewlib.indent_edifact(file_obj['content'])
                elif payload.content_type == 'application/XML':
                    file_obj['content'] = viewlib.indent_xml(file_obj['content'])
                file_obj['direction'] = message.get_direction_display()
                file_obj['type'] = 'AS2 MESSAGE'
                file_obj['headers'] = dict(HeaderParser().parsestr(message.headers or '').items())
                return render(request,self.template_name,{'file_obj': file_obj}) 
        except Exception,e:
            return render(request,self.template_name,{'error_content': _(u'No such file.')})

class MDNList(ListView):
    model = models.MDN
    paginate_by = 25
    def get_queryset(self):
        if self.request.GET:
                qstring = dict()
                for param in self.request.GET.items():
                    if param[1]:
                        if param[0] == 'dateuntil':
                            qstring['timestamp__lt'] = param[1]
                        elif param[0] == 'datefrom':
                            qstring['timestamp__gte'] = param[1]
                        elif param[0] in ['status', 'message_id']:
                            qstring[param[0]] = param[1]
			elif param[0] in ['omessage_id', 'mdn_mode']:
			    qstring['omessage__'+param[0]] = param[1]
			elif param[0] in ['organization','partner']:
			    qstring['omessage__'+param[0]+'__as2_name'] = param[1]
                return models.MDN.objects.filter(**qstring).order_by('-timestamp')
        return models.MDN.objects.all().order_by('-timestamp')


class MDNSearch(View):
    form_class = forms.MDNSearchForm
    template_name = 'pyas2/mdn_search.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect(viewlib.url_with_querystring(reverse('mdns'), **form.cleaned_data))
        else:
            return render(request, self.template_name, {'form': form})

class MDNView(View):
    template_name = 'pyas2/file_view.html'
    def get(self, request, pk, *args, **kwargs):
        try:
	    mdn = models.MDN.objects.get(message_id=pk)
	    message = mdn.omessage
	    mdnDirection = {
		'IN' : 'Sent',
		'OUT' : 'Received'
	    }
            if request.GET['action'] == 'downl':
                response = HttpResponse(content_type='multipart/report')
                dispositiontype = 'attachment'
                response['Content-Disposition'] = dispositiontype + '; filename=' + pk + '.mdn'
                response.write(as2utils.readdata(mdn.file))
                return response
            elif request.GET['action'] == 'this':
                file_obj = dict()
                file_obj['name'] = pk + '.mdn'
                file_obj['id'] = pk
                file_obj['content'] = as2utils.readdata(mdn.file,charset='utf-8',errors='ignore')
		file_obj['direction'] = mdn.get_status_display() 
		file_obj['type'] = 'AS2 MDN'
		file_obj['headers'] = dict(HeaderParser().parsestr(mdn.headers or '').items())
		return render(request,self.template_name,{'file_obj': file_obj})
        except Exception,e:
            return render(request,self.template_name,{'error_content': _(u'No such file.')})

class sendmessage(View):
    form_class = forms.SendMessageForm
    template_name = 'pyas2/sendmessage.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            python_executable_path = pyas2init.gsettings['python_path']
            managepy_path = pyas2init.gsettings['managepy_path'] 
            temp = tempfile.NamedTemporaryFile(prefix=request.FILES['file'].name,delete=False)
            for chunk in request.FILES['file'].chunks():
                temp.write(chunk)
            lijst = [python_executable_path,managepy_path,'sendas2message',form.cleaned_data['organization'],form.cleaned_data['partner'], temp.name]
            pyas2init.logger.info(_(u'Send message started with parameters: "%(parameters)s"'),{'parameters':str(lijst)})
            try:
                terug = subprocess.Popen(lijst).pid
            except Exception as msg:
                notification = _(u'Errors while trying to run send message: "%s".')%msg
                messages.add_message(request, messages.INFO, notification)
                pyas2init.logger.info(notification)
            else:
                messages.add_message(request, messages.INFO, _(u'Sending the message to your partner ......'))
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, self.template_name, {'form': form})

def resendmessage(request,pk,*args,**kwargs):
    orig_message = models.Message.objects.get(message_id=pk)
    python_executable_path = pyas2init.gsettings['python_path']
    managepy_path = pyas2init.gsettings['managepy_path'] 
    temp = tempfile.NamedTemporaryFile(prefix=orig_message.payload.name,delete=False)
    with open(orig_message.payload.file, 'rb+') as source:
        temp.write(source.read())
    lijst = [python_executable_path,managepy_path,'sendas2message',orig_message.organization.as2_name,orig_message.partner.as2_name,temp.name]
    pyas2init.logger.info(_(u'Re-send message started with parameters: "%(parameters)s"'),{'parameters':str(lijst)})
    try:
        terug = subprocess.Popen(lijst).pid
    except Exception as msg:
        notification = _(u'Errors while trying to re-send message: "%s".')%msg
        messages.add_message(request, messages.INFO, notification)
        pyas2init.logger.info(notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Re-Sending the message to your partner ......'))
    return HttpResponseRedirect(reverse('home'))
    
def sendasyncmdn(request,*args,**kwargs):
    python_executable_path = pyas2init.gsettings['python_path']
    managepy_path = pyas2init.gsettings['managepy_path'] 
    lijst = [python_executable_path,managepy_path,'sendasyncmdn']
    pyas2init.logger.info(_(u'Send async MDNs started with parameters: "%(parameters)s"'),{'parameters':str(lijst)})
    try:
        terug = subprocess.Popen(lijst).pid
    except Exception as msg:
        notification = _(u'Errors while trying to run send async MDNs: "%s".')%msg
        messages.add_message(request, messages.INFO, notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Sending all pending asynchronous MDNs .....'))
    return HttpResponseRedirect(reverse('home'))

def retryfailedcomms(request,*args,**kwargs):
    python_executable_path = pyas2init.gsettings['python_path']
    managepy_path = pyas2init.gsettings['managepy_path'] 
    lijst = [python_executable_path,managepy_path,'retryfailedas2comms']
    pyas2init.logger.info(_(u'Retry Failed communications started with parameters: "%(parameters)s"'),{'parameters':str(lijst)})
    try:
        terug = subprocess.Popen(lijst).pid
    except Exception as msg:
        notification = _(u'Errors while trying to retrying failed communications: "%s".')%msg
        messages.add_message(request, messages.INFO, notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Retrying failed communications .....'))
    return HttpResponseRedirect(reverse('home'))

def cancelretries(request,pk,*args,**kwargs):
    message = models.Message.objects.get(message_id=pk)
    message.status = 'E'
    models.Log.objects.create(message=message, status='S', text=_(u'User cancelled furthur retires for this message'))
    message.save()
    messages.add_message(request, messages.INFO, _(u'Cancelled retries for message %s'%pk))
    return HttpResponseRedirect(reverse('messages'))

def sendtestmailmanagers(request,*args,**kwargs):
    try:
        mail_managers(_(u'testsubject'), _(u'test content of report'))
    except Exception,e:
        txt = as2utils.txtexc()
        messages.add_message(request, messages.INFO, _(u'Sending test mail failed.'))
        pyas2init.logger.info(_(u'Sending test mail failed, error:\n%(txt)s'), {'txt':txt})
        return redirect(reverse('home'))
    notification = _(u'Sending test mail succeeded.')
    messages.add_message(request, messages.INFO, notification)
    pyas2init.logger.info(notification)
    return redirect(reverse('home'))

@csrf_exempt
def as2receive(request,*args,**kwargs):
    ''' 
       Function receives requests from partners.  
       Checks whether its an AS2 message or an MDN and acts accordingly.
    '''
    if request.method == 'POST':
        as2payload = ''
        for key in request.META:
            if key.startswith('HTTP') or key.startswith('CONTENT'):
                as2payload = as2payload + '%s: %s\n'%(key.replace("HTTP_","").replace("_","-").lower(), request.META[key])
        as2headers = as2payload
        as2payload = as2payload + '\n' + request.read()
        try:
            payload = email.message_from_string(as2payload)
            mdn_message = None 
            if payload.get_content_type() == 'multipart/report':
                mdn_message = payload
            elif payload.get_content_type() == 'multipart/signed':
                for part in payload.walk():
                    if part.get_content_type() == 'multipart/report':
                        mdn_message = part
            if mdn_message:
                for part in mdn_message.walk():
                    if (part.get_content_type() == 'message/disposition-notification'):
                        msg_id = part.get_payload().pop().get('Original-Message-ID')
                message = models.Message.objects.get(message_id=msg_id.strip('<>'))
                models.Log.objects.create(message=message, status='S', text=_(u'Processing asynchronous mdn received from partner'))
                try:	
                    as2lib.save_mdn(message, as2payload)
                except Exception,e:
                    message.status = 'E'
                    models.Log.objects.create(message=message, status='E', text=_(u'Failed to send message, error is %s' %e))		
                    #### Send mail here
                    as2utils.sendpyas2errorreport(message,_(u'Failed to send message, error is %s' %e))
                finally:
                    message.save()    
                    return HttpResponse(_(u'AS2 ASYNC MDN has been received'))
            else:
                try:
                    if  models.Message.objects.filter(message_id=payload.get('message-id').strip('<>')).exists():
                        message = models.Message.objects.create(message_id='%s_%s'%(payload.get('message-id').strip('<>'),payload.get('date')),direction='IN', status='IP', headers=as2headers)
                        raise as2utils.as2duplicatedocument(_(u'An identical message has already been sent to our server'))
                    message = models.Message.objects.create(message_id=payload.get('message-id').strip('<>'),direction='IN', status='IP', headers=as2headers)	
                    payload = as2lib.save_message(message, as2payload)
                    outputdir = as2utils.join(pyas2init.gsettings['root_dir'], 'messages', message.organization.as2_name, 'inbox', message.partner.as2_name)
                    storedir = pyas2init.gsettings['payload_receive_store'] 
                    if message.partner.keep_filename and payload.get_filename():
                        filename = payload.get_filename()
                    else:
                        filename = '%s.msg' %message.message_id
                    content = payload.get_payload(decode=True)
                    fullfilename = as2utils.storefile(outputdir,filename,content,False)
                    storefilename = as2utils.storefile(pyas2init.gsettings['payload_receive_store'],message.message_id,content,True)
                    models.Log.objects.create(message=message, status='S', text=_(u'Message has been saved successfully to %s'%fullfilename))
                    message.payload = models.Payload.objects.create(name=filename, file=storefilename, content_type=payload.get_content_type())
                    status, adv_status, status_message = 'success', '', ''
                    as2lib.run_postreceive(message,fullfilename)
                    message.save()
                except as2utils.as2duplicatedocument,e:
                    status, adv_status, status_message = 'warning', 'duplicate-document', _(u'An error occured during the AS2 message processing: %s'%e)
                except as2utils.as2partnernotfound,e:
                    status, adv_status, status_message = 'error', 'unknown-trading-partner', _(u'An error occured during the AS2 message processing: %s'%e)
                except as2utils.as2insufficientsecurity,e:
                    status, adv_status, status_message = 'error', 'insufficient-message-security', _(u'An error occured during the AS2 message processing: %s'%e) 
                except as2utils.as2decryptionfailed,e:
                    status, adv_status, status_message = 'error', 'decryption-failed', _(u'An error occured during the AS2 message processing: %s'%e)
                except as2utils.as2decompressionfailed,e:
                    status, adv_status, status_message = 'error', 'decompression-failed', _(u'An error occured during the AS2 message processing: %s'%e)
                except as2utils.as2invalidsignature,e:
                    status, adv_status, status_message = 'error', 'integrity-check-failed', _(u'An error occured during the AS2 message processing: %s'%e)
                except Exception,e:
                    txt = as2utils.txtexc()
                    pyas2init.logger.error(_(u'Unexpected error while processing message %(msg)s, error:\n%(txt)s'), {'txt':txt,'msg':message.message_id})
                    status, adv_status, status_message = 'error', 'unexpected-processing-error', 'An error occured during the AS2 message processing: %s'%e
                finally:
                    mdnbody, mdnmessage = as2lib.build_mdn(message, status, adv_status=adv_status, status_message=status_message)
                    if mdnbody:
                        mdnresponse = HttpResponse(mdnbody, content_type=mdnmessage.get_content_type())
                        for key,value in mdnmessage.items():
                            mdnresponse[key] = value
                        return mdnresponse
                    else:
                        return HttpResponse(_(u'AS2 message has been received'))
        except Exception,e:
            txt = as2utils.txtexc()
            reporttxt = _(u'Fatal error while processing message %(msg)s, error:\n%(txt)s')%{'txt':txt,'msg':request.META.get('HTTP_MESSAGE_ID').strip('<>')}
            pyas2init.logger.error(reporttxt)
            #### Send mail here
            mail_managers(_(u'[pyAS2 Error Report] Fatal error%(time)s')%{'time':request.META.get('HTTP_DATE')}, reporttxt)
    elif request.method == 'GET':
        return HttpResponse(_('To submit an AS2 message, you must POST the message to this URL '))
    elif request.method == 'OPTIONS':
        response = HttpResponse()
        response['allow'] = ','.join(['POST', 'GET'])
        return response

