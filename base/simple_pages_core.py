"""
See `simple_page_interface.py` for a description of the simple_page-system.
"""


class SimplePage(object):
    def __init__(self, type, title, content, utc_comment="", lang=None):

        self.type = type
        self.title = title
        self.content = content
        self.utc_comment = utc_comment
        self.lang = lang

        # this will be set later by `get_sp`
        self.language_list = []
