# core/templatetags/markdown_extras.py
import markdown
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
@stringfilter
def markdown_format(value):
    """
    Converts a string from Markdown to HTML.
    """
    return mark_safe(markdown.markdown(value))
