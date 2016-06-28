import datetime
import urllib
import xml.dom.minidom
import re


def datetimefrom():
    terug = datetime.datetime.today() - datetime.timedelta(days=30)
    return terug.strftime('%Y-%m-%d 00:00:00')


def datetimeuntil():
    terug = datetime.datetime.today()
    return terug.strftime('%Y-%m-%d 23:59:59')


def url_with_querystring(path, **kwargs):
    return path + '?' + urllib.urlencode(kwargs)


def indent_x12(content):
    if content.count('\n') > 6:
        return content
    count = 0
    for char in content[:200].lstrip():
        if char in '\r\n' and count != 105:  # pos 105: is record_sep, could be \r\n
            continue
        count += 1
        if count == 106:
            sep = char
            break
    else:
        return content
    if sep.isalnum() or sep.isspace():
        return content
    return content.replace(sep, sep + '\n')

EDIFACT_INDENT = re.compile('''
    (?<!\?)     #if no preceding escape (?)
    '           #apostrophe
    (?![\n\r])  #if no following CR of LF
    ''', re.VERBOSE)


def indent_edifact(content):
    return EDIFACT_INDENT.sub("'\n", content)


def indent_xml(content):
    this_xml = xml.dom.minidom.parseString(content)
    return this_xml.toprettyxml()
