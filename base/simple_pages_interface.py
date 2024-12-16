"""
This module (copied from moodpoll) organizes the access to a special kind of content: "simple pages". They consist of markdown text
which is rendered.

While this type of content in principle could live in the database it is much easier to maintain in textfiles.
To support different parallel instances of this app which can have different contents of the simple pages we use the
following structure:

The path to the file `simple_pages_content_custom.py` is configured via the settings (currently not done)
If this whole file or a key is not present the content of `simple_pages_content_default.py` is used as fallback.

The logic for this lives in `simple_pages_interface.py`.
The functions and datatypes live in `simple_pages_core.py`

"""

from ipydex import IPS
from collections import defaultdict
from django.conf import settings
from .simple_pages_core import SimplePage

# import the simple_page_default_dict for the default content
from .simple_pages_content_default import sp_defdict as sp_defdict_orig, new_sp

# look if we have custom_content
try:
    SIMPLE_PAGE_CONTENT_CUSTOM_PATH = settings.SIMPLE_PAGE_CONTENT_CUSTOM_PATH
except AttributeError:
    SIMPLE_PAGE_CONTENT_CUSTOM_PATH = None


# currently not implemented, see moodpoll for implementation
simple_pages_content_custom = None

try:
    sp_defdict_custom = simple_pages_content_custom.sp_defdict
except AttributeError:
    # create empty defaultdict with the same default value as in sp_defdict, but no items
    sp_defdict_custom = defaultdict(sp_defdict_orig.default_factory, [])

# now update the default in two steps
# to prevent that keys from first dict are overwritten by the default_factory of 2nd
sp_defdict = defaultdict(sp_defdict_custom.default_factory, sp_defdict_orig.items())
sp_defdict.update(dict(sp_defdict_custom))


def create_language_dict():

    language_dict = defaultdict(list)
    for key in sp_defdict.keys():
        parts = key.split("__")
        if len(parts) == 1:
            pagetype = key
            lang = None
        elif len(parts) == 2:
            pagetype = parts[0]
            lang = parts[1]
        else:
            msg = "Invalid key {key} in sp_defdict"
            raise ValueError(msg)

        language_dict[pagetype].append(lang)

    return language_dict


language_dict = create_language_dict()


def get_sp(pagetype, lang=None) -> SimplePage:

    desired_key = "{}__{}".format(pagetype, lang)
    if desired_key in sp_defdict:
        # return the corrcect language version if possible
        res = sp_defdict[desired_key]
    else:
        # return the only available version
        res = sp_defdict[pagetype]

    res.language_list = language_dict[pagetype]

    return res
