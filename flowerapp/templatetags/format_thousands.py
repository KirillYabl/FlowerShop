from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def format_thousands(value: str) -> str:
    """Format number by separate thousands: 3600 -> 3 600.

    If number not int it will be int.
    If value not number it will be returned without change.
    """
    try:
        value = int(value)
        return f'{value:,}'.replace(',', ' ')
    except ValueError:
        pass
    return value
