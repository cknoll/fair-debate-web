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


- download backups for local comparison: `python deployment/deploy.py -u -be` (see code before running)


---

- create fixture-ready pw-hash: `python -c "import django; from django.conf import settings; settings.configure(); from django.contrib.auth.hashers import make_password; print(make_password(input('new password:')))"`

---



### Local Deployment on Development Machine


```bash

# recommendation: make a fresh checkout of the repo
# copy (or create) valid config.toml

pip install -r requirements.txt
rm -f db.sqlite3
python manage.py migrate --run-syncdb
python manage.py loaddata tests/testdata/fixtures01.json
fdmd unpack-repos ./content_repos
rm -rf ./content_repos/d00-explanatory-example-debate
fdmd process-content-dir __FIXTURES_RP__/d00-explanatory-example-debate__plain ./content_repos/d00-explanatory-example-debate


python manage.py runserver
```