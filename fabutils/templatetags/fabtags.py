"""
Collection of template tags usefull in fab projects
"""

import re

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    """
    Construct a GET query url with a parameter keeping other values
    """
    request = context['request']
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    """
    Check if link is active
    Usage : class='(% active 'blog:news-list'%)' will be replace by class='active'
            if current url is 'blog:news-list'
    """
    try:
        pattern = '^' + reverse(pattern_or_urlname) + '$'
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].get_full_path()
    if re.search(pattern, path):
        return 'active'
    return ''


@register.simple_tag
def mod(value, arg):
    result = value % arg
    return result


register.filter('mod', mod)


@register.simple_tag(takes_context=True)
def url_replace_with_inverse(context, field):
    """
    Construct a GET query url with a parameter keeping other values and inversing existing for ordering purposes
    """

    request = context['request']
    dict_ = request.GET.copy()
    if field in dict_.get('order', ''):
        if dict_['order'].startswith('-'):
            dict_['order'] = field
        else:
            dict_['order'] = '-' + field
    else:
        dict_['order'] = field

    return dict_.urlencode()


@register.filter
def filename(value):
    import os
    return os.path.basename(value.file.name)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
