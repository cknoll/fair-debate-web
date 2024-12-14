from django.core.exceptions import ObjectDoesNotExist


def get_or_none(manager_obj, **kwargs):
    try:
        return manager_obj.get(**kwargs)
    except ObjectDoesNotExist:
        return None


class UsageError(ValueError):
    """
    This error class means, that the error was caused by bad app usage, which is to distinguish from
    some internal process error.
    """

    # The exception class is handled differently in `error_handler.py`
    pass


# we define this literal here to prevent circular imports
ABOUT_PATH = "about/"
