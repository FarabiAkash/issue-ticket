from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        user_model = get_user_model()
        candidates = list(user_model.objects.filter(username=username))
        if not candidates:
            candidates = list(user_model.objects.filter(email__iexact=username))
        if not candidates:
            user_model().set_password(password)
            return None
        matched = [
            user
            for user in candidates
            if user.check_password(password) and self.user_can_authenticate(user)
        ]
        if len(matched) == 1:
            return matched[0]
        return None
