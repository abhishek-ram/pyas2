from django.test import TestCase, Client
from pyas2 import models
from pyas2 import as2lib
from email import utils as emailutils
from email.parser import HeaderParser
from itertools import izip
import os

TEST_DIR = os.path.join((os.path.dirname(
    os.path.abspath(__file__))),  'fixtures')


class AS2SendReceiveTest(TestCase):
    """Test cases for the AS2 server and client.
    We will be testing each permutation as defined in RFC 4130 Section 2.4.2
    """
    @classmethod
    def setUpTestData(cls):
        # Every test needs a client.
        cls.client = Client()
        cls.header_parser = HeaderParser()

        # Load the client and server certificates
        cls.server_key = models.PrivateCertificate.objects.create(
            certificate=os.path.join(TEST_DIR, 'as2server.pem'),
            certificate_passphrase='password'
        )
        cls.server_crt = models.PublicCertificate.objects.create(
            certificate=os.path.join(TEST_DIR, 'as2server.crt')
        )
        cls.client_key = models.PrivateCertificate.objects.create(
            certificate=os.path.join(TEST_DIR, 'as2client.pem'),
            certificate_passphrase='password'
        )
        cls.client_crt = models.PublicCertificate.objects.create(
            certificate=os.path.join(TEST_DIR, 'as2client.crt')
        )

        # Setup the server organization and partner
        models.Organization.objects.create(
            name='Server Organization',
            as2_name='as2server',
            encryption_key=cls.server_key,
            signature_key=cls.server_key
        )
        models.Partner.objects.create(
            name='Server Partner',
            as2_name='as2client',
            target_url='http://localhost:8080/pyas2/as2receive',
            compress=False,
            mdn=False,
            signature_key=cls.client_crt,
            encryption_key=cls.client_crt
        )

        # Setup the client organization and partner
        cls.organization = models.Organization.objects.create(
            name='Client Organization',
            as2_name='as2client',
            encryption_key=cls.client_key,
            signature_key=cls.client_key
        )

        # Initialise the payload i.e. the file to be transmitted
        cls.payload = models.Payload.objects.create(
            name='testmessage.edi',
            file=os.path.join(TEST_DIR, 'testmessage.edi'),
            content_type='application/edi-consent'
        )

    def testEndpoint(self):
        """ Test if the as2 reveive endpoint is active """

        response = self.client.get('/pyas2/as2receive')
        self.assertEqual(response.status_code, 200)

    def testNoEncryptMessageNoMdn(self):
        """ Test Permutation 1: Sender sends un-encrypted data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testNoEncryptMessageMdn(self):
        """ Test Permutation 2: Sender sends un-encrypted data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testNoEncryptMessageSignMdn(self):
        """ Test Permutation 3: Sender sends un-encrypted data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                mdn=True,
                                                mdn_mode='SYNC',
                                                mdn_sign='sha1',
                                                signature_key=self.server_crt)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageNoMdn(self):
        """ Test Permutation 4: Sender sends encrypted data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageMdn(self):
        """ Test Permutation 5: Sender sends encrypted data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageSignMdn(self):
        """ Test Permutation 6: Sender sends encrypted data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=True,
                                                mdn_mode='SYNC',
                                                mdn_sign='sha1',
                                                signature_key=self.server_crt)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageNoMdn(self):
        """ Test Permutation 7: Sender sends signed data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageMdn(self):
        """ Test Permutation 8: Sender sends signed data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageSignMdn(self):
        """ Test Permutation 9: Sender sends signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageNoMdn(self):
        """ Test Permutation 10: Sender sends encrypted and signed data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageMdn(self):
        """ Test Permutation 11: Sender sends encrypted and signed data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and build the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageSignMdn(self):
        """ Test Permutation 12: Sender sends encrypted and signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testCompressEncryptSignMessageSignMdn(self):
        """ Test Permutation 13: Sender sends compressed, encrypted and signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=True,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageAsyncSignMdn(self):
        """ Test Permutation 14: Sender sends encrypted and signed data and requests an Asynchronous signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url='http://localhost:8080/pyas2/as2receive',
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_mode='ASYNC',
                                                mdn_sign='sha1')

        # Setup the message object and build the message, do not send it
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

        # Process the ASYNC MDN for the in message and check status
        message_headers = self.header_parser.parsestr(out_message.mdn.headers)
        http_headers = {}
        for header in message_headers.keys():
            key = 'HTTP_%s' % header.replace('-', '_').upper()
            http_headers[key] = message_headers[header]
        with open(out_message.mdn.file, 'rb') as mdn_file:
            mdn_content = mdn_file.read()

        # Switch the out and in messages, this is to prevent duplicate message from being picked
        out_message.delete()
        in_message.pk = message_id
        in_message.payload = None
        in_message.save()

        # Send the async mdn and check for its status
        content_type = http_headers.pop('HTTP_CONTENT_TYPE')
        response = self.client.post('/pyas2/as2receive',
                                    data=mdn_content,
                                    content_type=content_type,
                                    **http_headers)
        self.assertEqual(response.status_code, 200)

        in_message = models.Message.objects.get(message_id=message_id)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

    def buildSendMessage(self, message_id, partner):
        """ Function builds the message and posts the request. """

        message = models.Message.objects.create(message_id='%s_IN' % message_id,
                                                partner=partner,
                                                organization=self.organization,
                                                direction='OUT',
                                                status='IP',
                                                payload=self.payload)
        processed_payload = as2lib.build_message(message)

        # Set up the Http headers for the request
        message_headers = self.header_parser.parsestr(message.headers)
        http_headers = {}
        for header in message_headers.keys():
            key = 'HTTP_%s' % header.replace('-', '_').upper()
            http_headers[key] = message_headers[header]
        http_headers['HTTP_MESSAGE_ID'] = message_id
        content_type = http_headers.pop('HTTP_CONTENT_TYPE')
        # Post the request and return the response
        response = self.client.post('/pyas2/as2receive',
                                    data=processed_payload,
                                    content_type=content_type,
                                    **http_headers)
        return message, response

    @staticmethod
    def buildMdn(out_message, response):
        mdn_content = ''
        for key in ['message-id', 'content-type', ]:
            mdn_content += '%s: %s\n' % (key, response[key])
        mdn_content = '%s\n%s' % (mdn_content, response.content)
        as2lib.save_mdn(out_message, mdn_content)

    @staticmethod
    def printLogs(message):
        logs = models.Log.objects.filter(message=message)
        for log in logs:
            print (log.status, log.text)

    @staticmethod
    def compareFiles(filename1, filename2):
        with open(filename1, "rtU") as a:
            with open(filename2, "rtU") as b:
                # Note that "all" and "izip" are lazy
                # (will stop at the first line that's not identical)
                return all(lineA == lineB for lineA, lineB in izip(a.xreadlines(), b.xreadlines()))
