import re, os, sys
import email.utils
import email.message
import codecs
import collections
import zlib
from pyasn1.type import univ, namedtype, tag, namedval, constraint
from pyasn1.codec.ber import encoder, decoder
from M2Crypto import BIO, Rand, SMIME, X509
from cStringIO import StringIO
from email.generator import Generator

key_pass = ''

class AS2Error(Exception):
    ''' formats the error messages. Under all circumstances: give (reasonable) output, no errors.
        input (msg,*args,**kwargs) can be anything: strings (any charset), unicode, objects. Note that these are errors, so input can be 'not valid'!
        to avoid the risk of 'errors during errors' catch-all solutions are used.
        2 ways to raise Exceptions:
        - AS2Error('tekst %(var1)s %(var2)s',{'var1':'value1','var2':'value2'})  ###this one is preferred!!
        - AS2Error('tekst %(var1)s %(var2)s',var1='value1',var2='value2')
    '''
    def __init__(self, msg,*args,**kwargs):
        self.msg = safe_unicode(msg)
        if args:    ##expect args[0] to be a dict
            if isinstance(args[0],dict):
                xxx = args[0]
            else:
                xxx = {}
        else:
            xxx = kwargs
        self.xxx = collections.defaultdict(unicode)     #catch-all if var in string is not there
        for key,value in xxx.iteritems():
            self.xxx[safe_unicode(key)] = safe_unicode(value)
    def __unicode__(self):
        try:
            return self.msg % self.xxx
        except Exception as msg:
            #print "-----",type(msg),msg
            return u'Error while displaying error'
    def __str__(self):
        return self.__unicode__()

def safe_unicode(value):
    ''' For errors: return best possible unicode...should never lead to errors.
    '''
    try:
        if isinstance(value, unicode):      #is already unicode, just return
            return value
        elif isinstance(value, str):        #string, encoding unknown.
            for charset in ['utf_8','latin_1']:
                try:
                    return value.decode(charset, 'strict')  #decode strict
                except:
                    continue
            return value.decode('utf_8', 'ignore')  #decode as if it is utf-8, ignore errors.
        else:
            return unicode(value)
    except:
        try:
            return repr(value)
        except:
            return u'Error while displaying error'

def join(*paths):
    '''Does does more as join.....
        - join the paths (compare os.path.join)
        - if path is not absolute, interpretate this as relative from bots directory.
        - normalize'''
    return str(os.path.normpath(os.path.join(*paths)))

def dirshouldbethere(path):
    if path and not os.path.exists(path):
        os.makedirs(path)
        return True
    return False

def abspath(soort,filename):
    ''' get absolute path for internal files; path is a section in bots.ini '''
    directory = botsglobal.ini.get('directories',soort)
    return join(directory,filename)

def abspathdata(filename):
    ''' abspathdata if filename incl dir: return absolute path; else (only filename): return absolute path (datadir)'''
    if '/' in filename: #if filename already contains path
        return join(filename)
    else:
        directory = botsglobal.ini.get('directories','data')
        datasubdir = filename[:-3]
        if not datasubdir:
            datasubdir = '0'
        return join(directory,datasubdir,filename)

def deldata(filename):
    ''' delete internal data file.'''
    filename = abspathdata(filename)
    try:
        os.remove(filename)
    except:
        #~ print 'not deleted', filename
        pass

def opendata(filename,mode,charset=None,errors='strict'):
    ''' open internal data file. if no encoding specified: read file raw/binary.'''
    #filename = abspathdata(filename)
    if 'w' in mode:
        dirshouldbethere(os.path.dirname(filename))
    if charset:
        return codecs.open(filename,mode,charset,errors)
    else:
        return open(filename,mode)

def readdata(filename,charset=None,errors='strict'):
    ''' read internal data file in memory using the right encoding or no encoding'''
    filehandler = opendata(filename,'rb',charset,errors)
    content = filehandler.read()
    filehandler.close()
    return content


def unescape_as2name(ename):
	#uename = re.sub(r'^"|"$', "", ename)
	#uename = re.sub(r'\\\\','\\', uename)
	#uename = re.sub(r'\\"','"', uename)
	return email.utils.unquote(ename)

def escape_as2name(uename):
	if re.search( r'[\\" ]', uename, re.M):
		#ename = re.sub(r'\\', '\\\\\\\\', ename)
		#ename = re.sub(r'"', '\\"', ename)
		return '"' + email.utils.quote(uename) + '"'
	else:
		return uename	

def extractpayload(message, **kwargs):
    if message.is_multipart():
         headerlen = kwargs.get('headerlen', 78)
         messagestr = mimetostring(message, headerlen) #.replace('\n','\r\n')
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

def canonicalize(msg):
    result = ''
    header = list()
    for key,value in msg.items():
        header.append("%s: %s"%(key,value))
    result = "%s\r\n\r\n%s"%("\r\n".join(header),extractpayload(msg))
    return result

## Classes that define the ASN.1 structure for building  smime compressed message
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
        namedtype.NamedType('content',Content()),
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
    cdata_attr.setComponentByName('compressionAlgorithm',(1,2,840,113549,1,9,16,3,8))
    cdata_payload = CompressedDataPayload()
    cdata_payload.setComponentByName('content-type',(1,2,840,113549,1,7,1))
    cdata_payload.setComponentByName('content',Content(univ.OctetString(hexValue=zlib.compress(payload).encode('hex'))))
    cdata = CompressedData()
    cdata.setComponentByName('version',0)
    cdata.setComponentByName('attributes',cdata_attr)
    cdata.setComponentByName('payload',cdata_payload)
    #cdata_payload.setComponentByName('enum', 'no-error')
    cdata_main = CompressedDataMain()
    cdata_main.setComponentByName('id-ct-compressedData',(1,2,840,113549,1,9,16,1,9))
    cdata_main.setComponentByName('compressedData',cdata)
    return encoder.encode(cdata_main,defMode=False).encode('base64')

def decompress_payload(payload):
    decoded_content,substrate = decoder.decode(payload,asn1Spec=CompressedDataMain())
    compressed_content = decoded_content.getComponentByName('compressedData').getComponentByName('payload').getComponentByName('content')
    return zlib.decompress(compressed_content.asOctets())

def encrypt_payload(payload, key, cipher):
    encrypter = SMIME.SMIME()
    certificate = X509.X509_Stack()
    certificate.push(X509.load_cert(key))
    encrypter.set_x509_stack(certificate)
    encrypter.set_cipher(SMIME.Cipher(cipher))
    encryptedContent = encrypter.encrypt(BIO.MemoryBuffer(payload))
    out = BIO.MemoryBuffer()
    encrypter.write(out, encryptedContent)
    return email.message_from_string(out.read())

def decrypt_payload(payload, key, passphrase):
    global key_pass
    key_pass = passphrase
    privkey = SMIME.SMIME()
    privkey.load_key(key, callback=getKeyPassphrase)
    # Load the encrypted data.
    p7, data = SMIME.smime_load_pkcs7_bio(BIO.MemoryBuffer(payload))
    return privkey.decrypt(p7)

def sign_payload(data, key, passphrase):
    global key_pass
    key_pass = passphrase
    signature = email.Message.Message()
    signer = SMIME.SMIME()
    signer.load_key(key, callback=getKeyPassphrase)
    sign = signer.sign(BIO.MemoryBuffer(data),SMIME.PKCS7_DETACHED)
    out = BIO.MemoryBuffer()
    sign.write(out)	
    raw_sig = out.read().replace('-----BEGIN PKCS7-----\n','').replace('-----END PKCS7-----\n', '').replace('\n', '')
    signature.set_type('application/pkcs7-signature')
    signature.set_param('name', 'smime.p7s')
    signature.set_param('smime-type', 'signed-data')
    signature.add_header('Content-Disposition', 'attachment', filename='smime.p7s')
    signature.add_header('Content-Transfer-Encoding', 'base64')
    signature.set_payload('\n'.join(raw_sig[pos:pos+76] for pos in xrange(0, len(raw_sig), 76)))
    #signature.set_payload(out.read().replace('-----BEGIN PKCS7-----\n','').replace('-----END PKCS7-----\n', ''))
    del signature['MIME-Version']
    return signature

def verify_payload(msg, raw_sig, key):
    signer = SMIME.SMIME()
    signerKey = X509.X509_Stack()
    signerKey.push(X509.load_cert(key))
    signer.set_x509_stack(signerKey)
    signerStore = X509.X509_Store()
    signerStore.load_info(key)
    signer.set_x509_store(signerStore)
    if raw_sig:
	raw_sig.strip()
        sig = "-----BEGIN PKCS7-----\n%s\n-----END PKCS7-----\n"%raw_sig.replace('\r\n','\n')
        p7 = SMIME.load_pkcs7_bio(BIO.MemoryBuffer(sig))
        data_bio = BIO.MemoryBuffer(msg)
        signer.verify(p7, data_bio,SMIME.PKCS7_NOVERIFY)
    else:
	p7, data_bio = SMIME.smime_load_pkcs7_bio(BIO.MemoryBuffer(msg))
	signer.verify(p7, data_bio,SMIME.PKCS7_NOVERIFY)

def getKeyPassphrase(self):
    return key_pass
