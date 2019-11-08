"""

"""
from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter(name='get_class')
def get_class(value):
    return value.__class__.__name__


@register.filter
def content_type_id(obj):
    if not obj:
        return False
    return ContentType.objects.get_for_model(obj).pk


@register.filter
def content_type(obj):
    if not obj:
        return False
    return ContentType.objects.get_for_model(obj).name


@register.filter
def verbose_name(obj):
    return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
    return obj._meta.verbose_name_plural
