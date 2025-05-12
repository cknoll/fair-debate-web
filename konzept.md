# KDDK-Plattform: Faire Debatte


## Zusammenfassung

Es wird eine Plattform vorgestellt, auf der textbasierte kontroverse Diskussionen geführt werden können, und zwar so, dass mit wenig Aufwand auf die einzelnen konkreten Aussagen inhaltlich eingegangen werden kann. Durch die Verwendung von Versionskontrolle und öffentlich lesbare Git-Repos ist die Manipulationssicherheit und Neutralität der Plattform gegeben.


## Hintergrund – Problembeschreibung

### Problem 1: Struktureller Aufwand sich inhaltlich mit einzelnen Aussagen auseinanderzusetzen.

Bisher laufen Debatten typischerweise so ab, dass eine Seite einen Block an Aussagen veröffentlicht (Text, Audio, Video). Die andere Seite, die das kritisieren möchte, müsste dann mit Aufwand diesen Block untergliedern und inhaltlich auf die Teilaussagen eingehen. Dieser Aufwand wird oft nicht oder nicht ausreichend geleistet. Stattdessen wird oft der gesamte Block pauschal kritisiert oder in einem eigenen monolithischen Block eine Gegenposition veröffentlicht, welche sich aus strukturellen Gründen ebenfalls nur mit Aufwand inhaltlich adäquat kritisieren lässt. Dieser Debattenprozess setzt sich ggf. noch einige Runden fort, bis er meist irgendwann im Sande verläuft oder nach einer Eskalation abgebrochen wird. Eine objektiv gute Lösung des diskutierten Problems ist dann meist noch nicht gefunden.

### Problem 2: Zerstreuung der Debatte auf unterschiedliche Medien

Hinzu kommt, dass die Debatte meist sehr verstreut stattfindet: Partei A veröffentlicht Aussagen-Block 1 in Medium X, Partei B Antwortet darauf mit Aussagen-Block 2 in Medium Y. Das muss Partei A erstmal mitbekommen um darauf wiederum eingehen zu können. Und das Publikum von Aussagen-Block 1 müsste es auch mitbekommen, um diese Aussagen mit der geäußerten Kritik abzugleichen. Wenn die Debatte noch einige Runden weitergeht, kommen meist weitere Medien ins Spiel. Was es für die beteiligten und das Publikum schwer bis unmöglich macht, die Debatte gezielt zu verfolgen.


### Problem 3: Beeinflussung der Debatte durch Kontrolle über das Medium

Problem 2 kann vermieden werden, indem die Debatte auf einem Medium (z.B. Online-Forum, in einer Zeitschrift) stattfindet. Allerdings besteht dann die Gefahr, dass diejenigen, die das Medium kontrollieren (z.B. Administration des Forums) bezüglich des Debattenthemas parteiisch sind. Das kann dazu führen, dass bestimmte Argumente oder Akteure von der Debatte ausgeschlossen oder anderweitig behindert werden. Und es kann dazu führen, dass derartige Vorwürfe (z.B. als Ablenkungsmanöver) fälschlicherweise erhoben werden – weil es grundsätzlich möglich ist und sich das Gegenteil schwer beweisen lässt.

### Problem 4: Unklarheit über Akteure

Weiterhin ist es oft schwierig, den Überblick zu behalten, welche Akteure an der Debatte überhaupt teilnehmen und auf welcher Seite sie stehen. Z.B. kritisiert Partei C ebenfalls Aussagen-Block 1, aber mit anderen Argumenten als Partei B und Partei D kritisiert sowohl Aussagen-Block 1 als auch 2. Partei E wiederum gibt vor, für Partei A zu sprechen, allerdings ist unklar wie legitim dieser Anspruch ist.

## Lösungsvorschlag:


### Zu Problem 1:

Ein Text wird digital veröffentlicht. Jeder Satz und weitere relevante Elemente (Überschriften, Stichpunkte, Abbildungen) sind a) referenzierbare Objekte (wie z.B. die Buch-Kapitel-Vers-Gliederung der Bibel). Jedes referenzierbare Objekt ist über einen Klick kommentierbar. Jeder Kommentar besteht selbst wieder aus kommentierbaren Objekten. **Der Aufwand, sich auf die konkreten inhaltlich strittigen Aussagen zu beziehen, ist dadurch sehr gering**. Das gleiche gilt für die Antwort auf die Antwort etc.

### Zu Problem 2 und 3:

Es gibt *eine* Plattform, auf der die gesamte Debatte sichtbar ist. Um Problem 3 (Beeinflussung der Debatte durch Kontrolle über das Medium) zu vermeiden, bezieht die Plattform die angezeigten Debattenbeiträge aus unabhängigen und vertrauenswürdigen Quellen, z.B. öffentlichen git-Repositorien (z.B. bei github)). Jede an der Debatte beteiligte Partei hat selber die alleinige Kontrolle über den Schreibzugriff auf ihr Repo. Die Debattenplattform dient lediglich der übersichtlichen Anzeige der Debattenbeiträge und der technischen Unterstützung beim Aktualisieren des Repos.

Natürlich könnte die Plattform bei der Anzeige der Repo-Inhalte manipulieren. Allerdings hat die Plattform einen starken Anreiz, ihre Glaubwürdigkeit zu behalten und eine Manipulation der Anzeige wäre sehr einfach nachweisbar, da die manipulationssicheren Originalinhalte in den öffentlich lesbaren Repos einsehbar sind (nur eben nicht in einer auf Übersichtlichkeit optimierten Darstellung, sondern als normaler Text).

### Zu Problem 4:

Über die Repositorien, aus denen die Debatten-Beiträge bezogen werden, wird eine klare Identifikation der Akteure ermöglicht. Wenn sich ein Teil des Publikums nur für die Debatte zwischen den Parteien A und B interessiert, dann werden nur die sich aufeinander beziehenden Beiträge dieser Parteien (d.h. der zugehörigen Repositorien) angezeigt. Wenn Partei E beansprucht, für Partei A zu sprechen, muss sie innerhalb von Partei A Überzeugungsarbeit leisten, um die eigenen Beiträge innerhalb des Repos von Partei A veröffentlichen zu können. Technisch ist das mit Hilfe sog. Merge-Requests (auch Pull-Requests) sehr einfach möglich. Es eröffnet zudem die Chance für eine gruppeninterne Profilierung durch inhaltlich qualitative Beiträge.


---

## Multi-User-Problem

Dass nur zwei Akteure diskutieren, ist unrealistisch. Z.B. könnte das Tool ja eine kontroverse Debatte auf einer Mailingliste ersetzen, aber dort diskutieren typischerweise 2 bis 20 Leute, ggf. sogar mehr.

Grundsätzlich geht das mit den verfügbaren Keys: A Schreibt Block, B und C antworten, A antwortet auf B und C, C antwortet auf B usw.


Gefahren:
- mehr irrelevante und redundante Beiträge
- allgemeine Unübersichtlichkeit: Gute Argumente werden durch benachbarte Nebelkerzen-Beiträge verdeckt


Lösungsideen:
- Voting oder Nebelkerzen-Flagging durch User. → Einladung an Mehrfach-Accounts etc.
- KI → teuer, nicht nachhaltig, nicht zuverlässig genug
- Manuelle Moderation (skaliert nicht)
- Trusted Flagger, reduzierte Sichtbarkeit, Reputationsmanagement

---

## Technische Umsetzung

Die prototypische technische Umsetzung ist fortgeschritten aber noch nicht abgeschlossen. Die folgenden Notizen dienen dem Autor bei der Feinplanung (sind aber z.T. überholt).

---



## Grundsätzlicher Ablauf:

- an einer Debatte nehmen zwei Seiten ("Parteien") teil. Wie diese Parteien sich intern organisieren, z.B. welche natürlichen Personen Schreibrechte haben, können sie selber entscheiden.
- Partei A eröffnet die Debatte mit einem schriftlichen Beitrag.
- Partei B hat die Gelegenheit, auf der gleichen Plattform mit der gleichen Sichtbarkeit zu antworten
- Die einzelnen Beiträge sollen bestimmte Qualitätsstandards erfüllen:
    - Sachlicher Ton, keine Beleidigungen etc.
    - Aussagen, bei denen kein Konsens angenommen werden kann, sind zu belegen
    - Beiträge müssen sinnvoll in referenzierbare Aussagen gegliedert sein.
    - Aussagen müssen zueinander in Beziehung gesetzt werden.
- Die Debatte (in einem Argumentationsstrang) ist dann beendet, wenn 7 Tage keine Reaktion erfolgte. Reaktion kann auch sein: wir brauchen x Tage mehr Zeit.
- Ziel der Debatte ist es, dass sich Dritte (z.B. Journalisten, interessiertes Publikum) ein möglichst klares Bild über die Positionen und Argumente der beteiligten Parteien machen können.


## Technische Umsetzung:

### Frontend (Lesen)

- Frontend zeigt zunächst Text von Partei A an.
- Grenzen zwischen einzelnen referenzierbaren Aussagen sind klar erkennbar
- Durch Symbole wird deutlich, ob und in welchem Umfang auf diese "Elementaraussagen" reagiert wurde
- oben Meta-Infos (aufklappbar): wer ist Partei A und B (repo-Links), wann jeweils letzter Beitrag

### Frontend (Initialen Beitrag Schreiben)

- Einloggen als Partei A
    - Schreibt einen MD-Beitrag in ein textarea
    - Klick auf Preview-Phase1
    - Automatische Aufteilung in Segmente durch Einfügen von Keys
    -

### Frontend (Antwort Schreiben)
- Einloggen als Partei B
- Aussage anwählen
- Antwort verfassen
- Vorschau bestätigen
- Pullrequest wird vom Backend erzeugt (ggf. branch auswählen).
- Pullrequest (auf github etc.) manuell mergen


### Frontend (Antwort Schreiben Versuch 2)
- Einloggen als Partei B (sicherstellen, dass B nur von einem Gerät aus eingeloggt sein kann)
- Aussage anwählen
    -> Formular erscheint an passender stelle (per js eingefügt)
- Antwort schreiben -> wird in Datenbank gespeichert
- Vorschau wird (als "normale" Antwort aber mit anderem Hintergrund und mit edit-Button) angezeigt,
- Weitere Aussage anwählen, weitere Antwort schreiben, editieren etc. alles noch in db gespeichert.
- grüner Button "Repo exportieren" inklusive Erklärungs-(i) erscheint oben, sobald eine unexportierte Antwort in der Datenbank liegt.
    - Button bewirkt, dass Antworten als Datei ins Debatten-Verzeichnis geschrieben werden. Neuer Kommit wird erstellt.
    - PR-erzeugung etc. kommt später


## Abgrenzung Datenbank vs. Dateisystem

### Datenbank:

- User
- Jede Debatte als Objekt
- Repo (als Objekt)
- Zusammenhang zwischen User und Repo:
    - User kann beim Anmelden eine repo-url angeben
    - ggf. später noch weitere Hinzufügen, ändern, etc. aktuell aktives repo auswählen
    - Jeder user hat zu jeder Zeit genau ein aktives Repo

### Dateisystem:

- Verzeichnis für jede Debatte.
- Verzeichnis ist ein repo mit zwei remotes:
    - official_a
    - official_b
- Beide remotes müssen konsistenten main-branch haben, d.h. Repo X darf nur um "fast-forward-merge" von repo Y abweichen
- Prozedur:
    - Nutzer meldet sich an.
    - Erzeugt einen neuen Beitrag (a/a.md). Um ihn zur Diskussion zu stellen muss folgendes passieren:
        - Plattform erzeugt ein Repo (z.B. auf github) mit
            - generischer README und Link https://faire-debatte.de/d/d1-lorem_ipsum + Link zur Doku
            - Verzeichnisstruktur
        - Plattform kommittiert a/a.md (2. Kommit)
        - Plattform fordert user auf, das Repo zu forken
        - User a forkt es und teilt repo-url der Plattform mit (damit bestätigt er die Authentizität des Inhalts von a.md)
        - Plattform veröffentlicht Beitrag
    - Anderer Nutzer möchte auf Beitrag eingehen und meldet sich dazu an. Er erstellt Antworten auf einzelne Aussagen (in der Datenbank)
    - Um diese Antworten zu publizieren muss folgendes passieren:
        - Plattform erzeugt im Repo einen Kommit als user b
        - Plattform fordert user b auf, das repo zu forken
        - User b forkt es und teilt Plattform die URL mit. (damit bestätigt er die Authentizität des Inhalts von b/a\d+b.md)
        - Plattform macht Antworten von b öffentlich sichtbar


- Kritik: Prozedur ist für den Anfang zu umständlich. Versuch einer Vereinfachung:

- Prozedur:
    - Nutzer meldet sich an.
    - Erzeugt einen neuen Beitrag (a/a.md). Um ihn zur Diskussion zu stellen muss folgendes passieren:
    - Plattform erzeugt ein Repo (z.B. auf github) mit
            - generischer README und Link https://faire-debatte.de/d/d1-lorem_ipsum + Link zur Doku
            - Verzeichnisstruktur
        - Plattform kommittiert a/a.md (2. Kommit)
        - Plattform gibt user die Möglichkeit, das Repo zu forken und die eigene URL zu hinterlegen.
            - **Einfacher Weg:** User klickt auf OK dann ist das Plattform-kontrollierte-repo maßgeblich
            - Sicherer Weg: User a forkt es und teilt repo-url der Plattform mit (damit bestätigt er die Authentizität des Inhalts von a.md)
        - Plattform veröffentlicht Beitrag
    - Anderer Nutzer möchte auf Beitrag eingehen und meldet sich dazu an. Er erstellt Antworten auf einzelne Aussagen (in der Datenbank)
    - Um diese Antworten zu publizieren muss folgendes passieren:
        - Plattform erzeugt im Repo einen Kommit als user b
        - Plattform ermöglicht User b das repo zu forken
            - **Einfacher Weg: User klickt auf OK** dann ist das Plattform-kontrollierte-repo maßgeblich
            - sicherer Weg: User b forkt es und teilt Plattform die URL mit. (damit bestätigt er die Authentizität des Inhalts von b/a\d+b.md)
        - Plattform macht Antworten von b öffentlich sichtbar

1. Implementierungsstufe:

Repo nur lokal im Arbeitsverzeichnis


---

Test-Konzept:

Üblich:
- Testdaten liegen in fixture-Dateien
- für jeden Test wird eine leere Datenbank erzeugt und spezifische fixtures werden geladen

Problem:
- repo-basiertes Vorgehen nutzt Datenbank + Dateisystem
- → ich muss mich um das Herstellen eines definierten Zustandes selber kümmern
- setUp, tearDown

---

Können mehrere Repos auf einen Ausgangspost reagieren? -> sollte grundsätzlich möglich sein. allerdings sollte das Ziel der Plattform Qualität vor Quantität sein.
d.h. Kritiker sollten sich zusammenschließen und gemeinsam an einer möglichst guten Kritik arbeiten, statt an mehreren mittelmäßigen oder schlechten.

Wenn das nicht geht, ist es das sinnvollste, eine eigene Debatte (mit dem selben a.md-Beitrag) aufzumachen, die "in geeigneter Weise" auf die Ausgangsdebatte verweist.

Es sollte aber immer klar sein, das das nicht die offizielle Debatte ist und a-Autor "nicht verpflichtet" ist (entsprechend der Wettbewerbsregeln) auf die Kritik einzugehen.


Herausforderung: wie kann ich ein repo (inklusive jedem einzelnen Kommit für jeden Branch in einer Sammlung von patch-Dateien darstellen?) -> gelöst



repo erzeugen:

```
git init
git add a/a.md
git commit --author="user_a <user_a@example.org>" -m "my contribution"
git add b/a2b.md b/a4b.md b/a6b.md b/a7b.md
git commit --author="user_b <user_b@example.org>" -m "my contribution"
git add a/a2b1a.md
git commit --author="user_a <user_a@example.org>" -m "my contribution"
git add b/a2b1a3b.md
git commit --author="user_b <user_b@example.org>" -m "my contribution"
```

patches erzeugen:

```
git format-patch --root -o patches
```

patches anwenden:
```
git init
git am patches/*patch
```

Wo soll der git-bezogene code leben?
-> eher im package als im web-repo




## Repräsentation von Aussagen im Repo

- Grundsätzlich: DebateMD = Markdown + Zusatzsyntax
- User müssen selber MD Quelltext erstellen (ggf. mit GUI Unterstützung)
- Zusatzsyntax wird vom Frontend erzeugt.
- Jede Aussage bekommt für die Referenzierbarkeit einen Key.
- Konsistenz wird automatisiert geprüft.
- Top-Level Aussagen haben Keys wie: `a1`, `a2`, `a3`.
- Antworten bekommen Keys wie `a3b1`, `a3b2`, `a3b23a12b4`
- Ein Key ist solange aktiv bis der nächste key kommt.
- Syntax um andere Statements zu referenzieren: (:a3b1:)
- Jede Partei hat ihr eigenes Verzeichnis (`a/` und `b/`) und darf auch nur Dateien in diesem Verzeichnis anlegen/ändern.
- Level-0-Aussagen (DebateMD Quelltext) kommen in Datei: `a/a.md`
- Level-1-Antworten kommen in Dateien: `b/a3b.md`, `b/a4b.md` usw.
- Level-2-Antworten kommen in Dateien: `a/a3b2a.md` usw.
- Eine im main-Branch des jeweiligen Repos veröffentlichte Datei, darf unmittelbar von der anderen Seite beantwortet werden.



### Offene Fragen/Probleme, die erstmal ignoriert werden:

- Was passiert, wenn sich Aussagen ändern, auf die sich andere schon bezogen haben? → erstmal nicht zulassen
- Kann eine Partei auf eigene Aussagen Antworten? → erstmal nicht zugelassen
