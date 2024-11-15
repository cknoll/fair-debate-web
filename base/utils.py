
from django.core.exceptions import ObjectDoesNotExist

def get_or_none(manager_obj, **kwargs):
    try:
        return manager_obj.get(**kwargs)
    except ObjectDoesNotExist:
        return None
