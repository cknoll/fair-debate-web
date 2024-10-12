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
        return response

    def process_exception(self, request, exception):
        if settings.CATCH_EXCEPTIONS:

            if exception:
                err_page = error_page(request, title="general exception", msg=repr(exception), status=500)
                return err_page
