import datetime
from django import template
from pyas2 import pyas2init

register = template.Library()

@register.simple_tag
def get_init(key):
    return pyas2init.gsettings.get(key,'')    
