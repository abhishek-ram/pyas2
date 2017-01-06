import re
import os
import email
import codecs
import collections
import zlib
import time
import traceback
from django.utils.translation import ugettext as _
from pyasn1.type import univ, namedtype, tag
from pyasn1.codec.ber import encoder, decoder
from M2Crypto import BIO, SMIME, X509
from cStringIO import StringIO
from email.generator import Generator

key_pass = ''

# **********************************************************/**
# *************************Logging, Error handling********************/**
# **********************************************************/**


def senderrorreport(message, errortext):
    """ Send an email in case of errors or problems with send/receive.
        Email parameters are in settings.py (EMAIL_HOST, etc).
    """
    from django.core.mail import mail_managers
    from pyas2 import pyas2init
    try:
        subject = _(u'[pyAS2 Error Report] %(time)s') % {'time': str(message.timestamp)[:16]}
        reporttext = _(u'pyAS2 Report; \nmessage: %(mid)s, \ntime: %(time)s, '
                       u'\ndirection: %(dir)s, \npartner: %(prt)s, \norganization: '
                       u'%(org)s\n\n') % {'time': str(message.timestamp)[:19],
                                          'mid': message.message_id,
                                          'dir': message.get_direction_display(),
                                          'prt': message.partner,
                                          'org': message.organization}
        reporttext += '\nError Message:%s' % errortext
        mail_managers(subject, reporttext)
    except Exception as msg:
        pyas2init.logger.warning(u'Error in sending error report: %(msg)s', {'msg': msg})


def txtexc(mention_exception_type=True):
    """ Process last exception, get an errortext.
        Errortext should be valid unicode.
    """
    from pyas2 import pyas2init
    if pyas2init.gsettings['log_level'] == 'DEBUG':
        return safe_unicode(traceback.format_exc(limit=None))
    else:
        terug = safe_unicode(traceback.format_exc(limit=0))
        terug = terug.replace(u'Traceback (most recent call last):\n', u'')
        if not mention_exception_type:
            terug = terug.partition(': ')[2]
        return terug


def safe_unicode(value):
    """ For errors: return best possible unicode...should never lead to errors."""
    try:
        if isinstance(value, unicode):      # is already unicode, just return
            return value            
        elif isinstance(value, str):        # string, encoding unknown.
            for charset in ['utf_8', 'latin_1']:
                try:
                    return value.decode(charset, 'strict')  # decode strict
                except:
                    continue
            return value.decode('utf_8', 'ignore')  # decode as if it is utf-8, ignore errors.
        else:
            return unicode(value)
    except:
        try:
            return repr(value)
        except:
            return u'Error while displaying error'

# **********************************************************/**
# **************  Exception classes ***************************
# **********************************************************/**


class AS2Error(Exception):
    """ formats the error messages. Under all circumstances: give (reasonable) output, no errors.
        input (msg,*args,**kwargs) can be anything: strings (any charset), unicode, objects.
        Note that these are errors, so input can be 'not valid'!
        to avoid the risk of 'errors during errors' catch-all solutions are used.
        2 ways to raise Exceptions:
        - AS2Error('tekst %(var1)s %(var2)s',{'var1':'value1','var2':'value2'})  ###this one is preferred!!
        - AS2Error('tekst %(var1)s %(var2)s',var1='value1',var2='value2')
    """
    def __init__(self, msg, *args, **kwargs):
        self.msg = safe_unicode(msg)
        if args:    # expect args[0] to be a dict
            if isinstance(args[0], dict):
                xxx = args[0]
            else:
                xxx = {}
        else:
            xxx = kwargs
        self.xxx = collections.defaultdict(unicode)     # catch-all if var in string is not there
        for key, value in xxx.iteritems():
            self.xxx[safe_unicode(key)] = safe_unicode(value)

    def __unicode__(self):
        try:
            return self.msg % self.xxx
        except Exception:
            # print "-----",type(msg),msg
            return u'Error while displaying error'

    def __str__(self):
        return self.__unicode__()


class As2Exception(AS2Error):
    pass


class As2DuplicateDocument(AS2Error):
    pass


class As2PartnerNotFound(AS2Error):
    pass


class As2InsufficientSecurity(AS2Error):
    pass


class As2DecompressionFailed(AS2Error):
    pass


class As2DecryptionFailed(AS2Error):
    pass


class As2InvalidSignature(AS2Error):
    pass

# **********************************************************/**
# *************************File handling os.path etc***********************/**
# **********************************************************/**


def join(*paths):
    """Does does more as join.....
        - join the paths (compare os.path.join)
        - if path is not absolute, interpretate this as relative from bots directory.
        - normalize"""
    return str(os.path.normpath(os.path.join(*paths)))


def dirshouldbethere(path):
    if path and not os.path.exists(path):
        os.makedirs(path)
        return True
    return False


def opendata(filename, mode, charset=None, errors='strict'):
    """ open internal data file. if no encoding specified: read file raw/binary."""
    # filename = abspathdata(filename)
    if 'w' in mode:
        dirshouldbethere(os.path.dirname(filename))
    if charset:
        return codecs.open(filename, mode, charset, errors)
    else:
        return open(filename, mode)


def readdata(filename, charset=None, errors='strict'):
    """ read internal data file in memory using the right encoding or no encoding"""
    filehandler = opendata(filename, 'rb', charset, errors)
    content = filehandler.read()
    filehandler.close()
    return content


def storefile(targetdir, filename, content, archive):
    """ Save data to file system and optionally add date as sub directory for archiving"""
    if archive:
        targetdir = join(targetdir, time.strftime('%Y%m%d'))
    dirshouldbethere(targetdir)
    if os.path.isfile(join(targetdir, filename)):
        filename = os.path.splitext(filename)[0] + time.strftime('_%H%M%S') + os.path.splitext(filename)[1]
    absfilename = join(targetdir, filename)
    sfile = open(absfilename, 'wb')
    sfile.write(content)
    sfile.close()
    return absfilename
 
# **********************************************************/**
# ************************MIME Helper Functions***********************/**
# **********************************************************/**


def unescape_as2name(ename):
    return email.utils.unquote(ename)


def escape_as2name(uename):
    if re.search(r'[\\" ]', uename, re.M):
        return '"' + email.utils.quote(uename) + '"'
    else:
        return uename


def extractpayload(message, **kwargs):
    if message.is_multipart():
        headerlen = kwargs.get('headerlen', 78)
        messagestr = mimetostring(message, headerlen)  # .replace('\n','\r\n')
        boundary = '--' + message.get_boundary()
        temp = messagestr.split(boundary)
        temp.pop(0)
        return boundary + boundary.join(temp)
    else:
        return message.get_payload()


def mimetostring(msg, headerlen):
    fp = StringIO()
    g = Generator(fp, mangle_from_=False, maxheaderlen=headerlen)
    g.flatten(msg)
    return fp.getvalue()


def extractpayload_fromstring1(msg, boundary):
    return msg.split(boundary)[1].strip()


def extractpayload_fromstring2(msg, boundary):
    crlf_fixed = re.sub('\r\n\r\n$', '\r\n', msg.split(boundary)[1].lstrip())
    crlf_fixed = re.sub('\n\r\n$', '\n', crlf_fixed)
    crlf_fixed = re.sub('\r\r\n$', '\r', crlf_fixed)
    return crlf_fixed


def canonicalize2(msg):
    header = list()
    for key, value in msg.items():
        header.append("%s: %s" % (key, value))
    result = "%s\r\n\r\n%s" % ("\r\n".join(header), extractpayload(msg))
    return result


def canonicalize(msg):
    return msg.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')

# **********************************************************/**
# *************************Smime Functions such as compress, encrypt..***********************/**
# **********************************************************/**


# Classes that define the ASN.1 structure for building  smime compressed message
class CompressedDataAttr(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('compressionAlgorithm', univ.ObjectIdentifier()),
    )


class Content(univ.OctetString):
    tagSet = univ.OctetString.tagSet.tagExplicitly(
        tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0)
    )


class CompressedDataPayload(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('content-type', univ.ObjectIdentifier()),
        namedtype.NamedType('content', Content()),
    )


class CompressedData(univ.Sequence):
    tagSet = univ.Sequence.tagSet.tagExplicitly(
        tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0)
    )
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('version', univ.Integer()),
        namedtype.NamedType('attributes', CompressedDataAttr()),
        namedtype.NamedType('payload', CompressedDataPayload()),
    )


class CompressedDataMain(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('id-ct-compressedData', univ.ObjectIdentifier()),
        namedtype.NamedType('compressedData', CompressedData()),
    )


def compress_payload(payload):
    cdata_attr = CompressedDataAttr()
    cdata_attr.setComponentByName('compressionAlgorithm', (1, 2, 840, 113549, 1, 9, 16, 3, 8))
    cdata_payload = CompressedDataPayload()
    cdata_payload.setComponentByName('content-type', (1, 2, 840, 113549, 1, 7, 1))
    cdata_payload.setComponentByName('content',
                                     Content(univ.OctetString(hexValue=zlib.compress(payload).encode('hex'))))
    cdata = CompressedData()
    cdata.setComponentByName('version', 0)
    cdata.setComponentByName('attributes', cdata_attr)
    cdata.setComponentByName('payload', cdata_payload)
    cdata_main = CompressedDataMain()
    cdata_main.setComponentByName('id-ct-compressedData', (1, 2, 840, 113549, 1, 9, 16, 1, 9))
    cdata_main.setComponentByName('compressedData', cdata)
    return encoder.encode(cdata_main, defMode=False).encode('base64')


def decompress_payload(payload):
    decoded_content, substrate = decoder.decode(payload, asn1Spec=CompressedDataMain())
    compressed_content = decoded_content.getComponentByName('compressedData').getComponentByName('payload').\
        getComponentByName('content')
    return zlib.decompress(compressed_content.asOctets())


def encrypt_payload(payload, key, cipher):
    encrypter = SMIME.SMIME()
    certificate = X509.X509_Stack()
    certificate.push(X509.load_cert(key))
    encrypter.set_x509_stack(certificate)
    encrypter.set_cipher(SMIME.Cipher(cipher))
    encrypted_content = encrypter.encrypt(BIO.MemoryBuffer(payload), SMIME.PKCS7_BINARY)
    out = BIO.MemoryBuffer()
    encrypter.write(out, encrypted_content)
    return email.message_from_string(out.read())


def decrypt_payload(payload, key, passphrase):
    global key_pass
    key_pass = passphrase
    privkey = SMIME.SMIME()
    privkey.load_key(key, callback=get_key_passphrase)
    # Load the encrypted data.
    p7, data = SMIME.smime_load_pkcs7_bio(BIO.MemoryBuffer(payload))
    return privkey.decrypt(p7)


def sign_payload(data, key, passphrase):
    global key_pass
    key_pass = passphrase
    mic_alg, signature = None, None

    # Sign the message with the key provided
    signer = SMIME.SMIME()
    signer.load_key(key, callback=get_key_passphrase)
    sign = signer.sign(BIO.MemoryBuffer(data), SMIME.PKCS7_DETACHED)
    out = BIO.MemoryBuffer()
    buf = BIO.MemoryBuffer(data)
    signer.write(out, sign, buf)

    # Get the micalg from the signed message
    signed_message = email.message_from_string(out.read())
    mic_alg = signed_message.get_param('micalg')

    # Extract the raw signature from the signed message
    for part in signed_message.get_payload():
        if part.get_content_type() in ['application/pkcs7-signature', 'application/x-pkcs7-signature']:
            part.set_type('application/pkcs7-signature')
            signature = part
    return mic_alg, signature


def verify_payload(msg, raw_sig, cert, ca_cert, verify_cert):
    # Load the public certificate of the signer
    signer = SMIME.SMIME()
    signer_key = X509.X509_Stack()
    signer_key.push(X509.load_cert(cert))
    signer.set_x509_stack(signer_key)
    signer_store = X509.X509_Store()
    signer_store.load_info(ca_cert)
    signer.set_x509_store(signer_store)

    # Extract the pkcs7 signature and the data
    if raw_sig:
        raw_sig.strip()
        sig = "-----BEGIN PKCS7-----\n%s\n-----END PKCS7-----\n" % raw_sig.replace('\r\n', '\n')
        p7 = SMIME.load_pkcs7_bio(BIO.MemoryBuffer(sig))
        data_bio = BIO.MemoryBuffer(msg)
    else:
        p7, data_bio = SMIME.smime_load_pkcs7_bio(BIO.MemoryBuffer(msg))

    # Verify the signature against the message
    if verify_cert:
        signer.verify(p7, data_bio)
    else:
        # Don't verify the signer certificate if this flag is set
        signer.verify(p7, data_bio, SMIME.PKCS7_NOVERIFY)


def get_key_passphrase(self):
    return key_pass
