import pytz

from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = None
        if request.user.is_authenticated:
            tzname = request.user.profile.timezone
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
