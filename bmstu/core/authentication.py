from rest_framework.authentication import SessionAuthentication


class CookieSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return
