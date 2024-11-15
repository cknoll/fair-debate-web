
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Fair-Debate-Web

Fair-debate-Web is an experimental web application to facilitate controversial text-based debates.

## Development

`pip install -r requirements.txt`

### Manual Testing

- `fdmd unpack-repos ./content_repos`
- `python manage.py runserver`

### Unittests

`pytest` (requires splinter installed and configured)

## Feedback

Contact the maintainer <https://cknoll.github.io/pages/impressum.html>

## Coding style

We use `black -l 120 ./` to ensure coding style consistency.



## Development notes


helpful commands:

- fdmd unpack-repos ./content_repos
- py3 manage.py shell
- py3 manage.py createsuperuser
- mv db.sqlite3 db.sqlite3_old
- py3 manage.py migrate --run-syncdb
- py3 manage.py dumpdata auth.user base | jsonlint -f > fixtures.json
- py3 manage.py dumpdata base | jsonlint -f > fixtures.json
- py3 manage.py loaddata tests/testdata/users.json
- py3 manage.py loaddata tests/testdata/fixtures01.json


helpful urls:

localhost:8000/new
localhost:8000/new/test
localhost:8000/show/test
localhost:8000/d/d1-lorem_ipsum
