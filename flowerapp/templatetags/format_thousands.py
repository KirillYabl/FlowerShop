from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def format_thousands(value: str) -> str:
    """Format number by separate thousands: 3600 -> 3 600.

    If value not number it will be returned without change.
    """
    try:
        int_value = int(value)
        float_value = float(value)
        if float_value == int_value:
            value = int_value
        else:
            value = float_value
        return f'{value:,}'.replace(',', ' ')
    except ValueError:
        pass
    return value
