# Fair-Debate-Web

Fair-debate-Web is an experimental web application to facilitate controversial text-based debates.

### Manual Testing

- `python manage.py runserver`

### Unittests

`pytest` (requires splinter installed and configured)

### Feedback

Contact the maintainer <https://cknoll.github.io/pages/impressum.html>


## Development notes


- py3 manage.py createsuperuser
- py3 manage.py migrate --run-syncdb
- py3 manage.py dumpdata auth.user base | jsonlint -f > fixtures.json
