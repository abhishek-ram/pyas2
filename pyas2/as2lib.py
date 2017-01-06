import requests
import email
import hashlib
import as2utils
import os
import base64
from django.utils.translation import ugettext as _
from email.mime.multipart import MIMEMultipart
from email.parser import HeaderParser
from pyas2 import models
from pyas2 import pyas2init
from string import Template


def save_message(message, payload, raw_payload):
    """ Function decompresses, decrypts and verifies the received AS2 message
     Takes an AS2 message as input and returns the actual payload ex. X12 message """

    try:
        # Initialize variables
        mic_content = None
        mic_alg = None
        filename = payload.get_filename()

        # Search for the organization adn partner, raise error if none exists.
        models.Log.objects.create(message=message, status='S', text=_(u'Begin Processing of received AS2 message'))

        if not models.Organization.objects.filter(as2_name=as2utils.unescape_as2name(payload.get('as2-to'))).exists():
            raise as2utils.As2PartnerNotFound('Unknown AS2 organization with id %s' % payload.get('as2-to'))
        message.organization = models.Organization.objects.get(
            as2_name=as2utils.unescape_as2name(payload.get('as2-to')))

        if not models.Partner.objects.filter(as2_name=as2utils.unescape_as2name(payload.get('as2-from'))).exists():
            raise as2utils.As2PartnerNotFound('Unknown AS2 Trading partner with id %s' % payload.get('as2-from'))
        message.partner = models.Partner.objects.get(as2_name=as2utils.unescape_as2name(payload.get('as2-from')))
        models.Log.objects.create(
            message=message,
            status='S',
            text=_(u'Message is for Organization "%s" from partner "%s"' % (message.organization, message.partner))
         )

        # Check if message from this partner are expected to be encrypted
        if message.partner.encryption and payload.get_content_type() != 'application/pkcs7-mime':
            raise as2utils.As2InsufficientSecurity(
                u'Incoming messages from AS2 partner {0:s} are defined to be encrypted'.format(
                    message.partner.as2_name))

        # Check if payload is encrypted and if so decrypt it
        if payload.get_content_type() == 'application/pkcs7-mime' \
                and payload.get_param('smime-type') == 'enveloped-data':
            models.Log.objects.create(message=message, status='S', text=_(
                u'Decrypting the payload using private key {0:s}'.format(message.organization.encryption_key)))
            message.encrypted = True

            # Check if encrypted data is base64 encoded, if not then encode
            try:
                payload.get_payload().encode('ascii')
            except UnicodeDecodeError:
                payload.set_payload(payload.get_payload().encode('base64'))

            # Decrypt the base64 encoded data using the partners public key
            pyas2init.logger.debug(u'Decrypting the payload :\n{0:s}'.format(payload.get_payload()))
            try:
                decrypted_content = as2utils.decrypt_payload(
                    as2utils.mimetostring(payload, 78),
                    str(message.organization.encryption_key.certificate.path),
                    str(message.organization.encryption_key.certificate_passphrase)
                )
                raw_payload = decrypted_content
                payload = email.message_from_string(decrypted_content)

                # Check if decrypted content is the actual content i.e. no compression and no signatures
                if payload.get_content_type() == 'text/plain':
                    payload = email.Message.Message()
                    payload.set_payload(decrypted_content)
                    payload.set_type('application/edi-consent')
                    if filename:
                        payload.add_header('Content-Disposition', 'attachment', filename=filename)
            except Exception, msg:
                raise as2utils.As2DecryptionFailed('Failed to decrypt message, exception message is %s' % msg)

        # Check if message from this partner are expected to be signed
        if message.partner.signature and payload.get_content_type() != 'multipart/signed':
            raise as2utils.As2InsufficientSecurity(
                u'Incoming messages from AS2 partner {0:s} are defined to be signed'.format(message.partner.as2_name))

        # Check if message is signed and if so verify it
        if payload.get_content_type() == 'multipart/signed':
            if not message.partner.signature_key:
                raise as2utils.As2InsufficientSecurity('Partner has no signature verification key defined')
            models.Log.objects.create(message=message, status='S', text=_(
                u'Message is signed, Verifying it using public key {0:s}'.format(message.partner.signature_key)))
            pyas2init.logger.debug('Verifying the signed payload:\n{0:s}'.format(payload.as_string()))
            message.signed = True
            mic_alg = payload.get_param('micalg').lower() or 'sha1'
            # main_boundary = '--' + payload.get_boundary()

            # Get the partners public and ca certificates
            cert = str(message.partner.signature_key.certificate.path)
            ca_cert = cert
            if message.partner.signature_key.ca_cert:
                ca_cert = str(message.partner.signature_key.ca_cert.path)
            verify_cert = message.partner.signature_key.verify_cert

            # Extract the signature and signed content from the mime message
            raw_sig = None
            for part in payload.walk():
                if part.get_content_type() == "application/pkcs7-signature":
                    try:
                        raw_sig = part.get_payload().encode('ascii').strip()
                    except UnicodeDecodeError:
                        raw_sig = part.get_payload().encode('base64').strip()
                else:
                    payload = part

            # Verify message using raw payload received from partner
            try:
                as2utils.verify_payload(raw_payload, None, cert, ca_cert, verify_cert)
            except Exception:
                # Verify message using extracted signature and stripped message
                try:
                    as2utils.verify_payload(as2utils.canonicalize2(payload), raw_sig, cert, ca_cert, verify_cert)
                except Exception, e:
                    raise as2utils.As2InvalidSignature(
                        'Signature Verification Failed, exception message is {0:s}'.format(e))

            mic_content = as2utils.canonicalize2(payload)

        # Check if the message has been compressed and if so decompress it
        if payload.get_content_type() == 'application/pkcs7-mime' \
                and payload.get_param('smime-type') == 'compressed-data':
            models.Log.objects.create(message=message, status='S', text=_(u'Decompressing the payload'))
            message.compressed = True

            # Decode the data to binary if its base64 encoded
            compressed_content = payload.get_payload()
            try:
                compressed_content.encode('ascii')
                compressed_content = base64.b64decode(payload.get_payload())
            except UnicodeDecodeError:
                pass

            pyas2init.logger.debug('Decompressing the payload:\n%s' % compressed_content)
            try:
                decompressed_content = as2utils.decompress_payload(compressed_content)
                payload = email.message_from_string(decompressed_content)
            except Exception, e:
                raise as2utils.As2DecompressionFailed('Failed to decompress message,exception message is %s' % e)

        # Saving the message mic for sending it in the MDN
        if mic_content:
            pyas2init.logger.debug("Calculating MIC with alg {0:s} for content:\n{1:s}".format(mic_alg, mic_content))
            calculate_mic = getattr(hashlib, mic_alg.replace('-', ''), hashlib.sha1)
            message.mic = '%s, %s' % (calculate_mic(mic_content).digest().encode('base64').strip(), mic_alg)

        return payload
    finally:
        message.save()


def build_mdn(message, status, **kwargs):
    """ Function builds AS2 MDN report for the received message.
    Takes message status as input and returns the mdn content."""

    try:
        # Initialize variables
        mdn_body, mdn_message = None, None

        # Set the confirmation text message here
        confirmation_text = str()
        if message.organization and message.organization.confirmation_message:
            confirmation_text = message.organization.confirmation_message
        # overwrite with partner specific message
        if message.partner and message.partner.confirmation_message:
            confirmation_text = message.partner.confirmation_message
        # default message
        if confirmation_text.strip() == '':
            confirmation_text = _(u'The AS2 message has been processed. '
                                  u'Thank you for exchanging AS2 messages with Pyas2.')

        # Update message status and send mail here based on the created MDN
        if status != 'success':
            as2utils.senderrorreport(message, _(u'Failure in processing message from partner,\n '
                                                u'Basic status : %s \n Advanced Status: %s' %
                                                (kwargs['adv_status'], kwargs['status_message'])))
            confirmation_text = _(u'The AS2 message could not be processed. '
                                  u'The disposition-notification report has additional details.')
            models.Log.objects.create(message=message, status='E', text=kwargs['status_message'])
            message.status = 'E'
        else:
            message.status = 'S'

        # In case no MDN is requested exit from process
        header_parser = HeaderParser()
        message_header = header_parser.parsestr(message.headers)
        if not message_header.get('disposition-notification-to'):
            models.Log.objects.create(message=message, status='S',
                                      text=_(u'MDN not requested by partner, closing request.'))
            return mdn_body, mdn_message

        # Build the MDN report
        models.Log.objects.create(message=message, status='S', text=_(u'Building the MDN response to the request'))
        mdn_report = MIMEMultipart('report', report_type="disposition-notification")

        # Build the text message with confirmation text and add to report
        mdn_text = email.Message.Message()
        mdn_text.set_payload("%s\n" % confirmation_text)
        mdn_text.set_type('text/plain')
        mdn_text.set_charset('us-ascii')
        del mdn_text['MIME-Version']
        mdn_report.attach(mdn_text)

        # Build the MDN message and add to report
        mdn_base = email.Message.Message()
        mdn_base.set_type('message/disposition-notification')
        mdn_base.set_charset('us-ascii')
        mdn = 'Reporting-UA: Bots Opensource EDI Translator\n'
        mdn += 'Original-Recipient: rfc822; %s\n' % message_header.get('as2-to')
        mdn += 'Final-Recipient: rfc822; %s\n' % message_header.get('as2-to')
        mdn += 'Original-Message-ID: <%s>\n' % message.message_id
        if status != 'success':
            mdn += 'Disposition: automatic-action/MDN-sent-automatically; ' \
                   'processed/%s: %s\n' % (status, kwargs['adv_status'])
        else:
            mdn += 'Disposition: automatic-action/MDN-sent-automatically; processed\n'
        if message.mic:
            mdn += 'Received-content-MIC: %s\n' % message.mic
        mdn_base.set_payload(mdn)
        del mdn_base['MIME-Version']
        mdn_report.attach(mdn_base)
        del mdn_report['MIME-Version']

        # If signed MDN is requested by partner then sign the MDN and attach to report
        pyas2init.logger.debug('MDN for message %s created:\n%s' % (message.message_id, mdn_report.as_string()))
        mdn_signed = False
        if message_header.get('disposition-notification-options') and message.organization \
                and message.organization.signature_key:
            models.Log.objects.create(message=message,
                                      status='S',
                                      text=_(u'Signing the MDN using private key {0:s}'.format(
                                          message.organization.signature_key)))
            mdn_signed = True
            # options = message_header.get('disposition-notification-options').split(";")
            # algorithm = options[1].split(",")[1].strip()
            signed_report = MIMEMultipart('signed', protocol="application/pkcs7-signature")
            signed_report.attach(mdn_report)
            mic_alg, signature = as2utils.sign_payload(
                    as2utils.canonicalize(as2utils.mimetostring(mdn_report, 0)+'\n'),
                    str(message.organization.signature_key.certificate.path),
                    str(message.organization.signature_key.certificate_passphrase)
            )
            pyas2init.logger.debug('Signature for MDN created:\n%s' % signature.as_string())
            signed_report.set_param('micalg', mic_alg)
            signed_report.attach(signature)
            mdn_message = signed_report
        else:
            mdn_message = mdn_report

        # Extract the MDN boy from the mdn message.
        # Add new line between the MDN message and the signature,
        # Found that without this MDN signature verification fails on Mendelson AS2
        main_boundary = '--' + mdn_report.get_boundary() + '--'
        mdn_body = as2utils.canonicalize(
            as2utils.extractpayload(mdn_message).replace(main_boundary, main_boundary+'\n'))

        # Add the relevant headers to the MDN message
        mdn_message.add_header('ediint-features', 'CEM')
        mdn_message.add_header('as2-from', message_header.get('as2-to'))
        mdn_message.add_header('as2-to', message_header.get('as2-from'))
        mdn_message.add_header('AS2-Version', '1.2')
        mdn_message.add_header('date', email.Utils.formatdate(localtime=True))
        mdn_message.add_header('Message-ID', email.utils.make_msgid())
        mdn_message.add_header('user-agent', 'PYAS2, A pythonic AS2 server')

        # Save the MDN to the store
        filename = mdn_message.get('message-id').strip('<>') + '.mdn'
        full_filename = as2utils.storefile(pyas2init.gsettings['mdn_send_store'], filename, mdn_body, True)

        # Extract the MDN headers as string
        mdn_headers = ''
        for key in mdn_message.keys():
            mdn_headers += '%s: %s\n' % (key, mdn_message[key])

        # Is Async mdn is requested mark MDN as pending and return None
        if message_header.get('receipt-delivery-option'):
            message.mdn = models.MDN.objects.create(message_id=filename,
                                                    file=full_filename,
                                                    status='P',
                                                    signed=mdn_signed,
                                                    headers=mdn_headers,
                                                    return_url=message_header['receipt-delivery-option'])
            message.mdn_mode = 'ASYNC'
            mdn_body, mdn_message = None, None
            models.Log.objects.create(message=message,
                                      status='S',
                                      text=_(u'Asynchronous MDN requested, setting status to pending'))

        # Else mark MDN as sent and return the MDN message
        else:
            message.mdn = models.MDN.objects.create(message_id=filename,
                                                    file=full_filename,
                                                    status='S',
                                                    signed=mdn_signed,
                                                    headers=mdn_headers)
            message.mdn_mode = 'SYNC'
            models.Log.objects.create(message=message,
                                      status='S',
                                      text=_(u'MDN created successfully and sent to partner'))
        return mdn_body, mdn_message
    finally:
        message.save()


def build_message(message):
    """ Build the AS2 mime message to be sent to partner. Encrypts, signs and compresses the message based on
    the partner profile. Returns the message final message content."""

    # Initialize the variables
    mic_content, mic_alg = None, None
    payload = email.Message.Message()

    # Build the As2 message headers as per specifications
    models.Log.objects.create(message=message,
                              status='S',
                              text=_(u'Build the AS2 message and header to send to the partner'))
    email_datetime = email.Utils.formatdate(localtime=True)
    as2_header = {
        'AS2-Version': '1.2',
        'ediint-features': 'CEM',
        'MIME-Version': '1.0',
        'Message-ID': '<%s>' % message.message_id,
        'AS2-From': as2utils.escape_as2name(message.organization.as2_name),
        'AS2-To': as2utils.escape_as2name(message.partner.as2_name),
        'Subject': message.partner.subject,
        'Date': email_datetime,
        'recipient-address': message.partner.target_url,
        'user-agent': 'PYAS2, A pythonic AS2 server'
    }

    # Create the payload message and add the data to be transferred as its contents
    with open(message.payload.file, 'rb') as fh:
        as2_content = fh.read()
    payload.set_payload(as2_content)
    payload.set_type(message.partner.content_type)
    payload.add_header('Content-Disposition', 'attachment', filename=message.payload.name)
    del payload['MIME-Version']

    # Compress the message if requested in the profile
    if message.partner.compress:
        models.Log.objects.create(message=message, status='S', text=_(u'Compressing the payload.'))
        message.compressed = True
        compressed_message = email.Message.Message()
        compressed_message.set_type('application/pkcs7-mime')
        compressed_message.set_param('name', 'smime.p7z')
        compressed_message.set_param('smime-type', 'compressed-data')
        compressed_message.add_header('Content-Transfer-Encoding', 'base64')
        compressed_message.add_header('Content-Disposition', 'attachment', filename='smime.p7z')
        compressed_message.set_payload(
            as2utils.compress_payload(as2utils.canonicalize(as2utils.mimetostring(payload, 0))))
        as2_content, payload = compressed_message.get_payload(), compressed_message
        pyas2init.logger.debug('Compressed message %s payload as:\n%s' % (message.message_id, payload.as_string()))

    # Sign the message if requested in the profile
    if message.partner.signature:
        models.Log.objects.create(message=message,
                                  status='S',
                                  text=_(u'Signing the message using organization key {0:s}'.format(
                                      message.organization.signature_key)))
        message.signed = True
        signed_message = MIMEMultipart('signed', protocol="application/pkcs7-signature")
        del signed_message['MIME-Version']
        mic_content = as2utils.canonicalize(as2utils.mimetostring(payload, 0))
        signed_message.attach(payload)
        mic_alg, signature = as2utils.sign_payload(mic_content,
                                                   str(message.organization.signature_key.certificate.path),
                                                   str(message.organization.signature_key.certificate_passphrase))
        signed_message.set_param('micalg', mic_alg)
        signed_message.attach(signature)
        signed_message.as_string()
        as2_content = as2utils.canonicalize(as2utils.extractpayload(signed_message))
        payload = signed_message
        pyas2init.logger.debug('Signed message %s payload as:\n%s' % (message.message_id, payload.as_string()))

    # Encrypt the message if requested in the profile
    if message.partner.encryption:
        models.Log.objects.create(message=message,
                                  status='S',
                                  text=_(u'Encrypting the message using partner key {0:s}'.format(
                                      message.partner.encryption_key)))
        message.encrypted = True
        payload = as2utils.encrypt_payload(as2utils.canonicalize(as2utils.mimetostring(payload, 0)),
                                           message.partner.encryption_key.certificate.path,
                                           message.partner.encryption)
        payload.set_type('application/pkcs7-mime')
        as2_content = payload.get_payload()
        pyas2init.logger.debug('Encrypted message %s payload as:\n%s' % (message.message_id, payload.as_string()))

    # If MDN is to be requested from the partner, set the appropriate headers
    if message.partner.mdn:
        as2_header['disposition-notification-to'] = 'no-reply@pyas2.com'
        if message.partner.mdn_sign:
            as2_header['disposition-notification-options'] = u'signed-receipt-protocol=required, ' \
                                                             u'pkcs7-signature; ' \
                                                             u'signed-receipt-micalg=optional, ' \
                                                             u'%s' % message.partner.mdn_sign
        message.mdn_mode = 'SYNC'
        if message.partner.mdn_mode == 'ASYNC':
            as2_header['receipt-delivery-option'] = pyas2init.gsettings['mdn_url']
            message.mdn_mode = 'ASYNC'

    # If MIC content is set, i.e. message has been signed then calulcate the MIC
    if mic_content:
        pyas2init.logger.debug("Calculating MIC with alg %s for content:\n%s" % (mic_alg, mic_content))
        calculate_mic = getattr(hashlib, mic_alg.replace('-', ''), hashlib.sha1)
        message.mic = calculate_mic(mic_content).digest().encode('base64').strip()

    # Extract the As2 headers as a string and save it to the message object
    as2_header.update(payload.items())
    message.headers = ''
    for key in as2_header:
        message.headers += '%s: %s\n' % (key, as2_header[key])
    message.save()

    models.Log.objects.create(message=message,
                              status='S',
                              text=_(u'AS2 message has been built successfully, sending it to the partner'))
    return as2_content


def send_message(message, payload):
    """ Sends the AS2 message to the partner. Takes the message and payload as arguments and posts the as2 message to
     the partner."""

    try:
        # Parse the message header to a dictionary
        header_parser = HeaderParser()
        message_header = header_parser.parsestr(message.headers)

        # Set up the http auth if specified in the partner profile
        auth = None
        if message.partner.http_auth:
            auth = (message.partner.http_auth_user, message.partner.http_auth_pass)
        verify = True
        if message.partner.https_ca_cert:
            verify = message.partner.https_ca_cert.path

        # Send the AS2 message to the partner
        try:
            response = requests.post(message.partner.target_url,
                                     auth=auth,
                                     verify=verify,
                                     headers=dict(message_header.items()),
                                     data=payload)
            response.raise_for_status()
        except Exception, e:
            # Send mail here
            as2utils.senderrorreport(message, _(u'Failure during transmission of message to partner with error '
                                                u'"%s".\n\nTo retry transmission run the management '
                                                u'command "retryfailedas2comms".' % e))
            message.status = 'R'
            models.Log.objects.create(message=message, status='E', text=_(u'Message send failed with error %s' % e))
            return
        models.Log.objects.create(message=message, status='S', text=_(u'AS2 message successfully sent to partner'))

        # Process the MDN based on the partner profile settings
        if message.partner.mdn:
            if message.partner.mdn_mode == 'ASYNC':
                models.Log.objects.create(message=message, status='S',
                                          text=_(u'Requested ASYNC MDN from partner, waiting for it ........'))
                message.status = 'P'
                return
            # In case of Synchronous MDN the response content will be the MDN. So process it.
            # Get the response headers, convert key to lower case for normalization
            mdn_headers = dict((k.lower().replace('_', '-'), response.headers[k]) for k in response.headers)
            # create the mdn content with message-id and content-type header and response content
            mdn_content = '%s: %s\n' % ('message-id', mdn_headers['message-id'])
            mdn_content += '%s: %s\n\n' % ('content-type', mdn_headers['content-type'])
            mdn_content += response.content
            models.Log.objects.create(message=message, status='S', text=_(u'Synchronous mdn received from partner'))
            pyas2init.logger.debug('Synchronous MDN for message %s received:\n%s' % (message.message_id, mdn_content))
            save_mdn(message, mdn_content)
        else:
            message.status = 'S'
            models.Log.objects.create(message=message,
                                      status='S',
                                      text=_(u'No MDN needed, File Transferred successfully to the partner'))

            # Run the post successful send command
            run_post_send(message)
    finally:
        message.save()


def save_mdn(message, mdn_content):
    """ Process the received MDN and check status of sent message. Takes the raw mdn as input, verifies the signature
    if present and the extracts the status of the original message."""

    try:
        # Parse the raw mdn to an email.Message
        mdn_message = email.message_from_string(mdn_content)
        mdn_headers = ''
        for key in mdn_message.keys():
            mdn_headers += '%s: %s\n' % (key, mdn_message[key])
        message_id = mdn_message.get('message-id')

        # Raise error if message is not an MDN
        if mdn_message.get_content_type() not in ['multipart/signed', 'multipart/report']:
            raise as2utils.As2Exception(_(u'MDN report not found in the response'))

        # Raise error if signed MDN requested and unsigned MDN returned
        if message.partner.mdn_sign and mdn_message.get_content_type() != 'multipart/signed':
            models.Log.objects.create(message=message,
                                      status='W',
                                      text=_(u'Expected signed MDN but unsigned MDN returned'))

        mdn_signed = False
        if mdn_message.get_content_type() == 'multipart/signed':
            # Verify the signature in the MDN message
            models.Log.objects.create(message=message,
                                      status='S',
                                      text=_(u'Verifying the signed MDN with partner key {0:s}'.format(
                                          message.partner.signature_key)))
            mdn_signed = True

            # Get the partners public and ca certificates
            cert = str(message.partner.signature_key.certificate.path)
            ca_cert = cert
            if message.partner.signature_key.ca_cert:
                ca_cert = str(message.partner.signature_key.ca_cert.path)
            verify_cert = message.partner.signature_key.verify_cert

            # main_boundary = '--' + mdn_message.get_boundary()
            # Extract the signed message and signature
            for part in mdn_message.get_payload():
                if part.get_content_type().lower() == "application/pkcs7-signature":
                    sig = part
                else:
                    mdn_message = part

            # check if signature is base64 encoded and if not encode
            # try:
            #     raw_sig = sig.get_payload().encode('ascii').strip()
            # except Exception, e:
            #     raw_sig = sig.get_payload().encode('base64').strip()

            # Verify the signature using raw MDN content
            try:
                as2utils.verify_payload(mdn_content, None, cert, ca_cert, verify_cert)
            except Exception, e:
                # TODO: Verify using extracted message and signature
                raise as2utils.As2Exception(_(u'MDN Signature Verification Error, exception message is %s' % e))

        # Save the MDN to the store
        filename = message_id.strip('<>') + '.mdn'
        full_filename = as2utils.storefile(pyas2init.gsettings['mdn_receive_store'],
                                           filename,
                                           as2utils.extractpayload(mdn_message),
                                           True)
        message.mdn = models.MDN.objects.create(message_id=message_id.strip('<>'),
                                                file=full_filename,
                                                status='R',
                                                headers=mdn_headers,
                                                signed=mdn_signed)

        # Process the MDN report to extract the AS2 message status
        if mdn_message.get_content_type() == 'multipart/report':
            for part in mdn_message.walk():
                if part.get_content_type() == 'message/disposition-notification':
                    pyas2init.logger.debug('Found MDN report for message %s:\n%s' % (message.message_id,
                                                                                     part.as_string()))
                    models.Log.objects.create(message=message,
                                              status='S',
                                              text=_(u'Checking the MDN for status of the message'))
                    mdn = part.get_payload().pop()
                    mdn_status = mdn.get('Disposition').split(';')
                    # Check the status of the AS2 message
                    if mdn_status[1].strip() == 'processed':
                        models.Log.objects.create(message=message,
                                                  status='S',
                                                  text=_(u'Message has been successfully processed, '
                                                         u'verifying the MIC if present.'))
                        # Compare the MIC of the received message
                        if mdn.get('Received-Content-MIC') and message.mic:
                            mdn_mic = mdn.get('Received-Content-MIC').split(',')
                            if message.mic != mdn_mic[0]:
                                message.status = 'W'
                                models.Log.objects.create(message=message,
                                                          status='W',
                                                          text=_(u'Message Integrity check failed, please validate '
                                                                 u'message content with your partner'))
                            else:
                                message.status = 'S'
                                models.Log.objects.create(message=message,
                                                          status='S',
                                                          text=_(u'File Transferred successfully to the partner'))
                        else:
                            message.status = 'S'
                            models.Log.objects.create(message=message,
                                                      status='S',
                                                      text=_(u'File Transferred successfully to the partner'))

                        # Run the post successful send command
                        run_post_send(message)
                    else:
                        raise as2utils.As2Exception(_(u'Partner failed to process file. '
                                                      u'MDN status is %s' % mdn.get('Disposition')))
        else:
            raise as2utils.As2Exception(_(u'MDN report not found in the response'))
    finally:
        message.save()


def run_post_send(message):
    """ Execute command after successful send, can be used to notify successful sends """

    command = message.partner.cmd_send
    if command:
        models.Log.objects.create(message=message, status='S', text=_(u'Execute command post successful send'))
        # Create command template and replace variables in the command
        command = Template(command)
        variables = {
            'filename': message.payload.name,
            'sender': message.organization.as2_name,
            'recevier': message.partner.as2_name,
            'messageid': message.message_id
        }
        variables.update(dict(HeaderParser().parsestr(message.headers).items()))

        # Execute the command
        os.system(command.safe_substitute(variables))


def run_post_receive(message, full_filename):
    """ Execute command after successful receive, can be used to call the edi program for further processing"""

    command = message.partner.cmd_receive
    if command:
        models.Log.objects.create(message=message, status='S', text=_(u'Execute command post successful receive'))
        # Create command template and replace variables in the command
        command = Template(command)
        variables = {
            'filename': message.payload.name,
            'fullfilename': full_filename,
            'sender': message.organization.as2_name,
            'recevier': message.partner.as2_name,
            'messageid': message.message_id
        }
        variables.update(dict(HeaderParser().parsestr(message.headers).items()))

        # Execute the command
        os.system(command.safe_substitute(variables))
