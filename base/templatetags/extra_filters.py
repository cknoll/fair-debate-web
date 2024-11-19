from django import template
from django.conf import settings
import markdown

register = template.Library()


@register.filter
def render_markdown(txt):

    if txt is None:
        txt = ""
    return markdown.markdown(txt)


# this filter takes two arguments. used like: {% if request.user|can_edit:entry %}
@register.filter
def can_edit(user, item):
    if user.is_staff:
        return True
    if user == item.user:
        return True
    return False


@register.filter
def settings_value(name):
    """
    This filter serves to access the some values from settings.py inside the templates
    without passing them through the view.

    For security we only allow such values which are explicitly mentioned here.
    (to e.g. prevent an adversary template author to access settings.DATABASES etc.)

    :param name:    name of the requested setting
    :return:
    """

    allowed_settings = ["DEBUG", "VERSION", "DEPLOYMENT_DATE"]

    if name not in allowed_settings:
        msg = "using settings.{} is not explicitly allowed".format(name)
        raise ValueError(msg)

    return getattr(settings, name, None)


@register.filter
def debug(arg):
    from ipydex import IPS
    IPS()