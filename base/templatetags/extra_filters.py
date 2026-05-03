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
def get_user_role(debate, user):
    return debate.get_user_role(user)


@register.filter
def debug(arg):
    from ipydex import IPS

    IPS()

@register.tag(name="trim_whitespace_after")
def trim_whitespace_after(parser, token):
    """
    This tag serves to trim newlines and spaces from rendered html – this simplifies the creation of
    readable templates (with out <!-- ... --> based hacks). Usage

    {% trim_new_lines_after "»" stop_at="«" %}
    (some text»
    {% if data.condition %}
        should be inserted»
    {% endif %}
    )
    {% end_trim_whitespace_after %}
    """
    bits = token.split_contents()
    if len(bits) not in (2, 3):
        msg = "trimnewlines tag requires one positional argument and accepts one "
        "optional argument (`stop_at`)."
        raise template.TemplateSyntaxError(msg)

    start_marker = bits[1].strip("'\"")
    try:
        stop_marker = bits[2].split('=', 1)[1].strip("'\"")
    except IndexError:
        stop_marker = "«"

    node_list = parser.parse(('end_trim_whitespace_after',))
    parser.delete_first_token()
    return TrimSpaceNode(node_list, start_marker, stop_marker)

class TrimSpaceNode(template.Node):
    def __init__(self, node_list, start_marker, stop_marker):
        self.node_list = node_list
        self.start_marker = start_marker
        self.stop_marker = stop_marker


    def render(self, context):
        output = self.node_list.render(context)
        parts = output.split(f"{self.start_marker}\n")
        # Keep the first part as is, lstrip() the rest
        result = parts[0] + "".join(p.lstrip() for p in parts[1:])
        results2 = result.replace(self.stop_marker, "")
        return results2
