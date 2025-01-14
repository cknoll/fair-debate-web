
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Fair-Debate-Web

Fair-debate-Web is an experimental web application to facilitate controversial text-based debates.

## Development

`pip install -r requirements.txt`

### Manual Testing

#### Preparation

- `fdmd unpack-repos ./content_repos`
    - run this both in `<repo_root>` (workdir of development server) and `<repo_root>/tests/testdata` (for unittests)
- `python manage.py migrate --run-syncdb`
- `python manage.py loaddata tests/testdata/fixtures01.json`

#### Run automated unit tests

- `pytest` (requires splinter installed and configured)

#### Interactive Testing (using the development server)

- `python manage.py runserver`

## Feedback

Contact the maintainer <https://cknoll.github.io/pages/impressum.html>

## Coding style

We use `black -l 110 ./` to ensure coding style consistency. For commit messages we (now) try to follow the [conventional commits specification](https://www.conventionalcommits.org/en/).



## Development notes

### Terminology:

- "utc": unit test comment
- "utd": unit test data

### Local Testing

- Create test data:
- `fdmd unpack-repos ./content_repos`
    - this should be run in both in `<repo-root>` (for manual testing) and in `<repo-root/tests/testdata>` (for unittests)


### Helpful Commands:

- py3 manage.py shell
- py3 manage.py createsuperuser
- mv db.sqlite3 db.sqlite3_old
- py3 manage.py migrate --run-syncdb
- py3 manage.py dumpdata auth.user base | jsonlint -f > fixtures.json
- py3 manage.py dumpdata base | jsonlint -f > fixtures.json
- py3 manage.py loaddata tests/testdata/fixtures01.json


helpful urls:

localhost:8000/new
localhost:8000/new/test
localhost:8000/show/test
localhost:8000/d/d1-lorem_ipsum
