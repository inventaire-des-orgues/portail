from django import forms
from django import template


register = template.Library()


@register.filter
def addcssclass(field, css):
    existing_class = field.field.widget.attrs.get('class', '')
    return field.as_widget(attrs={'class': existing_class + ' ' + css})


@register.filter
def is_hidden(field):
    return isinstance(field.field.widget, forms.HiddenInput)


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


@register.filter
def is_select_multiple(field):
    return isinstance(field.field.widget, forms.SelectMultiple)


@register.filter
def is_date_field(field):
    return isinstance(field.field.widget, forms.DateTimeInput) or isinstance(field.field.widget, forms.DateInput)


@register.filter
def get_form_field(form, key):
    for element in form:
        if element.name == key:
            return element
    return None
