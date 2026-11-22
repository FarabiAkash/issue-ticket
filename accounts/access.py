from .models import User


def visible_users(user):
    if user.role == User.Role.SUPER_ADMIN:
        return User.objects.all()
    if user.role == User.Role.COMPANY_ADMIN and user.company_id:
        return User.objects.filter(company_id=user.company_id)
    return User.objects.none()


def manageable_users(user):
    if user.role == User.Role.SUPER_ADMIN:
        return User.objects.all()
    if user.role == User.Role.COMPANY_ADMIN and user.company_id:
        return User.objects.filter(
            company_id=user.company_id,
            role=User.Role.COMPANY_USER,
        )
    return User.objects.none()
