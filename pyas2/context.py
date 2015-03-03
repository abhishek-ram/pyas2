from django.conf import settings
from pyas2 import init
def set_context(request):
    ''' set variables in the context of templates.
    '''
    my_context = init.gsettings
    my_context['minDate'] = 0 - my_context['max_arch_days']
    return my_context 
