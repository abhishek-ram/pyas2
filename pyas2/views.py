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
from email.parser import HeaderParser
from pyas2 import models
from pyas2 import forms
from pyas2 import as2lib
from pyas2 import as2utils
from pyas2 import init
from pyas2 import viewlib
import subprocess
import sys
import os
import traceback, email, shutil
# Create your views here.


def index(request,*kw,**kwargs):
    ''' when using eg http://localhost:8080
        index can be reached without being logged in.
        most of the time user is redirected to '/home'
    '''
    return render(request,'admin/base.html')

def home(request,*kw,**kwargs):
    return render(request,'pyas2/about.html',{'pyas2info':init.gsettings})

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
	    print e
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

class SendMessage(View):
    form_class = forms.SendMessageForm
    template_name = 'pyas2/sendmessage.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
	    #botsglobal.logger.info(_(u'Run bots-engine with parameters: "%(parameters)s"'),{'parameters':str(lijst)})
	    python_executable_path = init.gsettings['python_path']
	    managepy_path = as2utils.join(os.path.dirname(os.path.dirname(__file__)), 'manage.py')
	    ufile = as2utils.join(init.gsettings['root_dir'], request.FILES['file'].name) 
	    with open(ufile, 'wb+') as destination:
		for chunk in request.FILES['file'].chunks():
		    destination.write(chunk)
	    lijst = [python_executable_path,managepy_path,'sendmessage',form.cleaned_data['organization'],form.cleaned_data['partner'], ufile]
	    print lijst
	    try:
                terug = subprocess.Popen(lijst).pid
            except Exception as msg:
                notification = _(u'Errors while trying to run send message: "%s".')%msg
                messages.add_message(request, messages.INFO, notification)
                #botsglobal.logger.info(notification)
            else:
                messages.add_message(request, messages.INFO, _(u'Sending the message to your partner ......'))
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, self.template_name, {'form': form})

def sendasyncmdn(request,*args,**kwargs):
    python_executable_path = sys.executable
    managepy_path = as2utils.join(os.path.dirname(os.path.dirname(__file__)), 'manage.py')
    lijst = [python_executable_path,managepy_path,'sendasyncmdn']
    try:
	terug = subprocess.Popen(lijst).pid
    except Exception as msg:
	notification = _(u'Errors while trying to run send async MDNs: "%s".')%msg
	messages.add_message(request, messages.INFO, notification)
    else:
	messages.add_message(request, messages.INFO, _(u'Sending all pending asynchronous MDNs .....'))
    return HttpResponseRedirect(reverse('home'))

def retryfailedmessages(request,*args,**kwargs):
    python_executable_path = sys.executable
    managepy_path = as2utils.join(os.path.dirname(os.path.dirname(__file__)), 'manage.py')
    lijst = [python_executable_path,managepy_path,'retryfailedmessages']
    try:
        terug = subprocess.Popen(lijst).pid
    except Exception as msg:
        notification = _(u'Errors while trying to run send async MDNs: "%s".')%msg
        messages.add_message(request, messages.INFO, notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Retrying failed outbound messages .....'))
    return HttpResponseRedirect(reverse('home'))

def sendtestmailmanagers(request,*args,**kwargs):
    from django.core.mail import mail_managers
    try:
        mail_managers(_(u'testsubject'), _(u'test content of report'))
    except Exception,e:
        #txt = botslib.txtexc()
        messages.add_message(request, messages.INFO, _(u'Sending test mail failed.'))
        #botsglobal.logger.info(_(u'Sending test mail failed, error:\n%(txt)s'), {'txt':txt})
        return redirect(reverse('home'))
    notification = _(u'Sending test mail succeeded.')
    messages.add_message(request, messages.INFO, notification)
    #botsglobal.logger.info(notification)
    return redirect(reverse('home'))

@csrf_exempt
def as2receive(request,*args,**kwargs):
    if request.method == 'POST':
        as2payload = ''
        for key in request.META:
            if key.startswith('HTTP') or key.startswith('CONTENT'):
                as2payload = as2payload + '%s: %s\n'%(key.replace("HTTP_","").replace("_","-").lower(), request.META[key])
	as2headers = as2payload
        as2payload = as2payload + '\n' + request.read()
	file = open("compressed.msg", 'wb')
        file.write(as2payload)
        file.close
	try:
	    payload = email.message_from_string(as2payload)
	    mdn = False
	    if payload.get_content_type() == 'multipart/report':
		mdn = True
		mdn_message = payload
	    elif payload.get_content_type() == 'multipart/signed':
		for part in payload.walk():
		    if part.get_content_type() == 'multipart/report':
			mdn = True
			mdn_message = part
	    if mdn:
		for part in mdn_message.walk():
		    if (part.get_content_type() == 'message/disposition-notification'):
			msg_id = part.get_payload().pop().get('Original-Message-ID')
		message = models.Message.objects.get(message_id=msg_id.strip('<>'))
		models.Log.objects.create(message=message, status='S', text='Processing asynchronous mdn received from partner')
		try:	
		    as2lib.save_mdn(message, as2payload)
		    message.status = 'S'
		    message.adv_status = 'Completed'
		    models.Log.objects.create(message=message, status='S', text='File Transferred successfully to the partner')
		except Exception,e:
		    message.status = 'E'
		    message.adv_status = 'Failed to send message, error is %s' %e
		    models.Log.objects.create(message=message, status='E', text = message.adv_status)		
		finally:
		    message.save()    
		    return HttpResponse("AS2 ASYNC MDN has been received")
	    else:
        	try:
	            if  models.Message.objects.filter(message_id=payload.get('message-id').strip('<>')).exists():
			message = models.Message.objects.create(message_id='%s_%s'%(payload.get('message-id').strip('<>'),payload.get('date')),direction='IN', status='IP', headers=as2headers)
			raise as2lib.as2duplicatedocument("An identical message has already been sent to our server")
		    message = models.Message.objects.create(message_id=payload.get('message-id').strip('<>'),direction='IN', status='IP', headers=as2headers)	
		    payload = as2lib.save_message(message, as2payload)
		    outputdir = as2utils.join(init.gsettings['root_dir'], 'messages', message.organization.as2_name, 'inbox', message.partner.as2_name)
		    storedir = init.gsettings['payload_receive_store'] 
		    filename = payload.get_filename() or message.message_id.strip('<>')
		    fullfilename = as2utils.join(outputdir, filename)
		    storefilename = as2utils.join(storedir, filename)
		    file = open(fullfilename , 'wb')
		    file.write(payload.get_payload(decode=True))
		    file.close()
		    shutil.copyfile(fullfilename, storefilename) 
		    models.Log.objects.create(message=message, status='S', text='Message has been saved successfully to %s'%fullfilename)
		    message.payload = models.Payload.objects.create(name=filename, file=storefilename, content_type=payload.get_content_type())
		    status, adv_status, status_message = 'success', '', ''
		    message.save()
		except as2lib.as2duplicatedocument,e:
		    status, adv_status, status_message = 'warning', 'duplicate-document', 'An error occured during the AS2 message processing: %s'%e
		except as2lib.as2partnernotfound,e:
		    status, adv_status, status_message = 'error', 'unknown-trading-partner', 'An error occured during the AS2 message processing: %s'%e
		except as2lib.as2insufficientsecurity,e:
		    status, adv_status, status_message = 'error', 'insufficient-message-security', 'An error occured during the AS2 message processing: %s'%e 
		except as2lib.as2decryptionfailed,e:
		    status, adv_status, status_message = 'error', 'decryption-failed', 'An error occured during the AS2 message processing: %s'%e
		except as2lib.as2invalidsignature,e:
		    print traceback.format_exc(None).decode('utf-8','ignore')
		    status, adv_status, status_message = 'error', 'integrity-check-failed', 'An error occured during the AS2 message processing: %s'%e
		except Exception,e:
		    status, adv_status, status_message = 'error', 'unexpected-processing-error', 'An error occured during the AS2 message processing: %s'%e
		finally:
		    mdnbody, mdnmessage = as2lib.build_mdn(message, status, adv_status=adv_status, status_message=status_message)
		    if mdnbody:
            		mdnresponse = HttpResponse(mdnbody, content_type=mdnmessage.get_content_type())
            		for key,value in mdnmessage.items():
                	     mdnresponse[key] = value
            		return mdnresponse
		    else:
	    		return HttpResponse("AS2 message has been received")
	except Exception,e:
	    print traceback.format_exc(None).decode('utf-8','ignore')
	    print e	
    elif request.method == 'GET':
        return HttpResponse("To submit an AS2 message, you must POST the message to this URL ")
    elif request.method == 'OPTIONS':
        response = HttpResponse()
        response['allow'] = ','.join(['POST', 'GET'])
        return response

