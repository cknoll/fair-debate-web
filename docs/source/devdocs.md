# Development Documentation

## Use Cases

This part of the documentation is targeted towards the development team. It documents the details of the usage mechanics.



### Basic Use Case (with multiple users)


:::{attention}
This section is yet only a placeholder.
:::

```{uml}

left to right direction
skinparam packageStyle rectangle

actor "User A" as UserA
actor "User B" as UserB
actor "User C" as UserC
actor "User D" as UserD

rectangle "Message Interaction System" {
  (Publish Message) as Publish
  (Answer Message) as Answer
  (Approve Third Party Answers) as Approve
}

UserA --> Publish: "Publishes message M1"
UserB --> Answer: "Can answer M1\n(normal status)"
UserC --> Answer: "Can answer M1\n(inofficial third party answers)"
UserD --> Answer: "Can answer M1\n(inofficial third party answers)"
UserB --> Approve: "Can approve\nthird party answers"

```



## Fixture Preparation

To make the platform understandable we need some example content. This requires data in the db and in repos

### Repos

There are three data sources:

- "proto-repos", i.e. directories with plain md files (without keys) which can easily be updated.
  - located in `fair-debate-md/src/fair_debate_md/fixtures/repos-preparation/`
  - example:
    ```
    d00-explanatory-example-debate__plain
    ├── a
    │   ├── a14b12a.md
    │   └── a.md
    └── b
        ├── a14b.md
        └── a20b.md
    ```
- "repos represented as .patch-files"
  - located in `fair-debate-md/src/fair_debate_md/fixtures/repos/`
  - example:
    ```
    .
    └── patches_01
        ├── 0001-first-commit.patch
        ├── 0002-add-contribution-a-a.md.patch
        └── 0003-add-contribution-b-a14b.md.patch
    ```


## Deployment


### Backup Strategy


Note: This is work in progress, and thus not as professional as desired.

- manual commands on testing instance:
  - `source ~/fair_debate_web-venv/bin/activate`
  - `cd fair_debate_web-deployment/fair-debate`
  - `python3 manage.py dumpdata --indent 2 base > ../fair-debate_db-backup/2026-04-08_115201_manual.json`
  - alternatively: `python manage.py savefixtures --backup` -> `~/fair_debate_web-deployment/fair_debate_web_db_backups/2026-mm-dd__10-08-37_backup_all.json`

- repos are saved at `~/fair_debate_web-deployment/fair_debate_repo_backups`


- download backups for local comparison:


on a remote machine where I have ssh access there is the following directory structure:

`~/AAA/BBB/YYYY-MM-DD__hh-mm-ss` where `YYYY-MM-DD__hh-mm-ss` is a placeholder for multiple directories all named with a time-stamp in iso-like format. I want to download the latest of those directories with rsync (without explicitly specifying its name). How can I do this?


`rsync -av "kddk@host:$(ssh user@host 'cd ~/AAA/BBB && ls -1d 20* | sort | tail -n 1')"  ./local-destination/`