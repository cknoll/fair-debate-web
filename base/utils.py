from django.core.exceptions import ObjectDoesNotExist

from ipydex import IPS


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


def get_contribution_numbers():
    """
    Helper function to manually update the fixtures
    """

    from . import models
    import fair_debate_md as fdmd
    from django.conf import settings

    res = []
    for debate_obj in models.Debate.objects.all():

        ctb_list = []
        for ctb_obj in debate_obj.contribution_set.all():
            ctb_list.append(fdmd.DBContribution(ctb_key=ctb_obj.contribution_key, body=ctb_obj.body))
        ddl = fdmd.load_repo(
            settings.REPO_HOST_DIR, debate_obj.debate_key, ctb_list=ctb_list, new_debate=False
        )
        n = [v.db_ctb for v in ddl.tree.values()].count(False)
        res.append((debate_obj.debate_key, n))
    return res
