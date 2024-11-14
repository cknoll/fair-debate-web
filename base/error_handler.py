from django.http import HttpResponse
from django.conf import settings
import traceback
import ipydex

from .views import error_page


class ErrorHandlerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code==404 and settings.CATCH_EXCEPTIONS:
            msg = f"Page <tt>{request.get_full_path()}</tt> could not be found. <!-- utc_404_error -->"
            err_page = error_page(request, title="404 not found", msg=msg, status=404)
            return err_page

        return response

    def process_exception(self, request, exception):
        if settings.CATCH_EXCEPTIONS:

            if exception:
                err_page = error_page(request, title="general exception", msg=repr(exception), status=500)
                return err_page
