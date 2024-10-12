from django import template
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
