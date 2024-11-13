# Fair-Debate-Web

Fair-debate-Web is an experimental web application to facilitate controversial text-based debates.

### Manual Testing

- `python manage.py runserver`

### Unittests

`pytest` (requires splinter installed and configured)

### Feedback

Contact the maintainer <https://cknoll.github.io/pages/impressum.html>


## Development notes


helpful commands:

- py3 manage.py shell
- py3 manage.py createsuperuser
- mv db.sqlite3 db.sqlite3_old
- py3 manage.py migrate --run-syncdb
- py3 manage.py dumpdata auth.user base | jsonlint -f > fixtures.json
- py3 manage.py dumpdata base | jsonlint -f > fixtures.json
- py3 manage.py loaddata tests/testdata/users.json
- py3 manage.py loaddata tests/testdata/*.json


helpful urls:

localhost:8000/new
localhost:8000/new/test
localhost:8000/show/test
