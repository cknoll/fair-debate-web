# Background: Identified Problems and Suggested Solutions

## Basic Assumptions

The following assumptions are foundational to this project:

- Constructive discussions about controversial topics are essential for a functional democracy.
- Given suitable circumstances humans are able to conduct constructive discussions even on controversial topics.
- Currently (as of 2025) most controversial online discussions are conducted in a nonconstructive way, and most often do not yield insights due to convincing arguments but instead frustration due to escalation and the lack of clarity.
- Technical properties of the respective platform can influence an online discussion for bad or for good.


## Identified Problems

### Problem 1: Structural Effort to Deal with the Content of Individual Statements.

Up to now, debates have typically taken place in such a way that one side publishes a block of
statements (text, audio, video). The other side, which would like to criticize this, would then have
to make an effort to subdivide this block and address the content of the sub-statements, e.g. by citing.
This effort is often not made or not made sufficiently. Instead, the entire block is often criticized
broadly and unspecifically or a counter-position is published in a separate monolithic block,
to which the same problem applies: A suitable reaction would require addressing specific statements,
which, however, would require effort of citing or other types of referencing. This debate process may
continue for a few more rounds until it usually fizzles out at some point or is broken off
after an escalation. An objectively good solution to the problem under discussion has
then usually not yet been found. Often, the specific original problem has even been slipped out of the focus
of the discussion.

Of course, in many cases citing or referencing of specific statements does happen.
However, in general it happens too rarely and if often also in misleading way e. g.
by presenting quotes out of context or change the wording.

### Problem 2: Scattering of Debate-Contributions Across Different Media

In addition, a public debate is usually very scattered: Party A publishes statement block 1 in medium X
(e.g. a "Strategy Paper" addressing a certain topic), party B responds with valid criticism as
statement block 2 in medium Y (e.g. a guest article in a newspaper). Party A must first be aware
of this in order to be able to respond. And the audience of statement block 1
must also be aware of this in order to compare these statements with the criticism expressed.
If the debate continues for more rounds, other media usually come into play.
This makes it difficult or even impossible for the participants and the audience
to follow the debate in a targeted manner.


### Problem 3: Influencing the Debate by Controlling the Medium

Problem 2 can be avoided by holding the debate on one medium (e.g. online forum, in a magazine).
However, there is then a risk that those who control the medium (e.g. the administration of the forum)
are biased with regard to the topic of the debate. This can lead to certain arguments or actors being
excluded from the debate or otherwise obstructed. And it can lead to such accusations being falsely made
(e.g. as a diversionary tactic) - because it is fundamentally possible and difficult to prove otherwise.

### Problem 4: Lack of Clarity About Actors

Furthermore, it is often difficult to keep track of which actors are participating in the debate and which
side they are on. For example, party C also criticizes statement block 1, but with different arguments than
party B and party D criticizes both statement block 1 and 2. Party E, on the other hand, claims to speak for
party A, but uses bad arguments and it is unclear how legitimate this claim is.


### Summary:

There are certain *structural* problems which significantly complicate, retard or even prevent a factual
and solution-orientend debate on controversial topics.

## Proposed Solutions by *Fair-Debate*:

The approach of *Fair-Debate* is to provide a platform for factual and solution-orientend debates
which solves or avoids above problems by technical means.

### For Problem 1 (Citing too Rarely and Often Badly)

A text is published digitally. Each sentence and other relevant elements
(headings, key points, illustrations) are a) referenceable objects (such as the book-chapter-verse
structure of the Bible). Each referenceable object can be commented on with a click.
Each comment itself consists of comment-able objects. **The effort required to refer to the specific
content of disputed statements is therefore very low**. The same applies to the reply to the reply etc.

### Addressing Problems 2 (Scattering of Debate-Contributions) and 3 (Abuse of Control over the Medium)

There is *one* platform on which the entire debate is visible. In order to avoid problem 3
(influencing the debate by controlling the medium), the platform obtains the displayed debate contributions
from independent and trustworthy sources, e.g. public git repositories (e.g. at github).
Each party involved in the debate has sole control over write access to its repo. The debate platform only
serves to *nicely display* the debate contributions and to simplify the authoring process.
It has no control over the actual content.

Of course, the platform could in theory manipulate the displayed version of the repo content.
However, such manipulation would be very easy to detect and prove beyond doubt, because the tamper-proof
original content of each contribution can be accessed and viewed in the publicly readable git repos.
The role of the software is just to collect the contributions from the respective repos and to provide
a suitable user interface.


### Addressing Problem 4

The repositories from which the debate contributions are obtained enable clear identification of the actors.
If part of the audience is only interested in the debate between parties A and B,
then only the related contributions of these parties (i.e. the associated repositories) are displayed.
If party E claims to speak for party A, it has to do persuasive work within party A in order to be able
to publish its own contributions within party A's repo. Technically, this is very easy to realize by means of
merge requests (also known as pull requests). It also opens up the opportunity for individuals to demonstrate
their expertise and communications skills by submitting qualitative contributions.

### Summary

*Fair-Debate* solves or avoids the four identified problems and thus can provide a platform for factual and
solution-orientend debates on controversial topics.
The main challenge is to convince people that the initial extra effort (familiarize with a new platform and
new discussion concept) is worth it. This requires open-minded people with dedication to convince
with good arguments are not afraid of reasonable counterarguments.
