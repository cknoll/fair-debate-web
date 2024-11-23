import logging

from django.http import HttpResponse
from django.conf import settings

import ipydex

from .views import error_page
from .utils import UsageError

logger = logging.getLogger("fair-debate")


class ErrorHandlerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and settings.CATCH_EXCEPTIONS:
            msg = f"Page <tt>{request.get_full_path()}</tt> could not be found. <!-- utc_404_error -->"
            err_page = error_page(request, title="404 not found", msg=msg, status=404)
            return err_page

        return response

    def process_exception(self, request, exception):
        if settings.CATCH_EXCEPTIONS:

            if exception:
                msg = repr(exception)
                if not isinstance(exception, UsageError):
                    # we only write a logfile entry for serious problems
                    logger.warning(msg)
                title = type(exception).__name__
                err_page = error_page(request, title=title, msg=msg, status=500)
                return err_page
