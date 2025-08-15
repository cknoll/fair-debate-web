"""
See `simple_page_interface.py` for a description of the simple_page-system.
"""

import collections
from django.utils.translation import gettext as _
from collections import defaultdict
from django.conf import settings

from .simple_pages_core import SimplePage
from . import utils


def reverse(*args, **kwargs):
    # this import is placed here to prevent circular imports
    from django.urls import reverse as orig_reverse

    return orig_reverse(*args, **kwargs)


dupurls = {
    "contact-page": "/contact",
    "about_page": utils.ABOUT_PATH,
}
duplicated_urls = defaultdict(lambda: "__invalid_url__", dupurls)


sp_unknown = SimplePage(
    type="unknown", title="unknown", content="This page is unknown. Please go back to `home`."
)

splist = [sp_unknown]


# Defining this function here in the content file results in some code-duplication but is the easiest approach.
def new_sp(**kwargs):
    sp = SimplePage(**kwargs)
    splist.append(sp)
    return sp


# ----------------------------------------------------------------------------

new_sp(type="settings", title="Settings", content="In the future you can configure some settings here.")


# ----------------------------------------------------------------------------

new_sp(
    type="user_profile",
    title="User Profile",
    content="""
# User Profile

In the future you can edit your user profile here.
""",
)


# ----------------------------------------------------------------------------

new_sp(
    type="imprint",
    title="Legal Notice",
    utc_comment="utc_imprint_en",
    content="""
## Legal Notice


This website is maintained by Carsten Knoll.
This website contains external links.
We can not assume any liability for the content of such external websites because they are not under our control.
This website contains content which was created and/or edited by users which are unknown to the maintainer.
We strive for compliance with all applicable laws and try to remove unlawful or otherwise inappropriate content.
However we can not guarantee the immediate removal.
Should there be any problem with the operation or the content of this website, please contact the maintainer.
<br><br>
Contact information: \n\n
- [http://cknoll.github.io/pages/impressum.html](http://cknoll.github.io/pages/impressum.html)
- [https://codeberg.org/kddk/fair-debate-web](https://codeberg.org/kddk/fair-debate-web)
""",
)


new_sp(
    type="imprint",
    lang="de",
    title="Impressum",
    utc_comment="utc_imprint_de",
    content="""
## Impressum

Diese Seite wird betrieben von Carsten Knoll.
Haftung für Links auf externe Seiten wird explizit nicht übernommen.
Diese Seite enthält Inhalte die von dem Betreiber unbekannten Benutzern eingestellt werden.
Der Betreiber bemüht sich, eventuelle Ordnungs- oder Gesetzeswidrigkeiten schnellstmöglich zu entfernen,
kann aber nicht dafür garantieren.
Sollte es ein Problem mit dem Betrieb oder den Inhalten der Seite geben, kontaktieren Sie bitte den Betreiber.
<br><br>
Kontaktinformationen: \n\n
- [https://cknoll.github.io/pages/impressum.html](http://cknoll.github.io/pages/impressum.html)
- [https://codeberg.org/kddk/fair-debate-web](https://codeberg.org/kddk/fair-debate-web)
""",
)


# ----------------------------------------------------------------------------
contact = True

new_sp(
    type="contact",
    title="Contact",
    utc_comment="utc_contact_en",
    content="""
This site is maintained by Carsten Knoll. For contact information see: \n\n

- [http://cknoll.github.io/pages/impressum.html](http://cknoll.github.io/pages/impressum.html)
- [https://codeberg.org/kddk/fair-debate-web](https://codeberg.org/kddk/fair-debate-web)
""",
)

new_sp(
    type="contact",
    lang="de",
    title="Kontakt",
    utc_comment="utc_contact_de",
    content="""
Diese Seite wird betrieben von Carsten Knoll.
Weitere Kontaktinformationen: \n\n

- [http://cknoll.github.io/pages/impressum.html](http://cknoll.github.io/pages/impressum.html)
- [https://codeberg.org/kddk/fair-debate-web](https://codeberg.org/kddk/fair-debate-web)
""",
)


# ----------------------------------------------------------------------------
privacy = True

new_sp(
    type="privacy",
    title=_("Privacy rules"),
    utc_comment="utc_privacy_en",
    content="""
## Privacy rules

This website aims for data **frugality**.
We only collect data which is necessary to operate this website or which is explicitly
submitted voluntarily by the user.
We use **cookies** to enable an internal area which serves to store settings and manage
access-rights for content.

In particular we collect and process the following data:

 - Content (if voluntarily submitted)
 - Webserver logs (contains ip-addresses, browser version and url of origin("referrer");
 Duration of storage of this data: 14 day; This data is collected to prevent abuse and facilitate secure operation
 of this website; See also  [Reason 49](https://dsgvo-gesetz.de/erwaegungsgruende/nr-49/))

If you have questions or requests (e.g. Correction or Deletion of data) please contact the maintainer of this website,
see [contact]({}).
""".format(
        dupurls["contact-page"]
    ),
)


new_sp(
    type="privacy",
    lang="de",
    title=_("Datenschutzrichtlinie"),
    utc_comment="utc_privacy_de",
    content="""
## Datenschutzrichtlinie

Diese Seite orientiert sich am Prinzip der **Datensparsamkeit**
und erhebt nur Daten, die für den Betrieb des Dienstes notwendig sind und
im Wesentlichen freiwillig übermittelt werden.
Die Seite setzt **Cookies** ein, um einen internen
Bereich zu ermöglichen, der zur Speicherung von Einstellungen und
dem Management von Zugriffsberechtigungen auf Inhalte dient.

Im Einzelnen werden folgende Daten erfasst und verarbeitet.:

 - Inhalte (wenn freiwillig angegeben, offensichtlich notwendig für den Betrieb der Seite)
 - Webserver-Logs (beinhalten IP-Adressen, Browser-Version und Herkunftsseite ("Referrer");
 Speicherdauer 14 Tage; Notwendig zum Schutz gegen Missbrauch und zum sicheren Betrieb der Webseite;
 [Erwägungsgrund 49](https://dsgvo-gesetz.de/erwaegungsgruende/nr-49/))

Bei Fragen bzw. Anfragen (z.B. Richtigstellung und Löschung von Daten) wenden Sie sich bitte den Betreiber der Seite.
Siehe [Kontakt]({}).

""".format(
        dupurls["contact-page"]
    ),
)

# ----------------------------------------------------------------------------
backup = True

new_sp(type="backup", title="backup message", content=_("""Backup has been written to: {backup_path}"""))
# ----------------------------------------------------------------------------
backup_no_login = True

# this is for logged in users which are no superuser

new_sp(
    type="backup_no_login",
    title="backup message",
    content=_("""You need to be logged in as admin to create a backup."""),
)

# ----------------------------------------------------------------------------
general_error = True

# this is for logged in users which are no superuser

new_sp(type="general_error", title="general error page", content=_("""Some Error occurred. Sorry."""))

# ----------------------------------------------------------------------------


# welcome = True
# pattern for reusing text

# extra1 = "`moodpoll` is an app for easy and good decision making.\n\n"

# rdme1 = get_project_READMEmd("<!-- marker_1 -->", "<!-- marker_2 -->")
# rdme2 = get_project_READMEmd("<!-- marker_2 -->", "<!-- marker_3 -->")


# txt1 = "".join((extra1, rdme1, rdme2))


# TODO: add content
about_text_en = """
# About *Fair Debate*

*Fair Debate* is a platform on which text-based controversial discussions can be held in such a way
that the content of the individual concrete statements can be addressed with little effort.
The use of version control and publicly readable Git repos ensures that the platform is tamper-proof and
neutral.


## Background - Problem Description

### Problem 1: Structural effort to deal with the content of individual statements.

Up to now, debates have typically taken place in such a way that one side publishes a block of
statements (text, audio, video). The other side, which would like to criticize this, would then have
to make an effort to subdivide this block and address the content of the sub-statements.
This effort is often not made or not made sufficiently. Instead, the entire block is often criticized
across the board or a counter-position is published in a separate monolithic block, which for structural
reasons can also only be adequately criticized in terms of content with effort. This debate process may
continue for a few more rounds until it usually fizzles out at some point or is broken off
after an escalation. An objectively good solution to the problem under discussion has
then usually not yet been found.

### Problem 2: Dispersion of the debate across different media

In addition, the debate is usually very scattered: Party A publishes statement block 1 in medium X, party B
responds with statement block 2 in medium Y. Party A must first be aware of this in order to be able
to respond. And the audience of statement block 1 must also be aware of this in order to compare
these statements with the criticism expressed. If the debate continues for a few more rounds,
other media usually come into play. This makes it difficult or even impossible for the participants
and the audience to follow the debate in a targeted manner.


### Problem 3: Influencing the debate by controlling the medium

Problem 2 can be avoided by holding the debate on one medium (e.g. online forum, in a magazine).
However, there is then a risk that those who control the medium (e.g. the administration of the forum)
are biased with regard to the topic of the debate. This can lead to certain arguments or actors being
excluded from the debate or otherwise obstructed. And it can lead to such accusations being falsely made
(e.g. as a diversionary tactic) - because it is fundamentally possible and difficult to prove otherwise.

### Problem 4: Lack of clarity about actors

Furthermore, it is often difficult to keep track of which actors are participating in the debate and which
side they are on. For example, party C also criticizes statement block 1, but with different arguments than
party B and party D criticizes both statement block 1 and 2. Party E, on the other hand, claims to speak for
party A, but it is unclear how legitimate this claim is.

## Proposed Solution by *Fair-Debate*:


### For problem 1:

A text is published digitally. Each sentence and other relevant elements
(headings, key points, illustrations) are a) referenceable objects (such as the book-chapter-verse
structure of the Bible). Each referenceable object can be commented on with a click.
Each comment itself consists of comment-able objects. **The effort required to refer to the specific
content of disputed statements is therefore very low**. The same applies to the reply to the reply etc.

### Addressing Problems 2 and 3:

There is *one* platform on which the entire debate is visible. In order to avoid problem 3
(influencing the debate by controlling the medium), the platform obtains the displayed debate contributions
from independent and trustworthy sources, e.g. public git repositories (e.g. at github).
Each party involved in the debate has sole control over write access to its repo. The debate platform only
serves to clearly display the debate contributions and to provide technical support when updating the repo.

Of course, the platform could manipulate the display of repo content. However, the platform has a
strong incentive to maintain its credibility and manipulation of the display would be very easy to prove,
as the tamper-proof original content can be viewed in the publicly readable repos (just not in a display
optimized for clarity, but as normal text).


### Addressing Problem 4:

The repositories from which the debate contributions are obtained enable clear identification of the actors.
If part of the audience is only interested in the debate between parties A and B,
then only the related contributions of these parties (i.e. the associated repositories) are displayed.
If party E claims to speak for party A, it has to do persuasive work within party A in order to be able
to publish its own contributions within party A's repo. Technically, this is very easy to do with the help
of merge requests (also known as pull requests). It also opens up the opportunity for group-internal
profiling through qualitative contributions.
"""

new_sp(type="about", title="About the app", content=_(about_text_en))

# extra2 = "You can [try it out now]({}) or [read more]({}).".format(dupurls["new_poll"], dupurls["about-page"])

# txt_landing = "".join((extra1, rdme1, extra2))
# new_sp(type="landing",
#        title="moodpoll - easy and good decision making",
#        content=_(txt_landing))

new_sp(
    type="landing",
    title="landing page",
    content=_(
        f"""
# Fair-Debate-Web

Fair-Debate-Web is an experimental web application to facilitate text-based debates on controversial topics.

[Learn more ...]({dupurls["about_page"]})

"""
    ),
)
# Try it out: [{settings.BASE_URL.rstrip("/")}/new]({settings.BASE_URL.rstrip("/")}/new)

# --


# TODO: ins englische übernehmen: neutrale Stimmen werden nicht mehr separat angezeigt
# Dienstag hat nur eine positive Stimme

# ----------------------------------------------------------------------------


# create a defaultdict of all simple pages with sp.type as key
items = []
for sp in splist:

    if sp.lang:
        key = f"{sp.type}__{sp.lang}"
    else:
        key = sp.type
    items.append((key, sp))

# noinspection PyArgumentList
sp_defdict = collections.defaultdict(lambda: sp_unknown, items)
