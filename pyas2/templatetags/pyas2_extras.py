import datetime
from django import template
from pyas2 import init

register = template.Library()

@register.simple_tag
def get_init(key):
    return init.gsettings.get(key,'')    
