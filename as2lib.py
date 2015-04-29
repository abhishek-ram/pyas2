import requests
import email.Message
import email.utils
import hashlib
import as2utils
import os 
import base64
from django.utils.translation import ugettext as _
from email.mime.multipart import MIMEMultipart
from email.parser import HeaderParser
from M2Crypto import BIO, Rand, SMIME, X509
from pyas2 import models
from pyas2 import pyas2init
from string import Template

def save_message(message, raw_payload):
    ''' Function decompresses, decrypts and verifies the received message'''
    try:
        payload = email.message_from_string(raw_payload)
        micContent = None
        models.Log.objects.create(message=message, status='S', text=_(u'Begin Processing of received AS2 message'))
        if not models.Organization.objects.filter(as2_name=as2utils.unescape_as2name(payload.get('as2-to'))).exists():
            raise as2utils.as2partnernotfound('Unknown AS2 organization with id %s'%payload.get('as2-to'))
        message.organization = models.Organization.objects.get(as2_name=as2utils.unescape_as2name(payload.get('as2-to')))
        if not models.Partner.objects.filter(as2_name=as2utils.unescape_as2name(payload.get('as2-from'))).exists():
            raise as2utils.as2partnernotfound('Unknown AS2 Trading partner with id %s'%payload.get('as2-from'))
        message.partner = models.Partner.objects.get(as2_name=as2utils.unescape_as2name(payload.get('as2-from')))
        models.Log.objects.create(
            message=message, 
            status='S', 
            text=_(u'Message is for Organization "%s" from partner "%s"'%(message.organization, message.partner))
        )
        #micContent = payload.get_payload()
        filename = payload.get_filename()
        if message.partner.encryption and payload.get_content_type() != 'application/pkcs7-mime':
            raise as2utils.as2insufficientsecurity('Incoming messages from AS2 partner %s are defined to be encrypted'%message.partner.as2_name)	
        if payload.get_content_type() == 'application/pkcs7-mime' and payload.get_param('smime-type') == 'enveloped-data':
            models.Log.objects.create(message=message, status='S', text=_(u'Decrypting the payload using private key %s'%message.organization.encryption_key))
            message.encrypted = True           
            ### Check if data is base64, if not then encode
            try:
                payload.get_payload().encode('ascii')
            except Exception,e:			
                payload.set_payload(payload.get_payload().encode('base64'))
            try:
                decrypted_content = as2utils.decrypt_payload(
                    as2utils.mimetostring(payload,78),
                    str(message.organization.encryption_key.certificate.path),
                    str(message.organization.encryption_key.certificate_passphrase)
                )
                #micContent,raw_payload = as2utils.canonicalize(decrypted_content),decrypted_content
                raw_payload = decrypted_content
                payload = email.message_from_string(decrypted_content)
                ### Check if decrypted content is the actual content
                if payload.get_content_type() == 'text/plain':
                    payload = email.Message.Message()
                    payload.set_payload(decrypted_content)
                    payload.set_type('application/edi-consent')
                    if filename:
                        payload.add_header('Content-Disposition', 'attachment', filename=filename)
            except Exception, msg:
                raise as2utils.as2decryptionfailed('Failed to decrypt message, exception message is %s' %msg)
        if message.partner.signature and payload.get_content_type() != 'multipart/signed':
            raise as2utils.as2insufficientsecurity('Incoming messages from AS2 partner %s are defined to be signed'%message.partner.as2_name)
        if payload.get_content_type() == 'multipart/signed':
            if not message.partner.signature_key:
                raise as2utils.as2insufficientsecurity('Partner has no signature varification key defined')
            micalg = payload.get_param('micalg').lower() or 'sha1'
            models.Log.objects.create(message=message, status='S', text=_(u'Message is signed, Verifying it using public key %s'%message.partner.signature_key))
            message.signed = True
            main_boundary = '--' + payload.get_boundary()
            verify_cert = str(message.partner.signature_key.certificate.path)
            ca_cert = verify_cert
            if message.partner.signature_key.ca_cert :
                ca_cert = str(message.partner.signature_key.ca_cert.path)
            ### Extract the base64 encoded signature 
            for part in payload.walk():
                if part.get_content_type() == "application/pkcs7-signature":
                    try:
                        raw_sig = part.get_payload().encode('ascii').strip()
                    except Exception,e:
                        raw_sig = part.get_payload().encode('base64').strip()
                else:
                    payload = part
            ### Verify message using complete raw payload received from partner
            #pyas2init.logger.debug('Received Signed Payload :\n%s'%raw_payload)
            try:
                as2utils.verify_payload(as2utils.canonicalize2(payload),raw_sig,verify_cert, ca_cert)
                #as2utils.verify_payload(raw_payload,None,verify_cert, ca_cert)
            except Exception, e:
                ### Verify message using extracted signature and stripped message
                try:
                    as2utils.verify_payload(as2utils.extractpayload_fromstring1(raw_payload,main_boundary),raw_sig,verify_cert,ca_cert)
                except Exception, e:
                    ### Verify message using extracted signature and message without extra trailing new line
                    try:
                        as2utils.verify_payload(as2utils.extractpayload_fromstring2(raw_payload,main_boundary),raw_sig,verify_cert, ca_cert)
                    except Exception, e:
                        raise as2utils.as2invalidsignature('Signature Verification Failed, exception message is %s'%str(e))
            micContent = as2utils.canonicalize2(payload)
            #micContent = as2utils.extractpayload_fromstring2(raw_payload,main_boundary)
        if payload.get_content_type() == 'application/pkcs7-mime' and payload.get_param('smime-type') == 'compressed-data':
            models.Log.objects.create(message=message, status='S', text=_(u'Decompressing the payload'))
            message.compressed = True
            ### Decode the data if its base64
            try:
                payload.get_payload().encode('ascii')
                cdata = base64.b64decode(payload.get_payload())
            except Exception,e:
                cdata = payload.get_payload()
            try:
                dcontent = as2utils.decompress_payload(cdata)
                #if not message.signed :
                    #micContent = as2utils.canonicalize(dcontent)
                payload = email.message_from_string(dcontent)
            except Exception, e:
                raise as2utils.as2decompressionfailed('Failed to decompress message,exception message is %s' %e) 
        ### Saving the message mic for sending it in the MDN
        pyas2init.logger.debug("Receive mic content \n%s"%micContent)
        if micContent:
            calcMIC = getattr(hashlib, micalg,'sha1')
            message.mic = '%s, %s'%(calcMIC(micContent).digest().encode('base64').strip(),micalg)
        return payload
    finally:
        message.save()	
	
def build_mdn(message, status, **kwargs):
    ''' Function builds AS2 MDN report '''
    try:
        hparser = HeaderParser()
        message_header = hparser.parsestr(message.headers)
        text = _(u'The AS2 message has been processed. Thank you for exchanging AS2 messages with Pyas2.')
        if status != 'success':
            #### Send mail here
            as2utils.sendpyas2errorreport(message, _(u'Failure in processing message from partner,\n Basic status : %s \n Advanced Status: %s'%(kwargs['adv_status'],kwargs['status_message'])))
            text = _(u'The AS2 message could not be processed. The disposition-notification report has additional details.')
            models.Log.objects.create(message=message, status='E', text = kwargs['status_message'])
            message.status = 'E'
        else:
            message.status = 'S'
        if not message_header.get('disposition-notification-to'):
            models.Log.objects.create(message=message, status='S', text=_(u'MDN not requested by partner, closing request.'))
            return None, None
        models.Log.objects.create(message=message, status='S', text=_(u'Building the MDN response to the request'))
        main = MIMEMultipart('report', report_type="disposition-notification")
        textmessage = email.Message.Message()
        textmessage.set_payload("%s\n"%text)
        textmessage.set_type('text/plain')
        textmessage.set_charset('us-ascii')
        del textmessage['MIME-Version']
        main.attach(textmessage)
        mdnbase = email.Message.Message()
        mdnbase.set_type('message/disposition-notification')
        mdnbase.set_charset('us-ascii')
        mdn = 'Reporting-UA: Bots Opensource EDI Translator\n'
        mdn = mdn + 'Original-Recipient: rfc822; %s\n'%message_header.get('as2-to')
        mdn = mdn + 'Final-Recipient: rfc822; %s\n'%message_header.get('as2-to')
        mdn = mdn + 'Original-Message-ID: <%s>\n'%message.message_id
        if status != 'success':
            mdn = mdn + 'Disposition: automatic-action/MDN-sent-automatically; processed/%s: %s\n'%(status, kwargs['adv_status'])
        else:
            mdn = mdn + 'Disposition: automatic-action/MDN-sent-automatically; processed\n'
        if message.mic:
            mdn = mdn + 'Received-content-MIC: %s\n'%message.mic
        mdnbase.set_payload(mdn)
        del mdnbase['MIME-Version']
        main.attach(mdnbase)
        del main['MIME-Version']
        mdnsigned = False
        if message_header.get('disposition-notification-options') and message.organization and message.organization.signature_key: 
            models.Log.objects.create(message=message, status='S', text=_(u'Signing the MDN using private key %s'%message.organization.signature_key))
            mdnsigned = True
            options = message_header.get('disposition-notification-options').split(";")
            algorithm = options[1].split(",")[1].strip()
            signed = MIMEMultipart('signed', protocol="application/pkcs7-signature", micalg='sha1')
            signed.attach(main)
            signature = as2utils.sign_payload(
                    as2utils.canonicalize(as2utils.mimetostring(main, 0)+'\n'),
                    str(message.organization.signature_key.certificate.path), 
                    str(message.organization.signature_key.certificate_passphrase)
            )
            signed.attach(signature)
            mdnmessage = signed
        else:
            mdnmessage = main
        ### Add new line between the MDN message and the signature
        mdnbody = as2utils.extractpayload(mdnmessage)
        mainboundary = '--' + main.get_boundary() + '--'
        mdnbody = as2utils.canonicalize(mdnbody.replace(mainboundary, mainboundary + '\n'))
        mdnmessage.add_header('ediint-features', 'CEM')
        mdnmessage.add_header('as2-from', message_header.get('as2-to'))
        mdnmessage.add_header('as2-to', message_header.get('as2-from')) 
        mdnmessage.add_header('AS2-Version', '1.2')
        mdnmessage.add_header('date', email.Utils.formatdate(localtime=True))
        mdnmessage.add_header('Message-ID', email.utils.make_msgid())
        mdnmessage.add_header('user-agent', 'PYAS2, A pythonic AS2 server')
        filename = mdnmessage.get('message-id').strip('<>') + '.mdn'
        fullfilename = as2utils.storefile(pyas2init.gsettings['mdn_send_store'],filename,mdnbody,True)
        mdn_headers = ''
        for key in mdnmessage.keys():
            mdn_headers = mdn_headers + '%s: %s\n'%(key, mdnmessage[key])
        if message_header.get('receipt-delivery-option'):
            message.mdn = models.MDN.objects.create(message_id=filename, file=fullfilename, status='P', signed=mdnsigned, headers=mdn_headers, return_url= message_header['receipt-delivery-option'])
            message.mdn_mode = 'ASYNC'
            mdnbody, mdnmessage = None, None
            models.Log.objects.create(message=message, status='S', text=_(u'Asynchronous MDN requested, setting status to pending'))
        else:
            message.mdn = models.MDN.objects.create(message_id=filename,file=fullfilename, status='S', signed=mdnsigned, headers=mdn_headers)
            message.mdn_mode = 'SYNC'
            models.Log.objects.create(message=message, status='S', text=_(u'MDN created successfully and sent to partner'))
        return mdnbody, mdnmessage
    finally:
        message.save()	

def build_message(message):
    ''' Build the AS2 mime message to be sent to partner'''
    models.Log.objects.create(message=message, status='S', text=_(u'Build the AS2 message and header to send to the partner'))
    reference = '<%s>'%message.message_id
    micContent = None
    email_datetime = email.Utils.formatdate(localtime=True)
    as2Header = {
        'AS2-Version'         : '1.2',
        'ediint-features'     : 'CEM',
        'MIME-Version'        : '1.0',  
        'Message-ID'          : reference,
        'AS2-From'            : as2utils.escape_as2name(message.organization.as2_name),
        'AS2-To'              : as2utils.escape_as2name(message.partner.as2_name),
        'Subject'             : message.partner.subject,
        'Date'                : email_datetime,
        'recipient-address'   : message.partner.target_url,
        'user-agent'          : 'PYAS2, A pythonic AS2 server'
    }
    payload = email.Message.Message()
    with open(message.payload.file, 'rb') as fh:
        payload.set_payload(fh.read())
        fh.close()
    payload.set_type(message.partner.content_type)
    payload.add_header('Content-Disposition', 'attachment', filename=message.payload.name)
    del payload['MIME-Version']
    #micContent,cmicContent,content = payload.get_payload(),None,payload.get_payload()
    content = payload.get_payload()
    if message.partner.compress:
        models.Log.objects.create(message=message, status='S', text=_(u'Compressing the payload.'))
        message.compressed = True
        #micContent = as2utils.canonicalize(as2utils.mimetostring(payload, 0))
        cmessage = email.Message.Message()
        cmessage.set_type('application/pkcs7-mime')
        cmessage.set_param('name', 'smime.p7z')
        cmessage.set_param('smime-type', 'compressed-data') 
        cmessage.add_header('Content-Transfer-Encoding', 'base64')
        cmessage.add_header('Content-Disposition', 'attachment', filename='smime.p7z')
        cmessage.set_payload(as2utils.compress_payload(as2utils.canonicalize(as2utils.mimetostring(payload, 0))))
        content,payload = cmessage.get_payload(),cmessage
    if message.partner.signature: 
        models.Log.objects.create(message=message, status='S', text=_(u'Signing the message using organzation key %s'%message.organization.signature_key))
        message.signed = True
        multipart = MIMEMultipart('signed',protocol="application/pkcs7-signature",micalg=message.partner.signature)
        del multipart['MIME-Version']
        #micContent = as2utils.canonicalize2(payload)
        micContent = as2utils.canonicalize(as2utils.mimetostring(payload, 0))
        multipart.attach(payload)
        signature = as2utils.sign_payload(micContent, str(message.organization.signature_key.certificate.path), str(message.organization.signature_key.certificate_passphrase))
        multipart.attach(signature)
        multipart.as_string()
        content = as2utils.canonicalize(as2utils.extractpayload(multipart))
        payload = multipart
    if message.partner.encryption: 
        #if not message.compressed and not message.signed:
            #micContent = as2utils.canonicalize(as2utils.mimetostring(payload, 0))
        models.Log.objects.create(message=message, status='S', text=_(u'Encrypting the message using partner key %s'%message.partner.encryption_key))
        message.encrypted = True
        payload = as2utils.encrypt_payload(as2utils.canonicalize(as2utils.mimetostring(payload, 0)), message.partner.encryption_key.certificate.path , message.partner.encryption)
        payload.set_type('application/pkcs7-mime')
        content = payload.get_payload()
    if message.partner.mdn:
        as2Header['disposition-notification-to'] = 'no-reply@pyas2.com' 
        if message.partner.mdn_sign:			
            as2Header['disposition-notification-options'] = 'signed-receipt-protocol=required, pkcs7-signature; signed-receipt-micalg=optional, %s'%message.partner.mdn_sign
        message.mdn_mode = 'SYNC'
        if message.partner.mdn_mode == 'ASYNC':
            as2Header['receipt-delivery-option'] = pyas2init.gsettings['mdn_url']
            message.mdn_mode = 'ASYNC'
    pyas2init.logger.debug("Sender Mic content \n%s"%micContent)
    if micContent:
        calcMIC = getattr(hashlib, message.partner.signature,'sha1')
        message.mic = calcMIC(micContent).digest().encode('base64').strip()
    as2Header.update(payload.items())
    message.headers = ''
    for key in as2Header:
        message.headers = message.headers + '%s: %s\n'%(key, as2Header[key])
    message.save()
    models.Log.objects.create(message=message, status='S', text=_(u'AS2 message has been built successfully, sending it to the partner'))
    return content 

def send_message(message, payload):
    ''' Sends the AS2 message to the partner '''
    try:
        hparser = HeaderParser()
        message_header = hparser.parsestr(message.headers)
        auth = None
        if message.partner.http_auth:
            auth = (message.partner.http_auth_user, message.partner.http_auth_pass)
        verify = True
        if message.partner.https_ca_cert:
            verify = message.partner.https_ca_cert.path
        try:
            response = requests.post(message.partner.target_url,  auth = auth, verify=verify, headers = dict(message_header.items()), data = payload)
            response.raise_for_status()
        except Exception,e:
            ### Send mail here
            as2utils.sendpyas2errorreport(message, _(u'Failure during transmission of message to partner with error "%s".\n\nTo retry transmission run the management command "retryfailedas2comms".'%e))
            message.status = 'R'
            models.Log.objects.create(message=message, status='E', text=_(u'Message send failed with error %s'%e))
            return
        models.Log.objects.create(message=message, status='S', text=_(u'AS2 message successfully sent to partner'))
        if message.partner.mdn:
            if message.partner.mdn_mode == 'ASYNC':
                models.Log.objects.create(message=message, status='S', text=_(u'Requested ASYNC MDN from partner, waiting for it ........'))
                message.status = 'P'
                return
            mdnContent = '';
            for key in response.headers:
                mdnContent = mdnContent + '%s: %s\n'%(key, response.headers[key])
            mdnContent = mdnContent + '\n' + response.content
            models.Log.objects.create(message=message, status='S', text=_(u'Synchronous mdn received from partner'))
            save_mdn(message, mdnContent)
        else:
            message.status = 'S'
            models.Log.objects.create(message=message, status='S', text=_(u'No MDN needed, File Transferred successfully to the partner'))
            run_postsend(message)
    finally:
        message.save()

def save_mdn(message, mdnContent):
    ''' Process the received MDN and check status of sent message '''
    try:
        mdnMessage = email.message_from_string(mdnContent)
        mdnHeaders = ''
        for key in mdnMessage.keys():
            mdnHeaders = mdnHeaders + '%s: %s\n'%(key, mdnMessage[key])
        messageId = mdnMessage.get('message-id')
        if message.partner.mdn_sign and mdnMessage.get_content_type() != 'multipart/signed':
            models.Log.objects.create(message=message, status='W', text=_(u'Expected signed MDN but unsigned MDN returned'))
        mdnsigned = False
        if mdnMessage.get_content_type() == 'multipart/signed':
            models.Log.objects.create(message=message, status='S', text=_(u'Verifying the signed MDN with partner key %s'%message.partner.signature_key))
            mdnsigned = True
            verify_cert = str(message.partner.signature_key.certificate.path)
            ca_cert = verify_cert
            if message.partner.signature_key.ca_cert:
                ca_cert = str(message.partner.signature_key.ca_cert.path)
            main_boundary = '--' + mdnMessage.get_boundary()
            ### Extract the mssage and signature
            for part in mdnMessage.get_payload():
                if part.get_content_type().lower() == "application/pkcs7-signature":
                    sig = part
                else:
                    mdnMessage = part
            ### check if signature is base64 encoded and if not encode
            try:
                raw_sig = sig.get_payload().encode('ascii').strip()
            except Exception,e:
                raw_sig = sig.get_payload().encode('base64').strip()
            ### Verify the signature using raw contents
            try:
                as2utils.verify_payload(mdnContent,None,verify_cert,ca_cert)
            except Exception, e:
                ### Verify the signature using extracted signature and message
                try:
                    as2utils.verify_payload(as2utils.extractpayload_fromstring1(mdnContent,main_boundary),raw_sig,verify_cert,ca_cert)
                except Exception, e:
                    ### Verify the signature using extracted signature and message without extra trailing new line in message
                    try:
                        as2utils.verify_payload(as2utils.extractpayload_fromstring2(mdnContent,main_boundary),raw_sig,verify_cert,ca_cert)
                    except Exception, e:
                        raise as2utils.as2exception(_(u'MDN Signature Verification Error, exception message is %s' %e))
        filename = messageId.strip('<>') + '.mdn'
        fullfilename = as2utils.storefile(pyas2init.gsettings['mdn_receive_store'],filename,as2utils.extractpayload(mdnMessage),True)
        message.mdn = models.MDN.objects.create(message_id=messageId.strip('<>'),file=fullfilename, status='R', headers=mdnHeaders, signed=mdnsigned)
        if mdnMessage.get_content_type() == 'multipart/report':
            for part in mdnMessage.walk():
                if (part.get_content_type() == 'message/disposition-notification'):
                    models.Log.objects.create(message=message, status='S', text=_(u'Checking the MDN for status of the message'))
                    mdn =  part.get_payload().pop()
                    mdnOMessageId = mdn.get('Original-Message-ID')
                    mdnStatus = mdn.get('Disposition').split(';')
                    if (mdnStatus[1].strip() == 'processed'):
                        models.Log.objects.create(message=message, status='S', text=_(u'Message has been successfully processed, verifying the MIC if present.'))
                        if mdn.get('Received-Content-MIC') and message.mic:
                            mdnMIC = mdn.get('Received-Content-MIC').split(',');
                            if (message.mic != mdnMIC[0]):
                                message.status = 'W'
                                models.Log.objects.create(message=message, status='W', text=_(u'Message Integrity check failed, please validate message content with your partner'))
                            else:
                                message.status = 'S'
                                models.Log.objects.create(message=message, status='S', text=_(u'File Transferred successfully to the partner'))
                        else:
                            message.status = 'S'
                            models.Log.objects.create(message=message, status='S', text=_(u'File Transferred successfully to the partner'))
                        run_postsend(message)
                    else:
                        raise as2utils.as2exception(_(u'Partner failed to process file. MDN status is %s'%mdn.get('Disposition')))        
        else:
            raise as2utils.as2exception(_(u'MDN report not found in the response'))
    finally:
        message.save()

def run_postsend(message):
    ''' Execute command after successful send, can be used to notify successfule sends '''
    command = message.partner.cmd_send
    if command:
        models.Log.objects.create(message=message, status='S', text=_(u'Exectute command post successful send'))
        command = Template(command)
        variables = {'filename':message.payload.name, 'sender':message.organization.as2_name, 'recevier':message.partner.as2_name, 'messageid':message.message_id}
        variables.update(dict(HeaderParser().parsestr(message.headers).items()))
        os.system(command.safe_substitute(variables))

def run_postreceive(message,fullfilename):
    ''' Execute command after successful receive, can be used to call the edi program for further processing'''
    command = message.partner.cmd_receive
    if command:
        models.Log.objects.create(message=message, status='S', text=_(u'Exectute command post successful receive'))
        command = Template(command)
        variables = {'filename':message.payload.name, 'fullfilename':fullfilename, 'sender':message.organization.as2_name, 'recevier':message.partner.as2_name, 'messageid':message.message_id}
        variables.update(dict(HeaderParser().parsestr(message.headers).items()))
        os.system(command.safe_substitute(variables))



