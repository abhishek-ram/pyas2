from django import template
from pyas2 import pyas2init

register = template.Library()


@register.simple_tag
def get_init(key):
    return pyas2init.gsettings.get(key,'')


def easy_tag(func):
    """deal with the repetitive parts of parsing template tags"""

    def inner(parser, token):
        # print token
        try:
            return func(*token.split_contents())
        except TypeError:
            raise template.TemplateSyntaxError(
                'Bad arguments for tag "%s"' % token.split_contents()[0])

    inner.__name__ = func.__name__
    inner.__doc__ = inner.__doc__
    return inner


class AppendGetNode(template.Node):
    def __init__(self, dict):
        self.dict_pairs = {}
        for pair in dict.split(','):
            pair = pair.split('=')
            self.dict_pairs[pair[0]] = template.Variable(pair[1])

    def render(self, context):
        request = context['request']
        get = request.GET.copy()
        for k, v in self.dict_pairs.items():
            get[k] = v.resolve(context)
        return "%s?%s" % (request.path, get.urlencode())


@register.tag()
@easy_tag
def append_to_get(_tag_name, q_dict):
    return AppendGetNode(q_dict)
